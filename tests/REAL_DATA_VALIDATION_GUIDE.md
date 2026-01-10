# Real Data Validation Guide

## Overview
This guide explains how to properly use real data validation instead of mock data in tests.

## Mock Data Issues
- Mock validation results always pass regardless of data quality
- Tests may not reflect real pipeline behavior
- False confidence in test results

## Real Data Validation
1. Use actual data from @data/ and @output/
2. Validate data quality using real validators
3. Fail tests when data quality issues exist
4. Document data sources for each test

## Implementation
```python
def validate_with_real_data(step_name: str, data_path: str) -> Dict[str, Any]:
    """Validate using real data and validators."""
    try:
        # Load real data
        data = pd.read_csv(data_path)
        
        # Use actual validator
        validator = import_validator(step_name)
        result = validator.validate(data)
        
        # Mark as real data
        result["is_mock"] = False
        result["data_source"] = "real_data"
        
        return result
    except Exception as e:
        return {
            "validation_passed": False,
            "errors": [str(e)],
            "is_mock": False,
            "data_source": "real_data"
        }
```

## Best Practices
- Always use real data when available
- Mark mock data usage clearly
- Fail tests when data quality issues exist
- Document data sources and validation methods
