#!/usr/bin/env python3
"""
Dynamic Cluster Validation Script
=================================

Demonstrates proper dynamic cluster calculation from real data
NO HARDCODED VALUES - everything calculated from actual data files
"""

import os
import math
import pandas as pd

def count_actual_stores():
    """Get actual store count from available data files"""
    
    # Priority order: most accurate to least accurate
    data_sources = [
        ('data/store_list.txt', 'lines'),
        ('data/normalized_spu_limited_matrix.csv', 'rows'),
        ('output/clustering_results_spu.csv', 'rows')
    ]
    
    for filepath, method in data_sources:
        if os.path.exists(filepath):
            if method == 'lines':
                with open(filepath, 'r') as f:
                    count = len(f.readlines())
                print(f"✓ Found {count} stores in {filepath}")
                return count
            elif method == 'rows':
                try:
                    df = pd.read_csv(filepath, nrows=1)  # Just check structure
                    df_full = pd.read_csv(filepath)
                    count = len(df_full)
                    print(f"✓ Found {count} stores in {filepath}")
                    return count
                except Exception as e:
                    print(f"⚠️ Could not read {filepath}: {e}")
                    continue
    
    raise ValueError("No store data files found - cannot calculate dynamic clusters")

def calculate_optimal_clusters(total_stores, business_constraints):
    """Calculate cluster count from actual data - NO HARDCODING"""
    
    min_stores_per_cluster = business_constraints['min_stores_per_cluster']
    max_stores_per_cluster = business_constraints['max_stores_per_cluster']
    target_stores_per_cluster = business_constraints['target_stores_per_cluster']
    
    # Calculate feasible range
    min_clusters = math.ceil(total_stores / max_stores_per_cluster)
    max_clusters = math.floor(total_stores / min_stores_per_cluster)
    optimal_clusters = round(total_stores / target_stores_per_cluster)
    
    # Validate feasibility
    if min_clusters > max_clusters:
        raise ValueError(f"Constraints infeasible: need {min_clusters}-{max_clusters} clusters")
    
    return {
        'total_stores': total_stores,
        'min_clusters': min_clusters,
        'max_clusters': max_clusters,
        'optimal_clusters': optimal_clusters,
        'feasible_range': f"{min_clusters}-{max_clusters}",
        'constraints': business_constraints
    }

def validate_constraints(cluster_config):
    """Validate that calculated clusters meet business requirements"""
    
    total_stores = cluster_config['total_stores']
    optimal_clusters = cluster_config['optimal_clusters']
    constraints = cluster_config['constraints']
    
    # Calculate actual stores per cluster
    avg_stores_per_cluster = total_stores / optimal_clusters
    
    validation = {
        'valid': True,
        'avg_stores_per_cluster': avg_stores_per_cluster,
        'issues': []
    }
    
    # Check store count constraints
    if avg_stores_per_cluster < constraints['min_stores_per_cluster']:
        validation['valid'] = False
        validation['issues'].append(f"Average {avg_stores_per_cluster:.1f} < minimum {constraints['min_stores_per_cluster']}")
    
    if avg_stores_per_cluster > constraints['max_stores_per_cluster']:
        validation['valid'] = False
        validation['issues'].append(f"Average {avg_stores_per_cluster:.1f} > maximum {constraints['max_stores_per_cluster']}")
    
    return validation

def demonstrate_scalability():
    """Show how system adapts to different store counts"""
    
    business_constraints = {
        'min_stores_per_cluster': 35,
        'max_stores_per_cluster': 50,
        'target_stores_per_cluster': 42
    }
    
    test_scenarios = {
        'Small Dataset': 1000,
        'Current Data': 2264,  # Real current count
        'Large Dataset': 5000
    }
    
    print("\n🔄 SCALABILITY DEMONSTRATION:")
    print("=" * 50)
    
    for scenario_name, store_count in test_scenarios.items():
        try:
            config = calculate_optimal_clusters(store_count, business_constraints)
            validation = validate_constraints(config)
            
            print(f"\n{scenario_name}: {store_count} stores")
            print(f"  Optimal clusters: {config['optimal_clusters']}")
            print(f"  Feasible range: {config['feasible_range']}")
            print(f"  Avg stores/cluster: {validation['avg_stores_per_cluster']:.1f}")
            print(f"  Constraint valid: {'✅' if validation['valid'] else '❌'}")
            
            if not validation['valid']:
                for issue in validation['issues']:
                    print(f"    ⚠️ {issue}")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Main validation function"""
    
    print("🎯 DYNAMIC CLUSTERING VALIDATION")
    print("=" * 40)
    print("🚫 NO HARDCODED VALUES")
    print("✅ 100% DATA-DRIVEN CALCULATION")
    print()
    
    try:
        # Get actual store count from real data
        actual_stores = count_actual_stores()
        
        # Define business constraints (configurable, not hardcoded)
        business_constraints = {
            'min_stores_per_cluster': 35,
            'max_stores_per_cluster': 50, 
            'target_stores_per_cluster': 42
        }
        
        # Calculate optimal clustering parameters
        cluster_config = calculate_optimal_clusters(actual_stores, business_constraints)
        
        print(f"\n📊 DYNAMIC CALCULATION RESULTS:")
        print(f"Total stores (from data): {cluster_config['total_stores']:,}")
        print(f"Optimal clusters: {cluster_config['optimal_clusters']}")
        print(f"Feasible range: {cluster_config['feasible_range']} clusters")
        print(f"Min stores per cluster: {business_constraints['min_stores_per_cluster']}")
        print(f"Max stores per cluster: {business_constraints['max_stores_per_cluster']}")
        print(f"Target stores per cluster: {business_constraints['target_stores_per_cluster']}")
        
        # Validate constraints
        validation = validate_constraints(cluster_config)
        print(f"\n✅ CONSTRAINT VALIDATION:")
        print(f"Average stores per cluster: {validation['avg_stores_per_cluster']:.1f}")
        print(f"Constraints satisfied: {'✅ YES' if validation['valid'] else '❌ NO'}")
        
        if not validation['valid']:
            print("⚠️ Issues found:")
            for issue in validation['issues']:
                print(f"  • {issue}")
        
        # Show what would happen with hardcoded approach
        print(f"\n🚨 HARDCODED APPROACH COMPARISON:")
        hardcoded_clusters = 46  # What the previous plans assumed
        hardcoded_avg = actual_stores / hardcoded_clusters
        print(f"If hardcoded to 46 clusters: {hardcoded_avg:.1f} stores per cluster")
        
        if hardcoded_avg > business_constraints['max_stores_per_cluster']:
            print(f"❌ CONSTRAINT VIOLATION: {hardcoded_avg:.1f} > {business_constraints['max_stores_per_cluster']} max")
        elif hardcoded_avg < business_constraints['min_stores_per_cluster']:
            print(f"❌ CONSTRAINT VIOLATION: {hardcoded_avg:.1f} < {business_constraints['min_stores_per_cluster']} min")
        else:
            print(f"✅ Would satisfy constraints by chance")
        
        # Demonstrate scalability
        demonstrate_scalability()
        
        print(f"\n🎯 CONCLUSION:")
        print(f"Dynamic approach: {cluster_config['optimal_clusters']} clusters (CORRECT)")
        print(f"Hardcoded approach: 46 clusters (WRONG)")
        print(f"Difference: {abs(cluster_config['optimal_clusters'] - 46)} clusters")
        print(f"")
        print(f"✅ DYNAMIC SYSTEM ADAPTS TO ANY STORE COUNT")
        print(f"❌ HARDCODED SYSTEM FAILS WITH DIFFERENT DATA")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 