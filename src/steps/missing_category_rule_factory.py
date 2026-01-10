"""Factory for creating MissingCategoryRuleStep instances."""

from typing import Optional

from src.core.logger import PipelineLogger
from src.components.missing_category import MissingCategoryConfig
from src.repositories.cluster_repository import ClusterRepository
from src.repositories.sales_repository import SalesRepository
from src.repositories.quantity_repository import QuantityRepository
from src.repositories.margin_repository import MarginRepository
from src.steps.missing_category_rule_step import MissingCategoryRuleStep


class MissingCategoryRuleFactory:
    """
    Factory for creating MissingCategoryRuleStep with all dependencies injected.
    
    Handles:
    - Repository creation
    - Component initialization
    - Dependency injection
    """
    
    @staticmethod
    def create(
        csv_repo,
        logger: PipelineLogger,
        config: Optional[MissingCategoryConfig] = None,
        fastfish_validator = None,
        output_repo = None
    ) -> MissingCategoryRuleStep:
        """
        Create MissingCategoryRuleStep with all dependencies.
        
        Args:
            csv_repo: Base CSV repository for file operations
            logger: Pipeline logger instance
            config: Configuration (creates default if None)
            fastfish_validator: Fast Fish validator instance (optional)
            output_repo: Output repository for saving results (optional, defaults to csv_repo)
            
        Returns:
            Configured MissingCategoryRuleStep instance
        """
        # Create config if not provided
        if config is None:
            config = MissingCategoryConfig.from_env_and_args()
        
        # Use csv_repo as output_repo if not provided
        if output_repo is None:
            output_repo = csv_repo
        
        # Create domain repositories
        cluster_repo = ClusterRepository(csv_repo, logger)
        sales_repo = SalesRepository(csv_repo, logger)
        quantity_repo = QuantityRepository(csv_repo, logger)
        margin_repo = MarginRepository(csv_repo, logger)
        
        # Create and return step
        return MissingCategoryRuleStep(
            cluster_repo=cluster_repo,
            sales_repo=sales_repo,
            quantity_repo=quantity_repo,
            margin_repo=margin_repo,
            output_repo=output_repo,
            sellthrough_validator=fastfish_validator,
            config=config,
            logger=logger
        )
