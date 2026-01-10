"""
Analyze missing store codes between mapping and coordinates files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_latest_file(pattern: str) -> pd.DataFrame:
    """Load the most recent file matching the pattern."""
    files = list(DATA_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"Loading: {latest_file}")
    return pd.read_csv(latest_file, dtype={'str_code': str})

def analyze_missing_stores():
    """Analyze stores in mapping file missing from coordinates file."""
    # Load data
    try:
        # Load mapping file (contains store-SPU relationships)
        mapping_df = load_latest_file("spu_store_mapping_*.csv")
        
        # Load coordinates file
        coords_df = load_latest_file("store_coordinates_extended_*.csv")
        
        # Convert store codes to string and ensure they're in the same format
        mapping_df['str_code'] = mapping_df['str_code'].astype(str).str.strip()
        coords_df['str_code'] = coords_df['str_code'].astype(str).str.strip()
        
        # Find stores in mapping but not in coordinates
        missing_stores = set(mapping_df['str_code']) - set(coords_df['str_code'])
        
        # Get details about these stores from the mapping file
        missing_stores_df = mapping_df[mapping_df['str_code'].isin(missing_stores)]
        
        # Save the analysis results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = OUTPUT_DIR / f'missing_stores_analysis_{timestamp}.xlsx'
        
        with pd.ExcelWriter(output_file) as writer:
            # Summary sheet
            summary = pd.DataFrame({
                'total_stores_in_mapping': [mapping_df['str_code'].nunique()],
                'total_stores_in_coordinates': [coords_df['str_code'].nunique()],
                'missing_stores_count': [len(missing_stores)],
                'analysis_date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'mapping_file': [str(max(DATA_DIR.glob("spu_store_mapping_*.csv"), key=lambda f: f.stat().st_mtime))],
                'coordinates_file': [str(max(DATA_DIR.glob("store_coordinates_extended_*.csv"), key=lambda f: f.stat().st_mtime))]
            })
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Missing stores details
            if not missing_stores_df.empty:
                missing_stores_df.to_excel(writer, sheet_name='Missing_Stores', index=False)
                
                # Count of SPUs per missing store
                spu_counts = missing_stores_df.groupby('str_code')['spu_code'].count().reset_index()
                spu_counts.columns = ['str_code', 'spu_count']
                spu_counts = spu_counts.sort_values('spu_count', ascending=False)
                spu_counts.to_excel(writer, sheet_name='SPU_Counts', index=False)
                
                # Categories affected
                categories = missing_stores_df.groupby('cate_name')['str_code'].nunique().reset_index()
                categories.columns = ['category', 'store_count']
                categories = categories.sort_values('store_count', ascending=False)
                categories.to_excel(writer, sheet_name='Categories_Affected', index=False)
        
        print(f"\nAnalysis complete. Results saved to: {output_file}")
        print(f"Total stores in mapping: {mapping_df['str_code'].nunique()}")
        print(f"Total stores in coordinates: {coords_df['str_code'].nunique()}")
        print(f"Missing stores: {len(missing_stores)}")
        
        if missing_stores:
            print("\nExample missing store codes:", 
                  ", ".join(sorted(missing_stores)[:5]) + ("..." if len(missing_stores) > 5 else ""))
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    analyze_missing_stores()
