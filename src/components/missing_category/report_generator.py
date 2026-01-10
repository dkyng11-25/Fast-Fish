"""Report generator component for creating summary reports."""

import fireducks.pandas as pd
from datetime import datetime
from typing import Optional
from .config import MissingCategoryConfig


class ReportGenerator:
    """
    Generates markdown summary reports for missing category analysis.
    
    Creates comprehensive reports with:
    - Executive summary
    - Sell-through distribution
    - Quantity and price diagnostics
    - Top opportunities
    """
    
    def __init__(self, config: MissingCategoryConfig, logger):
        """
        Initialize report generator.
        
        Args:
            config: Configuration for the analysis
            logger: Pipeline logger instance
        """
        self.config = config
        self.logger = logger
    
    def generate_summary_report(
        self,
        opportunities_df: pd.DataFrame,
        aggregated_df: pd.DataFrame
    ) -> str:
        """
        Generate comprehensive summary report.
        
        Args:
            opportunities_df: Opportunity-level data
            aggregated_df: Store-level aggregated data
            
        Returns:
            Markdown-formatted report string
        """
        self.logger.info("Generating summary report...")
        
        report_lines = []
        
        # Header
        report_lines.extend(self._format_header())
        
        # Seasonal blending info
        if self.config.use_blended_seasonal:
            report_lines.extend(self._format_seasonal_info())
        
        # Executive summary
        report_lines.extend(self._format_executive_summary(
            opportunities_df, aggregated_df
        ))
        
        # Sell-through distribution
        if 'predicted_sellthrough' in opportunities_df.columns:
            report_lines.extend(self._format_sellthrough_distribution(
                opportunities_df
            ))
        
        # Quantity and price diagnostics
        report_lines.extend(self._format_diagnostics(opportunities_df))
        
        # Fast Fish compliance
        if 'final_approved' in opportunities_df.columns:
            report_lines.extend(self._format_fastfish_compliance(
                opportunities_df
            ))
        
        # Top opportunities
        report_lines.extend(self._format_top_opportunities(
            opportunities_df
        ))
        
        report = '\n'.join(report_lines)
        
        self.logger.info(f"Report generated: {len(report_lines)} lines")
        
        return report
    
    def _format_header(self) -> list:
        """Format report header."""
        return [
            f"# Missing {self.config.analysis_level.title()} Analysis Report",
            "",
            f"**Period:** {self.config.period_label}",
            f"**Analysis Level:** {self.config.analysis_level}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
    
    def _format_seasonal_info(self) -> list:
        """Format seasonal blending information."""
        return [
            "## Seasonal Data Blending",
            "",
            f"- **Enabled:** Yes",
            f"- **Recent Weight:** {self.config.recent_weight:.0%}",
            f"- **Seasonal Weight:** {self.config.seasonal_weight:.0%}",
            f"- **Years Back:** {self.config.seasonal_years_back}",
            "",
            "---",
            ""
        ]
    
    def _format_executive_summary(
        self,
        opportunities_df: pd.DataFrame,
        aggregated_df: pd.DataFrame
    ) -> list:
        """Format executive summary section."""
        lines = [
            "## Executive Summary",
            ""
        ]
        
        if len(opportunities_df) == 0:
            lines.append("**No opportunities identified.**")
            return lines
        
        # Calculate metrics
        total_stores = len(aggregated_df)
        total_opps = len(opportunities_df)
        total_qty = opportunities_df['recommended_quantity'].sum()
        
        lines.extend([
            f"- **Stores with Opportunities:** {total_stores:,}",
            f"- **Total Opportunities:** {total_opps:,}",
            f"- **Total Units Recommended:** {total_qty:,.0f}",
        ])
        
        if 'investment_required' in opportunities_df.columns:
            total_investment = opportunities_df['investment_required'].sum()
            lines.append(f"- **Total Investment:** ${total_investment:,.0f}")
        
        if 'margin_uplift' in opportunities_df.columns:
            total_margin = opportunities_df['margin_uplift'].sum()
            avg_roi = opportunities_df['roi'].mean() if 'roi' in opportunities_df.columns else 0
            lines.extend([
                f"- **Total Margin Uplift:** ${total_margin:,.0f}",
                f"- **Average ROI:** {avg_roi:.1%}"
            ])
        
        lines.extend(["", "---", ""])
        
        return lines
    
    def _format_sellthrough_distribution(
        self,
        opportunities_df: pd.DataFrame
    ) -> list:
        """Format sell-through distribution section."""
        lines = [
            "## Sell-Through Distribution",
            ""
        ]
        
        st_col = 'predicted_sellthrough'
        if st_col not in opportunities_df.columns:
            return lines
        
        # Calculate distribution
        bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
        labels = ['<30%', '30-50%', '50-70%', '70-90%', '90%+']
        
        opportunities_df['st_bin'] = pd.cut(
            opportunities_df[st_col],
            bins=bins,
            labels=labels,
            include_lowest=True
        )
        
        distribution = opportunities_df['st_bin'].value_counts().sort_index()
        
        lines.append("| Range | Count | Percentage |")
        lines.append("|-------|-------|------------|")
        
        total = len(opportunities_df)
        for label in labels:
            count = distribution.get(label, 0)
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"| {label} | {count:,} | {pct:.1f}% |")
        
        lines.extend(["", "---", ""])
        
        return lines
    
    def _format_diagnostics(
        self,
        opportunities_df: pd.DataFrame
    ) -> list:
        """Format quantity and price diagnostics section."""
        lines = [
            "## Quantity & Price Diagnostics",
            ""
        ]
        
        if len(opportunities_df) == 0:
            return lines
        
        # Quantity distribution
        qty_stats = opportunities_df['recommended_quantity'].describe()
        lines.extend([
            "### Quantity Distribution",
            "",
            f"- **Mean:** {qty_stats['mean']:.1f} units",
            f"- **Median:** {qty_stats['50%']:.1f} units",
            f"- **Min:** {qty_stats['min']:.0f} units",
            f"- **Max:** {qty_stats['max']:.0f} units",
            ""
        ])
        
        # Price source distribution
        if 'price_source' in opportunities_df.columns:
            price_sources = opportunities_df['price_source'].value_counts()
            lines.extend([
                "### Price Source Distribution",
                ""
            ])
            for source, count in price_sources.items():
                pct = count / len(opportunities_df) * 100
                lines.append(f"- **{source}:** {count:,} ({pct:.1f}%)")
            lines.append("")
        
        lines.extend(["---", ""])
        
        return lines
    
    def _format_fastfish_compliance(
        self,
        opportunities_df: pd.DataFrame
    ) -> list:
        """Format Fast Fish compliance section."""
        lines = [
            "## Fast Fish Compliance",
            ""
        ]
        
        if 'final_approved' not in opportunities_df.columns:
            return lines
        
        approved = opportunities_df['final_approved'].sum()
        total = len(opportunities_df)
        approval_rate = (approved / total * 100) if total > 0 else 0
        
        lines.extend([
            f"- **Approved:** {approved:,} / {total:,} ({approval_rate:.1f}%)",
            f"- **Rejected:** {total - approved:,}",
            ""
        ])
        
        if 'avg_predicted_sellthrough' in opportunities_df.columns:
            avg_st = opportunities_df[opportunities_df['final_approved']]['predicted_sellthrough'].mean()
            lines.append(f"- **Avg ST (Approved):** {avg_st:.1%}")
            lines.append("")
        
        lines.extend(["---", ""])
        
        return lines
    
    def _format_top_opportunities(
        self,
        opportunities_df: pd.DataFrame,
        top_n: int = 10
    ) -> list:
        """Format top opportunities table."""
        lines = [
            f"## Top {top_n} Opportunities",
            ""
        ]
        
        if len(opportunities_df) == 0:
            return lines
        
        # Sort by investment or quantity
        sort_col = 'margin_uplift' if 'margin_uplift' in opportunities_df.columns else 'recommended_quantity'
        top_opps = opportunities_df.nlargest(top_n, sort_col)
        
        # Create table
        lines.append("| Store | Feature | Qty | Price | Investment | Margin | ROI |")
        lines.append("|-------|---------|-----|-------|------------|--------|-----|")
        
        feature_col = self.config.feature_column
        
        for _, opp in top_opps.iterrows():
            store = opp['str_code']
            feature = opp[feature_col][:20] if len(str(opp[feature_col])) > 20 else opp[feature_col]
            qty = opp['recommended_quantity']
            price = opp.get('unit_price', 0)
            investment = opp.get('investment_required', 0)
            margin = opp.get('margin_uplift', 0)
            roi = opp.get('roi', 0)
            
            lines.append(
                f"| {store} | {feature} | {qty:.0f} | ${price:.0f} | "
                f"${investment:,.0f} | ${margin:,.0f} | {roi:.0%} |"
            )
        
        lines.extend(["", "---", ""])
        
        return lines
