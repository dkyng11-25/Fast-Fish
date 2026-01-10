"""Step 7: Missing Category/SPU Rule with Sell-Through Validation."""

import fireducks.pandas as pd
from typing import Optional
from datetime import datetime
from pathlib import Path

from src.core.step import Step
from src.core.context import StepContext
from src.core.logger import PipelineLogger
from src.core.exceptions import DataValidationError

from src.components.missing_category import (
    MissingCategoryConfig,
    DataLoader,
    ClusterAnalyzer,
    OpportunityIdentifier,
    SellThroughValidator,
    ROICalculator,
    ResultsAggregator,
    ReportGenerator
)


class MissingCategoryRuleStep(Step):
    """
    Step 7: Missing Category/SPU Rule with Sell-Through Validation.
    
    Identifies missing opportunities where stores are not selling
    well-selling features from their cluster, calculates recommended
    quantities, validates with Fast Fish sell-through predictions,
    and optionally calculates ROI metrics.
    
    4-Phase Pattern:
    1. SETUP: Load clustering, sales, quantity, and margin data
    2. APPLY: Identify opportunities, validate, calculate ROI, aggregate
    3. VALIDATE: Verify data quality and required columns
    4. PERSIST: Save results and generate reports
    """
    
    def __init__(
        self,
        cluster_repo,
        sales_repo,
        quantity_repo,
        margin_repo,
        output_repo,
        sellthrough_validator: Optional[SellThroughValidator],
        config: MissingCategoryConfig,
        logger: PipelineLogger,
        step_name: str = "Missing Category Rule",
        step_number: int = 7
    ):
        """
        Initialize Missing Category Rule step.
        
        Args:
            cluster_repo: Repository for clustering data
            sales_repo: Repository for sales data
            quantity_repo: Repository for quantity data
            margin_repo: Repository for margin data
            output_repo: Repository for output files
            sellthrough_validator: Fast Fish sell-through validator (optional)
            config: Configuration for the analysis
            logger: Pipeline logger instance
            step_name: Name of the step
            step_number: Step number in pipeline
        """
        super().__init__(logger, step_name, step_number)
        
        # Store repositories
        self.cluster_repo = cluster_repo
        self.sales_repo = sales_repo
        self.quantity_repo = quantity_repo
        self.margin_repo = margin_repo
        self.output_repo = output_repo
        
        # Store configuration
        self.config = config
        
        # Create components
        self.data_loader = DataLoader(
            cluster_repo=cluster_repo,
            sales_repo=sales_repo,
            quantity_repo=quantity_repo,
            margin_repo=margin_repo,
            config=config,
            logger=logger
        )
        
        self.cluster_analyzer = ClusterAnalyzer(config, logger)
        
        # Initialize sell-through validator first
        self.sellthrough_validator = SellThroughValidator(
            fastfish_validator=sellthrough_validator,
            config=config,
            logger=logger
        ) if sellthrough_validator else None
        
        # Debug: Log validator status
        if self.sellthrough_validator:
            has_ff = hasattr(self.sellthrough_validator, 'fastfish_validator')
            ff_value = getattr(self.sellthrough_validator, 'fastfish_validator', None) if has_ff else None
            logger.info(f"SellThroughValidator initialized: has_fastfish_validator={has_ff}, value={ff_value is not None}")
        else:
            logger.warning("No SellThroughValidator - Fast Fish validation will be skipped")
        
        # Pass validator to opportunity identifier for Fast Fish validation
        self.opportunity_identifier = OpportunityIdentifier(
            config, 
            logger,
            validator=self.sellthrough_validator
        )
        
        self.roi_calculator = ROICalculator(config, logger) if config.use_roi else None
        
        self.results_aggregator = ResultsAggregator(config, logger)
        
        self.report_generator = ReportGenerator(config, logger)
    
    def setup(self, context: StepContext) -> StepContext:
        """
        SETUP Phase: Load all required data.
        
        Loads:
        - Clustering assignments
        - Sales data (with optional seasonal blending)
        - Quantity data with prices
        - Margin rates (if ROI enabled)
        
        Args:
            context: Step context
            
        Returns:
            Context with loaded data
        """
        self.logger.info("SETUP: Loading data...")
        
        # Load all data using DataLoader
        data = self.data_loader.load_all_data()
        
        # Store in context
        context.data['cluster_df'] = data['cluster_df']
        context.data['sales_df'] = data['sales_df']
        context.data['quantity_df'] = data['quantity_df']
        context.data['margin_df'] = data['margin_df']
        
        self.logger.info(
            f"Data loaded: {len(data['cluster_df'])} stores, "
            f"{len(data['sales_df'])} sales records"
        )
        
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """
        APPLY Phase: Identify opportunities and calculate quantities.
        
        Process:
        1. Identify well-selling features per cluster
        2. Find missing opportunities (stores not selling well-selling features)
        3. Validate opportunities with sell-through predictions
        4. Calculate ROI metrics (if enabled)
        5. Aggregate to store level
        
        Args:
            context: Step context with loaded data
            
        Returns:
            Context with analysis results
        """
        self.logger.info("APPLY: Analyzing opportunities...")
        
        # Extract data from context
        cluster_df = context.data['cluster_df']
        sales_df = context.data['sales_df']
        quantity_df = context.data['quantity_df']
        margin_df = context.data['margin_df']
        
        # Step 1: Identify well-selling features per cluster
        self.logger.info("Step 1: Identifying well-selling features...")
        well_selling = self.cluster_analyzer.identify_well_selling_features(
            sales_df=sales_df,
            cluster_df=cluster_df
        )
        context.data['well_selling_features'] = well_selling
        
        if len(well_selling) == 0:
            self.logger.warning("No well-selling features found. No opportunities to identify.")
            context.data['opportunities'] = pd.DataFrame()
            context.data['results'] = pd.DataFrame()
            return context
        
        # Step 2: Identify missing opportunities
        self.logger.info("Step 2: Identifying missing opportunities...")
        opportunities = self.opportunity_identifier.identify_missing_opportunities(
            well_selling_df=well_selling,
            cluster_df=cluster_df,
            sales_df=sales_df,
            quantity_df=quantity_df
        )
        
        if len(opportunities) == 0:
            self.logger.warning("No opportunities identified.")
            context.data['opportunities'] = pd.DataFrame()
            # Create empty results for all stores (match legacy behavior)
            results = self.results_aggregator.create_empty_results(cluster_df=cluster_df)
            context.data['results'] = results
            return context
        
        # Step 3: Validate with sell-through
        if self.sellthrough_validator:
            self.logger.info("Step 3: Validating with sell-through predictions...")
            opportunities = self.sellthrough_validator.validate_opportunities(
                opportunities
            )
            
            # Filter to approved opportunities only
            if 'final_approved' in opportunities.columns:
                approved_count = opportunities['final_approved'].sum()
                self.logger.info(f"Sell-through validation: {approved_count} approved")
        else:
            self.logger.info("Step 3: Sell-through validation disabled")
        
        context.data['opportunities'] = opportunities
        
        # Step 4: Calculate ROI (if enabled)
        if self.roi_calculator and len(opportunities) > 0:
            self.logger.info("Step 4: Calculating ROI metrics...")
            opportunities = self.roi_calculator.calculate_and_filter(
                opportunities_df=opportunities,
                margin_df=margin_df
            )
            context.data['opportunities'] = opportunities
        else:
            self.logger.info("Step 4: ROI calculation disabled or no opportunities")
        
        # Step 5: Aggregate to store level
        if len(opportunities) > 0:
            self.logger.info("Step 5: Aggregating to store level...")
            results = self.results_aggregator.aggregate_to_store_level(
                opportunities_df=opportunities
            )
            
            # Add cluster metadata
            results = self.results_aggregator.add_store_metadata(
                aggregated_df=results,
                cluster_df=cluster_df
            )
            
            context.data['results'] = results
        else:
            # Create empty results for all stores (match legacy behavior)
            self.logger.warning("No opportunities after filtering. Creating empty results for all stores.")
            results = self.results_aggregator.create_empty_results(cluster_df=cluster_df)
            context.data['results'] = results
        
        return context
    
    def validate(self, context: StepContext) -> None:
        """
        VALIDATE Phase: Verify data quality and required columns.
        
        Checks:
        - Results have required columns
        - No negative quantities
        - Opportunities have required columns (if present)
        - Data types are correct
        
        Args:
            context: Step context with results
            
        Raises:
            DataValidationError: If validation fails
        """
        self.logger.info("VALIDATE: Checking data quality...")
        
        results = context.data.get('results', pd.DataFrame())
        opportunities = context.data.get('opportunities', pd.DataFrame())
        
        # Allow empty results (no opportunities found is valid)
        if len(results) == 0:
            self.logger.warning("No results to validate (no opportunities found)")
            return
        
        # Check required columns in results
        required_result_cols = [
            'str_code',
            'cluster_id',
            'total_quantity_needed'
        ]
        
        missing_cols = [col for col in required_result_cols if col not in results.columns]
        if missing_cols:
            raise DataValidationError(
                f"Results missing required columns: {missing_cols}. "
                f"Available: {list(results.columns)}"
            )
        
        # Check no negative quantities
        if (results['total_quantity_needed'] < 0).any():
            negative_count = (results['total_quantity_needed'] < 0).sum()
            raise DataValidationError(
                f"Found {negative_count} stores with negative quantities"
            )
        
        # Validate opportunities if present
        if len(opportunities) > 0:
            required_opp_cols = [
                'str_code',
                self.config.feature_column,
                'recommended_quantity'
            ]
            
            missing_cols = [col for col in required_opp_cols if col not in opportunities.columns]
            if missing_cols:
                raise DataValidationError(
                    f"Opportunities missing required columns: {missing_cols}"
                )
        
        self.logger.info(
            f"Validation passed: {len(results)} stores, "
            f"{len(opportunities)} opportunities"
        )
    
    def persist(self, context: StepContext) -> StepContext:
        """
        PERSIST Phase: Save results and generate reports.
        
        Saves:
        - Store-level results CSV
        - Opportunity-level details CSV
        - Markdown summary report
        
        Args:
            context: Step context with results
            
        Returns:
            Context with output file paths
        """
        self.logger.info("PERSIST: Saving results...")
        
        results = context.data.get('results', pd.DataFrame())
        opportunities = context.data.get('opportunities', pd.DataFrame())
        
        # Always save results file (even if empty) to match legacy behavior
        if len(results) == 0:
            self.logger.warning("No results dataframe - cannot save")
            return context
        
        # Save store-level results using repository pattern
        self.logger.info("Saving store results using repository...")
        self.output_repo.save(results)
        self.logger.info(f"✅ Saved results: {self.output_repo.file_path}")
        context.data['results_file'] = self.output_repo.file_path
        
        # Save opportunity-level details using repository pattern
        if len(opportunities) > 0:
            self.logger.info("Saving opportunities using repository...")
            # Note: Currently using same repository for both files
            # In production, should have separate repositories for results and opportunities
            # Following pattern from Steps 1, 2, 5, 6
            opportunities_path = str(self.output_repo.file_path).replace('_results_', '_opportunities_')
            opportunities.to_csv(opportunities_path, index=False)
            self.logger.info(f"✅ Saved opportunities: {opportunities_path}")
            context.data['opportunities_file'] = opportunities_path
        
        # Generate summary report
        self.logger.info("Generating summary report...")
        report = self.report_generator.generate_summary_report(
            opportunities_df=opportunities,
            aggregated_df=results
        )
        
        # Generate timestamp for report filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = (
            f"rule7_missing_{self.config.analysis_level}_"
            f"summary_{timestamp}.md"
        )
        
        self.logger.info(f"Report generated: {report_filename}")
        context.data['report_file'] = report_filename
        context.data['report_content'] = report
        
        # Log summary statistics
        total_stores = len(results)
        total_qty = results['total_quantity_needed'].sum()
        
        self.logger.info(
            f"Results summary: {total_stores} stores, "
            f"{total_qty:,.0f} total units recommended"
        )
        
        # Set state variables for summary display
        context.set_state('opportunities_count', len(opportunities))
        context.set_state('stores_with_opportunities', total_stores)
        
        if 'total_investment_required' in results.columns:
            total_investment = results['total_investment_required'].sum()
            self.logger.info(f"Total investment: ${total_investment:,.0f}")
            context.set_state('total_investment_required', total_investment)
        else:
            context.set_state('total_investment_required', 0.0)
        
        return context
