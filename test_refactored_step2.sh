#!/bin/bash

# Set the project root directory
PROJECT_ROOT="/mnt/c/Users/andyk/Downloads/emergency/ProducMixClustering_spu_clustering_rules_visualization-copy"

# Set the Python path to include the project root
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Change to the project directory
cd "${PROJECT_ROOT}" || exit 1

# Run the refactored Step 2 with the latest data
python src/steps/extract_coordinates_step.py
