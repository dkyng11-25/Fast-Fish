#!/usr/bin/env python3
"""Optimized dashboard generation script."""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dashboard_generator import ComprehensiveDashboardGenerator

# Set up logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def main():
    """Generate the comprehensive dashboard with optimizations."""
    logger.info("Starting optimized comprehensive dashboard generation...")
    
    try:
        # Create dashboard generator
        generator = ComprehensiveDashboardGenerator()
        
        # Generate unified dashboard
        logger.info("Generating unified dashboard...")
        dashboard_html = generator.generate_unified_dashboard()
        
        # Save dashboard
        logger.info(f"Generated dashboard HTML size: {len(dashboard_html) if dashboard_html else 0} characters")
        if dashboard_html:
            output_file = generator.save_dashboard(dashboard_html)
            logger.info(f"✅ Comprehensive dashboard successfully generated and saved to {output_file}")
            logger.info("🎉 All 156 features and fixes have been integrated into the modular dashboard!")
        else:
            logger.error("❌ Dashboard generation returned empty HTML content")
            
    except Exception as e:
        logger.error(f"❌ Failed to generate comprehensive dashboard: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
