#!/bin/bash
# Run Step 13 tests with clean environment

# Unset any existing pipeline environment variables
unset PIPELINE_TARGET_YYYYMM
unset PIPELINE_TARGET_PERIOD
unset PIPELINE_YYYYMM
unset PIPELINE_PERIOD

# Set the correct period for tests
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A

# Run the tests
python3 -m pytest tests/step13/ -v "$@"
