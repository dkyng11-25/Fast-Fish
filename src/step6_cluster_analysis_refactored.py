#!/usr/bin/env python3
"""
Step 6: Cluster Analysis (Refactored)

This script uses the refactored ClusterAnalysisStep implementation.
It performs clustering analysis on store-level matrices to group similar stores.

Usage:
    # Run with default configuration (from environment variables)
    python src/step6_cluster_analysis_refactored.py
    
    # Run for specific period and matrix type
    python src/step6_cluster_analysis_refactored.py --target-yyyymm 202510 --target-period A --matrix-type spu
    
    # Run with temperature constraints enabled
    python src/step6_cluster_analysis_refactored.py --enable-temperature-constraints
    
    # Run with custom cluster configuration
    python src/step6_cluster_analysis_refactored.py --pca-components 30 --target-cluster-size 60
    
Environment Variables:
    PIPELINE_TARGET_YYYYMM: Target year-month (default: 202510)
    PIPELINE_TARGET_PERIOD: Target period A or B (default: A)
    PIPELINE_MATRIX_TYPE: Matrix type (default: spu)
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from steps.cluster_analysis_factory import create_cluster_analysis_step
from core.context import StepContext
from core.exceptions import DataValidationError


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Step 6: Cluster Analysis for store grouping (Refactored)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Period configuration
    parser.add_argument(
        '--target-yyyymm',
        type=str,
        default=os.environ.get('PIPELINE_TARGET_YYYYMM', '202510'),
        help='Target year-month (e.g., 202510). Default: from PIPELINE_TARGET_YYYYMM env var or 202510'
    )
    
    parser.add_argument(
        '--target-period',
        type=str,
        choices=['A', 'B'],
        default=os.environ.get('PIPELINE_TARGET_PERIOD', 'A'),
        help='Target period (A or B). Default: from PIPELINE_TARGET_PERIOD env var or A'
    )
    
    # Matrix configuration
    parser.add_argument(
        '--matrix-type',
        type=str,
        choices=['spu', 'subcategory', 'category_agg'],
        default=os.environ.get('PIPELINE_MATRIX_TYPE', 'spu'),
        help='Type of matrix to cluster (spu, subcategory, category_agg). Default: spu'
    )
    
    # Output configuration
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory for output files (default: output)'
    )
    
    # PCA configuration
    parser.add_argument(
        '--pca-components',
        type=int,
        default=20,
        help='Number of PCA components for dimensionality reduction (default: 20)'
    )
    
    # Clustering configuration
    parser.add_argument(
        '--target-cluster-size',
        type=int,
        default=50,
        help='Target number of stores per cluster (default: 50)'
    )
    
    parser.add_argument(
        '--min-cluster-size',
        type=int,
        default=30,
        help='Minimum allowed cluster size (default: 30)'
    )
    
    parser.add_argument(
        '--max-cluster-size',
        type=int,
        default=60,
        help='Maximum allowed cluster size (default: 60)'
    )
    
    parser.add_argument(
        '--max-balance-iterations',
        type=int,
        default=100,
        help='Maximum iterations for cluster balancing (default: 100)'
    )
    
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    # Temperature constraints
    parser.add_argument(
        '--enable-temperature-constraints',
        action='store_true',
        help='Enable temperature-aware clustering (default: disabled)'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Display configuration
    print("=" * 80)
    print("Step 6: Cluster Analysis (Refactored)")
    print("=" * 80)
    print(f"Period: {args.target_yyyymm}{args.target_period}")
    print(f"Matrix Type: {args.matrix_type}")
    print(f"PCA Components: {args.pca_components}")
    print(f"Target Cluster Size: {args.target_cluster_size}")
    print(f"Cluster Size Range: [{args.min_cluster_size}, {args.max_cluster_size}]")
    print(f"Temperature Constraints: {'Enabled' if args.enable_temperature_constraints else 'Disabled'}")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 80)
    print()
    
    try:
        # Create step with factory
        print("Creating Step 6 with dependencies...")
        step = create_cluster_analysis_step(
            matrix_type=args.matrix_type,
            target_yyyymm=args.target_yyyymm,
            target_period=args.target_period,
            output_dir=args.output_dir,
            pca_components=args.pca_components,
            target_cluster_size=args.target_cluster_size,
            min_cluster_size=args.min_cluster_size,
            max_cluster_size=args.max_cluster_size,
            enable_temperature_constraints=args.enable_temperature_constraints,
            max_balance_iterations=args.max_balance_iterations,
            random_state=args.random_state
        )
        
        # Create initial context
        context = StepContext()
        
        # Execute step
        print("Executing Step 6...")
        print()
        final_context = step.execute(context)
        
        # Display results
        print()
        print("=" * 80)
        print("✅ Step 6 completed successfully!")
        print("=" * 80)
        
        # Show summary
        results = final_context.data.get('results')
        if results is not None:
            n_stores = len(results)
            n_clusters = results['Cluster'].nunique()
            
            print(f"Clustered {n_stores} stores into {n_clusters} clusters")
            print()
            print("Cluster Distribution:")
            cluster_counts = results['Cluster'].value_counts().sort_index()
            for cluster_id, count in cluster_counts.items():
                print(f"  Cluster {cluster_id}: {count} stores")
            
            print()
            print(f"Output files saved to: {args.output_dir}/")
            print(f"  - clustering_results_{args.matrix_type}_{args.target_yyyymm}{args.target_period}_*.csv")
            print(f"  - cluster_profiles_{args.matrix_type}_{args.target_yyyymm}{args.target_period}_*.csv")
            print(f"  - per_cluster_metrics_{args.matrix_type}_{args.target_yyyymm}{args.target_period}_*.csv")
            print(f"  - cluster_visualization_{args.matrix_type}_{args.target_yyyymm}{args.target_period}.png")
        
        print("=" * 80)
        return 0
        
    except DataValidationError as e:
        print()
        print("=" * 80)
        print("❌ Step 6 validation failed!")
        print("=" * 80)
        print(f"Error: {e}")
        print("=" * 80)
        return 1
        
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("⚠️  Step 6 interrupted by user")
        print("=" * 80)
        return 130
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Step 6 execution failed!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
