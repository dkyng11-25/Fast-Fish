"""
Fast Fish Store Clustering - Final Optimized Modules
=====================================================

This package contains the final optimized clustering pipeline with ALL improvements:

C3 Improvements (Baseline 1):
- I1: Store Profile Features (str_type, sal_type, traffic)
- I2: Fixed Cluster Count (30 clusters)

Final Improvements (A + B + C):
- A: Block-wise Feature Architecture (separate PCA per block)
- B: Alternative Normalization (log-transform + row normalization)
- C: Algorithm Optimization (L2 normalization + optimized KMeans)

Modules:
- step1_download_api_data.py: Download data from FastFish API
- step2_extract_coordinates.py: Extract store coordinates
- step3_prepare_matrix_final.py: Prepare matrix with Improvement B
- step4_download_weather_data.py: Download weather data
- step5_calculate_feels_like_temperature.py: Calculate feels-like temperature
- step6_cluster_analysis_final.py: Final optimized clustering (ALL improvements)
- run_final_pipeline.py: Complete pipeline runner with visualizations

Usage:
    python run_final_pipeline.py

Results:
- Silhouette Score: ~0.3754 (+685% vs baseline)
- Cluster Count: 30 (compliant with 20-40 requirement)
- Cluster Size Range: 26-177 (well-balanced)
"""

__version__ = "1.0.0"
__author__ = "Fast Fish Data Science Team"
