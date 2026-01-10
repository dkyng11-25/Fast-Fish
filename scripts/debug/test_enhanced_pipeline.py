#!/usr/bin/env python3
"""
Enhanced Pipeline Test Script
============================

Tests the complete enhanced SPU aggregation pipeline:
1. Step 13: Consolidate rules with dimensional data
2. Step 14: Enhanced Fast Fish format with outputFormat.md compliance
3. Validation: All required fields and data quality

This script verifies that all enhanced functionality works correctly.
"""

import pandas as pd
import numpy as np
import os
import sys
import subprocess
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_step13_execution():
    """Test Step 13 execution"""
    logger.info("🧪 Testing Step 13: Consolidate SPU Rules...")
    
    try:
        # Run step 13
        result = subprocess.run(
            ["python", "src/step13_consolidate_spu_rules.py"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Step 13 executed successfully")
            return True
        else:
            logger.error(f"❌ Step 13 failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Step 13 timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Step 13 exception: {e}")
        return False

def test_step14_execution():
    """Test enhanced Step 14 execution"""
    logger.info("🧪 Testing Enhanced Step 14: Fast Fish Format...")
    
    try:
        # Run enhanced step 14
        result = subprocess.run(
            ["python", "src/step14_create_fast_fish_format.py"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Enhanced Step 14 executed successfully")
            return True, result.stdout
        else:
            logger.error(f"❌ Enhanced Step 14 failed: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Enhanced Step 14 timed out")
        return False, "Timeout"
    except Exception as e:
        logger.error(f"❌ Enhanced Step 14 exception: {e}")
        return False, str(e)

def validate_enhanced_output():
    """Validate the enhanced output format"""
    logger.info("🔍 Validating enhanced output format...")
    
    # Find the latest enhanced output file
    import glob
    output_files = glob.glob("output/enhanced_fast_fish_format_*.csv")
    if not output_files:
        logger.error("❌ No enhanced output files found")
        return False, {}
    
    latest_file = max(output_files, key=os.path.getmtime)
    logger.info(f"Validating file: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file)
        logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns")
        
        # Required outputFormat.md fields
        required_fields = [
            'Year', 'Month', 'Period', 'Store_Group_Name', 'Target_Style_Tags',
            'Current_SPU_Quantity', 'Target_SPU_Quantity', 'ΔQty',
            'Data_Based_Rationale', 'Expected_Benefit',
            'men_percentage', 'women_percentage',
            'front_store_percentage', 'back_store_percentage',
            'Display_Location', 'Temp_14d_Avg', 'Historical_ST%'
        ]
        
        validation_results = {}
        missing_fields = []
        
        # Check for required fields
        for field in required_fields:
            if field in df.columns:
                validation_results[f"has_{field}"] = True
            else:
                missing_fields.append(field)
                validation_results[f"has_{field}"] = False
        
        # Check dimensional Target_Style_Tags format
        sample_tags = df['Target_Style_Tags'].iloc[:5].tolist()
        dimensional_format = all('[' in str(tag) and ']' in str(tag) and ',' in str(tag) for tag in sample_tags)
        validation_results['dimensional_target_style_tags'] = dimensional_format
        
        # Check customer mix percentages
        has_customer_mix = ('men_percentage' in df.columns and 
                          'women_percentage' in df.columns and
                          df['men_percentage'].notna().any())
        validation_results['has_customer_mix'] = has_customer_mix
        
        # Check ΔQty calculation
        delta_qty_correct = ('ΔQty' in df.columns and 
                           (df['ΔQty'] == df['Target_SPU_Quantity'] - df['Current_SPU_Quantity']).all())
        validation_results['delta_qty_correct'] = delta_qty_correct
        
        # Data quality checks
        validation_results['no_null_store_groups'] = df['Store_Group_Name'].isnull().sum() == 0
        validation_results['positive_spu_counts'] = (df['Target_SPU_Quantity'] >= 0).all()
        validation_results['valid_percentages'] = (
            (df['men_percentage'] >= 0).all() and (df['men_percentage'] <= 100).all() and
            (df['women_percentage'] >= 0).all() and (df['women_percentage'] <= 100).all()
        )
        
        # Calculate scores
        structure_score = (len(required_fields) - len(missing_fields)) / len(required_fields) * 100
        dimensional_score = 100 if dimensional_format else 0
        fields_score = 100 if len(missing_fields) == 0 else 0
        
        validation_results['structure_score'] = structure_score
        validation_results['dimensional_score'] = dimensional_score  
        validation_results['fields_score'] = fields_score
        validation_results['missing_fields'] = missing_fields
        validation_results['sample_target_style_tags'] = sample_tags
        
        # Overall validation
        overall_pass = (structure_score >= 90 and dimensional_score >= 90 and fields_score >= 90)
        
        logger.info(f"📊 Validation Results:")
        logger.info(f"   Structure Score: {structure_score:.1f}%")
        logger.info(f"   Dimensional Score: {dimensional_score:.1f}%")
        logger.info(f"   Fields Score: {fields_score:.1f}%")
        
        if missing_fields:
            logger.warning(f"   Missing Fields: {missing_fields}")
        
        if overall_pass:
            logger.info("✅ Validation PASSED - Enhanced output is compliant!")
        else:
            logger.error("❌ Validation FAILED - Output needs improvement")
        
        return overall_pass, validation_results
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return False, {"error": str(e)}

def run_enhanced_pipeline_test():
    """Run complete enhanced pipeline test"""
    logger.info("🚀 Starting Enhanced Pipeline Test...")
    logger.info("="*60)
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'step13_success': False,
        'step14_success': False,
        'validation_success': False,
        'validation_details': {}
    }
    
    # Test Step 13
    step13_success = test_step13_execution()
    test_results['step13_success'] = step13_success
    
    if not step13_success:
        logger.error("❌ Step 13 failed, skipping remaining tests")
        return test_results
    
    # Test Enhanced Step 14
    step14_success, step14_output = test_step14_execution()
    test_results['step14_success'] = step14_success
    test_results['step14_output'] = step14_output
    
    if not step14_success:
        logger.error("❌ Enhanced Step 14 failed, skipping validation")
        return test_results
    
    # Validate Output
    validation_success, validation_details = validate_enhanced_output()
    test_results['validation_success'] = validation_success
    test_results['validation_details'] = validation_details
    
    # Final Summary
    logger.info("="*60)
    logger.info("🏁 ENHANCED PIPELINE TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Step 13 (Consolidation): {'✅ PASS' if step13_success else '❌ FAIL'}")
    logger.info(f"Step 14 (Enhanced Format): {'✅ PASS' if step14_success else '❌ FAIL'}")
    logger.info(f"Output Validation: {'✅ PASS' if validation_success else '❌ FAIL'}")
    
    overall_success = step13_success and step14_success and validation_success
    logger.info(f"Overall Result: {'🎉 ALL TESTS PASSED!' if overall_success else '⚠️ TESTS FAILED'}")
    
    # Save test results
    test_file = f"test_results_enhanced_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(test_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"Test results saved: {test_file}")
    
    return test_results

def main():
    """Main test execution"""
    
    # Check prerequisites
    logger.info("Checking prerequisites...")
    
    required_files = [
        'src/step13_consolidate_spu_rules.py',
        'src/step14_create_fast_fish_format.py'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    # Check data availability
    possible_api_files = [
        'data/api_data/complete_spu_sales_202506A.csv',
        'data/api_data/complete_spu_sales_202407A.csv',
        'data/api_data/complete_spu_sales_202505.csv'
    ]
    
    api_file_found = any(os.path.exists(f) for f in possible_api_files)
    if not api_file_found:
        logger.error("Missing API data files - none of the expected files found")
        return False
    
    logger.info("✅ Prerequisites checked")
    
    # Run test
    results = run_enhanced_pipeline_test()
    
    return results['validation_success'] if 'validation_success' in results else False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 