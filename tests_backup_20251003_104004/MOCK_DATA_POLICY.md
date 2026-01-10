# Mock Data Usage Policy

## Policy Statement
Mock data should only be used for unit tests of individual functions, not for integration tests of pipeline steps.

## Allowed Uses
- Unit tests of individual functions
- Testing error handling
- Testing edge cases
- Development and debugging

## Prohibited Uses
- Integration tests of pipeline steps
- End-to-end testing
- Production validation
- Performance testing

## Implementation Requirements
1. Mock data must be clearly marked with `is_mock: True`
2. Mock validation results must fail by default
3. Real data must be used when available
4. Mock data usage must be documented

## Validation Results
```python
# Mock data validation result
{
    "validation_passed": False,  # Must fail by default
    "is_mock": True,  # Must be marked as mock
    "errors": ["Mock data used - not real validation"],
    "warnings": ["Results not reliable - mock data"],
    "data_source": "synthetic"
}

# Real data validation result
{
    "validation_passed": True,  # Based on actual validation
    "is_mock": False,  # Real data
    "errors": [],
    "warnings": [],
    "data_source": "real_data"
}
```

## Enforcement
- All mock data usage must be reviewed
- Tests using mock data must be clearly marked
- Real data validation must be implemented where possible
- Mock data fallbacks must be documented
