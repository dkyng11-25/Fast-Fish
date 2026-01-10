#!/usr/bin/env python3
"""Test script to isolate map generation performance issue."""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from step15_interactive_map_dashboard import load_map_data, generate_map_dashboard_html

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

def test_map_generation():
    """Test map generation to identify performance bottlenecks."""
    try:
        logger.info("Starting map data loading test...")
        
        # Load map data
        map_data, summary_stats, enhanced_data = load_map_data()
        logger.info(f"Map data loaded successfully. Shape: {map_data.shape}")
        logger.info(f"Map data columns: {list(map_data.columns)}")
        
        # Test SPU details loading
        logger.info("Loading SPU details...")
        from step15_interactive_map_dashboard import load_spu_violation_details
        spu_details = load_spu_violation_details()
        logger.info(f"SPU details loaded. Keys: {list(spu_details.keys())}")
        
        # Test HTML generation with a small sample
        logger.info("Testing HTML generation with sample data...")
        sample_data = map_data.head(100)  # Use smaller sample
        html_content = generate_map_dashboard_html(sample_data, summary_stats, spu_details)
        logger.info(f"HTML generated successfully. Length: {len(html_content)} characters")
        
        logger.info("Map generation test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in map generation test: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    test_map_generation()
