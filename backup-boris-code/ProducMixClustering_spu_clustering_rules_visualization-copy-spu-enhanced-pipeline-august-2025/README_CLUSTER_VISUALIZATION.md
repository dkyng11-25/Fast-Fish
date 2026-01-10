# Advanced Cluster Map Visualization Tool

## 🎯 Overview

This repository now includes a comprehensive cluster map visualization tool that creates interactive maps and statistical dashboards for your clustering analysis results. The tool supports multiple clustering types and provides professional-grade visualizations.

## ✨ Features

### 📊 **Multi-Type Clustering Support**
- **Subcategory-Level Clustering**: Product subcategory-based store similarities
- **SPU-Level Clustering**: Granular Stock Keeping Unit analysis  
- **Category-Aggregated Clustering**: High-level category patterns

### 🗺️ **Interactive Visualizations**
- **Folium Interactive Maps**: Zoom, pan, and explore store locations
- **Cluster Navigation Controls**: Forward/backward buttons to browse individual clusters
- **Individual Cluster View**: Focus on one cluster at a time to avoid visual clutter
- **Cluster Selection Dropdown**: Jump directly to any specific cluster
- **Show All/Zoom Controls**: Toggle between all clusters and individual cluster views
- **Cluster-Based Coloring**: Distinct colors for each cluster
- **Store Popup Information**: Detailed store data on click
- **Multiple Map Layers**: Different map styles and overlays
- **Temperature Integration**: Weather data visualization when available

### 📈 **Statistical Dashboards**
- **Cluster Size Distribution**: Bar charts showing cluster composition
- **Geographic Analysis**: Scatter plots of store locations
- **Statistical Metrics**: Box plots and histograms
- **Quality Assessment**: Comprehensive cluster evaluation

### 📁 **Export Capabilities**
- **Interactive HTML Maps**: Share-ready web visualizations
- **Statistical HTML Dashboards**: Interactive plot interfaces
- **Static PNG Images**: High-resolution images for reports
- **CSV Data Exports**: Complete datasets for further analysis
- **Markdown Reports**: Comprehensive analysis summaries

## 🚀 Quick Start

### Prerequisites
```bash
pip install pandas numpy plotly folium tqdm
pip install kaleido  # Optional: for PNG export functionality
```

### Basic Usage
```bash
# Run visualization for all clustering types
python create_cluster_map_visualization.py
```

### Advanced Usage
```python
from create_cluster_map_visualization import ClusterMapVisualizer

# Create visualizer for specific clustering type
visualizer = ClusterMapVisualizer("subcategory")

# Run full analysis pipeline
output_files = visualizer.run_full_analysis()

print(f"Interactive map: {output_files['interactive_map']}")
print(f"Statistical plots: {output_files['statistical_plots']}")
```

## 📂 Generated Output Files

The tool creates the following files in `output/visualizations/`:

### 🗺️ Interactive Maps
- `cluster_map_subcategory.html`
- `cluster_map_spu.html` 
- `cluster_map_category_agg.html`

### 📊 Statistical Dashboards
- `cluster_plots_subcategory.html`
- `cluster_plots_spu.html`
- `cluster_plots_category_agg.html`

### 📋 Data Exports
- `cluster_detailed_data_[type].csv` - Complete merged datasets
- `cluster_analysis_[type].csv` - Summary statistics
- `cluster_visualization_report_[type].md` - Comprehensive reports

### 🖼️ Static Images (requires kaleido)
- `cluster_plots_[type].png` - High-resolution plot images

## 🔧 Configuration

### Clustering Types
The tool automatically detects and processes these clustering types:
- `subcategory` - Category-level analysis
- `spu` - Product-level analysis  
- `category_agg` - Aggregated category analysis

### Required Input Files
- `output/clustering_results_[type].csv` - Clustering assignments
- `data/store_coordinates_extended.csv` - Store locations
- `output/stores_with_feels_like_temperature.csv` - Temperature data (optional)

### Customization
Edit the script to modify:
- Color schemes for clusters
- Map center and zoom levels
- Statistical plot types
- Export formats

## 📊 Key Features Explained

### Interactive Maps
- **Cluster Visualization**: Each store is colored by its cluster assignment
- **Store Popups**: Click any store to see detailed information including:
  - Store code and cluster ID
  - Geographic coordinates
  - Temperature data (if available)
  - Additional store metadata

### Statistical Analysis
- **Cluster Size Distribution**: Visual representation of how stores are distributed across clusters
- **Geographic Patterns**: Identify regional clustering trends
- **Quality Metrics**: Assess clustering effectiveness
- **Temperature Integration**: Understand climate impacts on clustering

### Professional Reports
- **Executive Summaries**: Key metrics and insights
- **Methodology Documentation**: Technical approach details
- **Usage Recommendations**: Strategic and operational guidance
- **Quality Assessment**: Statistical evaluation of clustering results

## 🎨 Visualization Examples

### 🚀 **NEW! Enhanced Navigation Features**
- 🎮 **Cluster Navigation**: Use ← Previous / Next → buttons to browse clusters one by one
- 📋 **Cluster Dropdown**: Jump directly to any cluster using the selection dropdown
- 👁️ **Individual Focus**: View one cluster at a time to eliminate visual clutter
- 🌍 **Show All Option**: Toggle back to viewing all clusters simultaneously  
- 🎯 **Zoom to Cluster**: Automatically zoom to the selected cluster's geographic center
- 📊 **Live Statistics**: See real-time cluster information (size, color, store count)

### Interactive Map Features
- 🎨 **44 distinct cluster colors** for easy differentiation
- 🌍 **Multiple map layers** (OpenStreetMap, CartoDB, Dark theme)
- 📍 **Store markers** with hover tooltips and detailed popups
- 📊 **Dynamic legend** showing cluster statistics
- 🔍 **Zoom and pan** for detailed exploration
- 🎮 **Navigation controls** to browse clusters individually

### Statistical Dashboard
- 📊 **Cluster size bar chart** - Distribution of stores per cluster
- 🗺️ **Geographic scatter plot** - Store locations colored by cluster
- 📈 **Statistical box plots** - Cluster size variation analysis
- 🌡️ **Temperature histograms** - Climate distribution analysis

## 🚨 Troubleshooting

### Common Issues

**Missing PNG exports?**
```bash
pip install kaleido
```

**No temperature data visualizations?**
```bash
# Run weather data pipeline first
python src/step4_download_weather_data.py
python src/step5_calculate_feels_like_temperature.py
```

**Empty maps or missing stores?**
- Check that `data/store_coordinates_extended.csv` exists
- Verify clustering results files are present
- Ensure coordinate data contains latitude/longitude columns

### Performance Notes
- Processing 2,000+ stores takes ~10-15 seconds
- Large datasets are processed with progress bars
- Memory usage optimized for 32-64GB RAM systems

## 📈 Integration with Pipeline

This visualization tool integrates seamlessly with your existing clustering pipeline:

1. **Run clustering analysis** (`src/step6_cluster_analysis.py`)
2. **Generate coordinates** (`src/step2_extract_coordinates.py`) 
3. **Optionally add weather data** (`src/step4_download_weather_data.py`)
4. **Create visualizations** (`create_cluster_map_visualization.py`)

## 💼 Business Applications

### Strategic Planning
- **Geographic expansion**: Identify underserved regions
- **Store format optimization**: Understand regional preferences
- **Market segmentation**: Group stores by customer behavior

### Operational Excellence  
- **Inventory allocation**: Optimize product distribution
- **Logistics planning**: Improve supply chain efficiency
- **Performance benchmarking**: Compare similar store clusters

### Data-Driven Insights
- **Customer preferences**: Understand regional buying patterns
- **Seasonal impacts**: Incorporate weather data analysis
- **Store performance**: Identify high and low-performing clusters

## 🤝 Next Steps

After generating your visualizations:

1. **Explore Interactive Maps**: Open the HTML files in your web browser
2. **Analyze Statistical Dashboards**: Review cluster quality and patterns
3. **Read Comprehensive Reports**: Understand methodology and recommendations
4. **Integrate with Business Processes**: Use insights for strategic decisions
5. **Share Results**: Export static images for presentations

---

## 📝 Sample Output

Your visualization pipeline will generate:
- ✅ **3 interactive maps** (one per clustering type)
- ✅ **3 statistical dashboards** with 4 plots each
- ✅ **15 total output files** including data exports and reports
- ✅ **Professional documentation** with business insights

**Success! 🎉** Your cluster visualization tool is now complete and ready to provide deep insights into your store clustering patterns. 