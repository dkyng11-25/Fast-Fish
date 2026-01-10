#!/usr/bin/env python3
"""
Advanced Cluster Map Visualization Tool

This script creates comprehensive cluster map visualizations using the clustering results
from the Product Mix Clustering Pipeline. It supports multiple clustering types and
provides interactive maps with detailed cluster analysis.

Key Features:
- Support for subcategory, SPU, and category-aggregated clustering
- Interactive Folium maps with cluster-based coloring
- Plotly-based statistical visualizations
- Comprehensive cluster analysis and metrics
- Temperature-aware visualization (if available)
- Memory-efficient processing for large datasets
- Multiple export formats (HTML, PNG, CSV)

Author: Data Pipeline
Date: 2025-06-14
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium import plugins
import os
import warnings
import json
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime
from tqdm import tqdm
import logging

# Suppress warnings
warnings.filterwarnings('ignore')

# ——— CONFIGURATION ———

# Clustering type configuration
CLUSTERING_TYPES = ["subcategory", "spu", "category_agg"]
DEFAULT_CLUSTERING_TYPE = "subcategory"

# File paths configuration
DATA_DIR = "data"
OUTPUT_DIR = "output"
VIZ_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "visualizations")

# Create visualization output directory
os.makedirs(VIZ_OUTPUT_DIR, exist_ok=True)

# Color schemes for different clustering types
CLUSTER_COLOR_SCHEMES = {
    "subcategory": "Set3",
    "spu": "tab20",
    "category_agg": "Pastel1"
}

# Map configuration
DEFAULT_MAP_CENTER = [39.8283, -98.5795]  # Geographic center of US
DEFAULT_ZOOM = 4

class ClusterMapVisualizer:
    """
    Advanced cluster map visualization class.
    
    This class handles the creation of comprehensive cluster visualizations
    including interactive maps, statistical plots, and detailed analysis.
    """
    
    def __init__(self, clustering_type: str = DEFAULT_CLUSTERING_TYPE) -> None:
        """
        Initialize the cluster map visualizer.
        
        Args:
            clustering_type (str): Type of clustering analysis to visualize
        """
        if clustering_type not in CLUSTERING_TYPES:
            raise ValueError(f"Clustering type must be one of {CLUSTERING_TYPES}")
        
        self.clustering_type: str = clustering_type
        self.cluster_data: Optional[pd.DataFrame] = None
        self.coordinates_data: Optional[pd.DataFrame] = None
        self.temperature_data: Optional[pd.DataFrame] = None
        self.merged_data: Optional[pd.DataFrame] = None
        
        # Setup logging
        self._setup_logging()
        
        print(f"[INIT] Cluster Map Visualizer initialized for {clustering_type} clustering")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(OUTPUT_DIR, 'cluster_visualization.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _log_progress(self, message: str) -> None:
        """
        Log progress to console and file with timestamp.
        
        Args:
            message (str): Progress message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        self.logger.info(message)
    
    def load_data(self) -> None:
        """
        Load all required data for visualization.
        
        This method loads clustering results, store coordinates, and optional
        temperature data for comprehensive visualization.
        """
        self._log_progress(f"Loading data for {self.clustering_type} clustering visualization...")
        
        # Load clustering results
        cluster_file = os.path.join(OUTPUT_DIR, f"clustering_results_{self.clustering_type}.csv")
        if not os.path.exists(cluster_file):
            # Try backup file without clustering type suffix
            cluster_file = os.path.join(OUTPUT_DIR, "clustering_results.csv")
        
        if os.path.exists(cluster_file):
            self.cluster_data = pd.read_csv(cluster_file, dtype={'str_code': str})
            self._log_progress(f"Loaded clustering results: {len(self.cluster_data)} stores")
        else:
            raise FileNotFoundError(f"Clustering results file not found: {cluster_file}")
        
        # Load store coordinates
        coordinates_file = os.path.join(DATA_DIR, "store_coordinates_extended.csv")
        if os.path.exists(coordinates_file):
            self.coordinates_data = pd.read_csv(coordinates_file, dtype={'str_code': str})
            self._log_progress(f"Loaded coordinates: {len(self.coordinates_data)} stores")
        else:
            raise FileNotFoundError(f"Coordinates file not found: {coordinates_file}")
        
        # Load temperature data if available
        temperature_file = os.path.join(OUTPUT_DIR, "stores_with_feels_like_temperature.csv")
        if os.path.exists(temperature_file):
            try:
                self.temperature_data = pd.read_csv(temperature_file, dtype={'store_code': str})
                self.temperature_data.rename(columns={'store_code': 'str_code'}, inplace=True)
                self._log_progress(f"Loaded temperature data: {len(self.temperature_data)} stores")
            except Exception as e:
                self._log_progress(f"Warning: Could not load temperature data: {str(e)}")
                self.temperature_data = None
        else:
            self._log_progress("Temperature data not available")
            self.temperature_data = None
        
        # Merge all data
        self._merge_data()
    
    def _merge_data(self) -> None:
        """Merge all loaded data into a single DataFrame."""
        self._log_progress("Merging data sources...")
        
        # Start with cluster data
        self.merged_data = self.cluster_data.copy()
        
        # Merge with coordinates
        self.merged_data = self.merged_data.merge(
            self.coordinates_data, 
            on='str_code', 
            how='inner'
        )
        
        # Merge with temperature data if available
        if self.temperature_data is not None:
            self.merged_data = self.merged_data.merge(
                self.temperature_data, 
                on='str_code', 
                how='left'
            )
        
        # Remove stores without coordinates
        initial_count = len(self.merged_data)
        self.merged_data = self.merged_data.dropna(subset=['latitude', 'longitude'])
        final_count = len(self.merged_data)
        
        if initial_count > final_count:
            self._log_progress(f"Removed {initial_count - final_count} stores without coordinates")
        
        self._log_progress(f"Final dataset: {final_count} stores with complete data")
    
    def analyze_clusters(self) -> Dict[str, Union[int, float, List]]:
        """
        Perform comprehensive cluster analysis.
        
        Returns:
            Dict containing cluster statistics and metrics
        """
        self._log_progress("Performing cluster analysis...")
        
        if self.merged_data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        n_clusters = self.merged_data['Cluster'].nunique()
        cluster_sizes = self.merged_data['Cluster'].value_counts().sort_index()
        
        analysis = {
            'n_clusters': n_clusters,
            'total_stores': len(self.merged_data),
            'cluster_sizes': cluster_sizes.tolist(),
            'min_cluster_size': cluster_sizes.min(),
            'max_cluster_size': cluster_sizes.max(),
            'avg_cluster_size': cluster_sizes.mean(),
            'std_cluster_size': cluster_sizes.std(),
        }
        
        # Geographic analysis
        if 'latitude' in self.merged_data.columns and 'longitude' in self.merged_data.columns:
            analysis.update({
                'center_lat': self.merged_data['latitude'].mean(),
                'center_lng': self.merged_data['longitude'].mean(),
                'lat_range': self.merged_data['latitude'].max() - self.merged_data['latitude'].min(),
                'lng_range': self.merged_data['longitude'].max() - self.merged_data['longitude'].min(),
            })
        
        # Temperature analysis if available
        if self.temperature_data is not None and 'feels_like_temperature' in self.merged_data.columns:
            temp_by_cluster = self.merged_data.groupby('Cluster')['feels_like_temperature'].agg([
                'mean', 'std', 'min', 'max'
            ]).round(2)
            analysis['temperature_by_cluster'] = temp_by_cluster.to_dict()
        
        self._log_progress(f"Analysis complete: {n_clusters} clusters, {analysis['total_stores']} stores")
        
        return analysis
    
    def create_interactive_map(self, analysis: Dict) -> folium.Map:
        """
        Create an interactive Folium map with cluster navigation controls.
        
        Args:
            analysis (Dict): Cluster analysis results
            
        Returns:
            folium.Map: Interactive map object with navigation controls
        """
        self._log_progress("Creating interactive cluster map with navigation controls...")
        
        # Determine map center
        center_lat = analysis.get('center_lat', DEFAULT_MAP_CENTER[0])
        center_lng = analysis.get('center_lng', DEFAULT_MAP_CENTER[1])
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=DEFAULT_ZOOM,
            tiles='OpenStreetMap'
        )
        
        # Add additional tile layers
        folium.TileLayer('cartodbpositron', name='CartoDB Positron').add_to(m)
        folium.TileLayer('cartodbdark_matter', name='CartoDB Dark').add_to(m)
        
        # Generate colors for clusters
        n_clusters = analysis['n_clusters']
        colors = self._generate_cluster_colors(n_clusters)
        
        # Prepare data for JavaScript
        markers_data = []
        cluster_centers = {}
        
        # Create markers and collect data
        for idx, row in self.merged_data.iterrows():
            cluster_id = int(row['Cluster'])
            popup_content = self._create_popup_content(row)
            
            # Store marker data for JavaScript (convert to native Python types)
            # Note: We don't add Folium markers to avoid duplication with JavaScript markers
            markers_data.append({
                'lat': float(row['latitude']),
                'lng': float(row['longitude']),
                'cluster': int(cluster_id),
                'store_code': str(row['str_code']),
                'color': str(colors[cluster_id]),
                'popup_content': popup_content
            })
        
        # Calculate cluster centers (convert to native Python types)
        for cluster_id in range(n_clusters):
            cluster_stores = self.merged_data[self.merged_data['Cluster'] == cluster_id]
            cluster_centers[cluster_id] = {
                'lat': float(cluster_stores['latitude'].mean()),
                'lng': float(cluster_stores['longitude'].mean()),
                'size': int(len(cluster_stores)),
                'color': str(colors[cluster_id])
            }
        
        # Add enhanced navigation controls with embedded data
        self._add_enhanced_navigation_controls(m, markers_data, cluster_centers, analysis)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        self._log_progress("Interactive map with navigation created successfully")
        
        return m
    
    def _generate_cluster_colors(self, n_clusters: int) -> List[str]:
        """
        Generate distinct colors for clusters.
        
        Args:
            n_clusters (int): Number of clusters
            
        Returns:
            List[str]: List of color codes
        """
        # Base color palette
        base_colors = [
            '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#e67e22', '#34495e', '#f1c40f', '#e91e63',
            '#8e44ad', '#16a085', '#27ae60', '#2980b9', '#c0392b',
            '#d35400', '#7f8c8d', '#95a5a6', '#bdc3c7', '#ecf0f1'
        ]
        
        # Extend colors if needed
        colors = base_colors * ((n_clusters // len(base_colors)) + 1)
        
        return colors[:n_clusters]
    
    def _create_popup_content(self, row: pd.Series) -> str:
        """
        Create HTML popup content for store markers.
        
        Args:
            row (pd.Series): Store data row
            
        Returns:
            str: HTML popup content
        """
        content = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="margin: 0; color: #2c3e50;">🏪 Store {row['str_code']}</h4>
            <hr style="margin: 5px 0;">
            <p><strong>Cluster:</strong> {int(row['Cluster'])}</p>
            <p><strong>Location:</strong> {row['latitude']:.4f}, {row['longitude']:.4f}</p>
        """
        
        # Add temperature info if available
        if 'feels_like_temperature' in row and pd.notna(row['feels_like_temperature']):
            content += f"<p><strong>Temperature:</strong> {row['feels_like_temperature']:.1f}°F</p>"
        
        # Add any additional store information
        if 'store_name' in row:
            content += f"<p><strong>Name:</strong> {row['store_name']}</p>"
        
        content += "</div>"
        
        return content
    
    def _add_enhanced_navigation_controls(self, map_obj: folium.Map, markers_data: List[Dict], 
                                        cluster_centers: Dict, analysis: Dict) -> None:
        """
        Add working navigation controls using embedded JavaScript data.
        
        Args:
            map_obj (folium.Map): Map object to add controls to
            markers_data (List[Dict]): All marker data
            cluster_centers (Dict): Cluster center information
            analysis (Dict): Overall analysis data
        """
        
        # Create the navigation HTML and JavaScript
        navigation_html = f"""
        <div id="cluster-navigator" style="position: fixed; top: 10px; right: 10px; z-index: 9999; 
             background: white; border: 2px solid #333; border-radius: 8px; padding: 15px; 
             font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.3); min-width: 280px;">
            
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 10px;">
                <h3 style="margin: 0; color: #2c3e50;">{self.clustering_type.title()} Clusters</h3>
                <p style="margin: 5px 0; font-size: 12px; color: #666;">
                    {analysis['total_stores']} stores in {analysis['n_clusters']} clusters
                </p>
            </div>
            
            <!-- Current Cluster Display -->
            <div style="text-align: center; margin-bottom: 15px; padding: 10px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; border-radius: 5px;">
                <div id="current-cluster-info">
                    <h4 style="margin: 0;">All Clusters Visible</h4>
                    <p style="margin: 0; font-size: 12px;">Click navigation to focus on individual clusters</p>
                </div>
            </div>
            
            <!-- Navigation Controls -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <button id="prev-cluster" onclick="ClusterNavigator.navigateCluster(-1)" 
                        style="background: #3498db; color: white; border: none; padding: 8px 12px; 
                               border-radius: 4px; cursor: pointer; font-size: 14px;">
                    ← Previous
                </button>
                
                <select id="cluster-selector" onchange="ClusterNavigator.jumpToCluster(this.value)"
                        style="padding: 6px; border-radius: 4px; border: 1px solid #ddd; font-size: 14px;">
                    <option value="all">All Clusters</option>
                    {chr(10).join([f'<option value="{i}">Cluster {i}</option>' for i in range(analysis['n_clusters'])])}
                </select>
                
                <button id="next-cluster" onclick="ClusterNavigator.navigateCluster(1)"
                        style="background: #3498db; color: white; border: none; padding: 8px 12px; 
                               border-radius: 4px; cursor: pointer; font-size: 14px;">
                    Next →
                </button>
            </div>
            
            <!-- View Controls -->
            <div style="text-align: center; margin-bottom: 10px;">
                <button id="show-all" onclick="ClusterNavigator.showAllClusters()"
                        style="background: #27ae60; color: white; border: none; padding: 6px 12px; 
                               border-radius: 4px; cursor: pointer; font-size: 12px; margin-right: 5px;">
                    Show All
                </button>
                <button id="zoom-to-cluster" onclick="ClusterNavigator.zoomToCurrentCluster()"
                        style="background: #e67e22; color: white; border: none; padding: 6px 12px; 
                               border-radius: 4px; cursor: pointer; font-size: 12px;">
                    Zoom to Cluster
                </button>
            </div>
            
            <!-- Statistics -->
            <div style="font-size: 11px; color: #666; border-top: 1px solid #ddd; padding-top: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <span>Avg Size: {analysis['avg_cluster_size']:.1f}</span>
                    <span>Range: {analysis['min_cluster_size']}-{analysis['max_cluster_size']}</span>
                </div>
            </div>
        </div>

        <script>
            // Create ClusterNavigator object to avoid global namespace pollution
            window.ClusterNavigator = (function() {{
                // Embedded marker and cluster data (properly serialized)
                const markersData = {json.dumps(markers_data)};
                const clusterCenters = {json.dumps(cluster_centers)};
                
                // Navigation state
                let currentCluster = 'all';
                let totalClusters = {analysis['n_clusters']};
                let map = null;
                let allMarkers = [];
                let isInitialized = false;
                
                // Initialize function
                function initialize() {{
                    if (isInitialized) return;
                    
                    console.log('[ClusterNavigator] Starting initialization...');
                    
                    // Try multiple methods to find the map instance
                    map = findMapInstance();
                    
                    if (!map) {{
                        console.error('[ClusterNavigator] Could not find map instance, retrying...');
                        setTimeout(initialize, 1000); // Retry after 1 second
                        return;
                    }}
                    
                    console.log('[ClusterNavigator] Map instance found, creating markers...');
                    
                    // Create markers programmatically (but don't add to map initially)
                    try {{
                        markersData.forEach(function(markerData, index) {{
                            const marker = L.circleMarker([markerData.lat, markerData.lng], {{
                                radius: 8,
                                color: 'white',
                                weight: 2,
                                fillColor: markerData.color,
                                fillOpacity: 0.8,
                                clusterId: markerData.cluster
                            }});
                            
                            // Add popup and tooltip
                            marker.bindTooltip(`Store ${{markerData.store_code}} (Cluster ${{markerData.cluster}})`);
                            if (markerData.popup_content) {{
                                marker.bindPopup(markerData.popup_content, {{maxWidth: 300}});
                            }}
                            
                            allMarkers.push(marker);
                            
                            if (index % 500 === 0) {{
                                console.log(`[ClusterNavigator] Created ${{index + 1}} markers...`);
                            }}
                        }});
                        
                        console.log(`[ClusterNavigator] Successfully created ${{allMarkers.length}} interactive markers`);
                        
                        // Initialize display - show all clusters initially
                        showCluster('all');
                        updateClusterInfo('all');
                        isInitialized = true;
                        
                        console.log('[ClusterNavigator] Initialization complete!');
                        
                    }} catch (error) {{
                        console.error('[ClusterNavigator] Error creating markers:', error);
                        setTimeout(initialize, 2000); // Retry after 2 seconds
                    }}
                }}
                
                // Enhanced map finding function
                function findMapInstance() {{
                    // Method 1: Try window map variables
                    for (const key in window) {{
                        if (key.startsWith('map_') && window[key] && window[key].getContainer) {{
                            console.log(`[ClusterNavigator] Found map via window.${{key}}`);
                            return window[key];
                        }}
                    }}
                    
                    // Method 2: Try Leaflet map registry
                    if (window.L && window.L.Map && window.L.Map._mapList) {{
                        const maps = window.L.Map._mapList;
                        if (maps.length > 0) {{
                            console.log('[ClusterNavigator] Found map via Leaflet registry');
                            return maps[0];
                        }}
                    }}
                    
                    // Method 3: Try DOM-based search
                    const mapElements = document.querySelectorAll('.leaflet-container');
                    if (mapElements.length > 0) {{
                        const mapId = mapElements[0].id;
                        if (window[mapId]) {{
                            console.log(`[ClusterNavigator] Found map via DOM search: ${{mapId}}`);
                            return window[mapId];
                        }}
                    }}
                    
                    return null;
                }}
                
                // Update cluster info display
                function updateClusterInfo(clusterId) {{
                    const infoDiv = document.getElementById('current-cluster-info');
                    const selector = document.getElementById('cluster-selector');
                    
                    if (!infoDiv || !selector) {{
                        console.warn('[ClusterNavigator] Info elements not found');
                        return;
                    }}
                    
                    if (clusterId === 'all') {{
                        infoDiv.innerHTML = `
                            <h4 style="margin: 0;">All Clusters Visible</h4>
                            <p style="margin: 0; font-size: 12px;">Total: {analysis['total_stores']} stores across {analysis['n_clusters']} clusters</p>
                        `;
                        selector.value = 'all';
                    }} else {{
                        const cluster = clusterCenters[clusterId];
                        if (cluster) {{
                            infoDiv.innerHTML = `
                                <h4 style="margin: 0;">Cluster ${{clusterId}}</h4>
                                <p style="margin: 0; font-size: 12px;">${{cluster.size}} stores • <span style="color: ${{cluster.color}};">●</span> ${{cluster.color}}</p>
                            `;
                            selector.value = clusterId;
                        }}
                    }}
                }}
                
                // Show cluster function
                function showCluster(clusterId) {{
                    if (!map || !isInitialized) {{
                        console.warn('[ClusterNavigator] Map not ready, cannot show cluster');
                        return;
                    }}
                    
                    console.log(`[ClusterNavigator] Showing cluster: ${{clusterId}}`);
                    
                    // Remove all existing markers
                    allMarkers.forEach(marker => {{
                        try {{
                            map.removeLayer(marker);
                        }} catch (e) {{
                            // Ignore errors for markers already removed
                        }}
                    }});
                    
                    let visibleCount = 0;
                    
                    if (clusterId === 'all') {{
                        // Show all markers
                        allMarkers.forEach(marker => {{
                            try {{
                                map.addLayer(marker);
                                visibleCount++;
                            }} catch (e) {{
                                console.warn('[ClusterNavigator] Error adding marker:', e);
                            }}
                        }});
                    }} else {{
                        // Show only markers for selected cluster
                        allMarkers.forEach(marker => {{
                            if (marker.options.clusterId == clusterId) {{
                                try {{
                                    map.addLayer(marker);
                                    visibleCount++;
                                }} catch (e) {{
                                    console.warn('[ClusterNavigator] Error adding cluster marker:', e);
                                }}
                            }}
                        }});
                    }}
                    
                    currentCluster = clusterId;
                    updateClusterInfo(clusterId);
                    console.log(`[ClusterNavigator] Showing ${{visibleCount}} markers for cluster ${{clusterId}}`);
                }}
                
                // Navigation function
                function navigateCluster(direction) {{
                    if (!isInitialized) {{
                        console.warn('[ClusterNavigator] Not initialized, cannot navigate');
                        return;
                    }}
                    
                    console.log(`[ClusterNavigator] Navigating ${{direction > 0 ? 'forward' : 'backward'}}`);
                    
                    if (currentCluster === 'all') {{
                        currentCluster = direction > 0 ? 0 : totalClusters - 1;
                    }} else {{
                        currentCluster = parseInt(currentCluster) + direction;
                        if (currentCluster >= totalClusters) currentCluster = 0;
                        if (currentCluster < 0) currentCluster = totalClusters - 1;
                    }}
                    
                    showCluster(currentCluster);
                }}
                
                // Jump to cluster function
                function jumpToCluster(clusterId) {{
                    if (!isInitialized) {{
                        console.warn('[ClusterNavigator] Not initialized, cannot jump to cluster');
                        return;
                    }}
                    
                    console.log(`[ClusterNavigator] Jumping to cluster: ${{clusterId}}`);
                    showCluster(clusterId);
                }}
                
                // Show all clusters function
                function showAllClusters() {{
                    if (!isInitialized) {{
                        console.warn('[ClusterNavigator] Not initialized, cannot show all clusters');
                        return;
                    }}
                    
                    console.log('[ClusterNavigator] Showing all clusters');
                    showCluster('all');
                }}
                
                // Zoom to current cluster function
                function zoomToCurrentCluster() {{
                    if (!map || !isInitialized) {{
                        console.warn('[ClusterNavigator] Map not ready, cannot zoom');
                        return;
                    }}
                    
                    console.log(`[ClusterNavigator] Zooming to cluster: ${{currentCluster}}`);
                    
                    if (currentCluster !== 'all' && clusterCenters[currentCluster]) {{
                        const cluster = clusterCenters[currentCluster];
                        map.setView([cluster.lat, cluster.lng], 8);
                    }} else {{
                        map.setView([{analysis.get('center_lat', DEFAULT_MAP_CENTER[0])}, {analysis.get('center_lng', DEFAULT_MAP_CENTER[1])}], {DEFAULT_ZOOM});
                    }}
                }}
                
                // Start initialization with multiple attempts
                function startInitialization() {{
                    console.log('[ClusterNavigator] Starting initialization sequence...');
                    
                    // Try immediate initialization
                    setTimeout(initialize, 500);
                    
                    // Backup initialization attempts
                    setTimeout(initialize, 2000);
                    setTimeout(initialize, 5000);
                    
                    // Last resort initialization
                    setTimeout(function() {{
                        if (!isInitialized) {{
                            console.warn('[ClusterNavigator] Final initialization attempt...');
                            initialize();
                        }}
                    }}, 10000);
                }}
                
                // Public API
                return {{
                    navigateCluster: navigateCluster,
                    jumpToCluster: jumpToCluster,
                    showAllClusters: showAllClusters,
                    zoomToCurrentCluster: zoomToCurrentCluster,
                    isInitialized: () => isInitialized,
                    initialize: startInitialization
                }};
            }})();
            
            // Start initialization when DOM is ready
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', ClusterNavigator.initialize);
            }} else {{
                ClusterNavigator.initialize();
            }}
            
            console.log('[ClusterNavigator] Script loaded successfully');
        </script>
        """
        
        map_obj.get_root().html.add_child(folium.Element(navigation_html))
    
    def create_statistical_plots(self, analysis: Dict) -> go.Figure:
        """
        Create comprehensive statistical plots for cluster analysis.
        
        Args:
            analysis (Dict): Cluster analysis results
            
        Returns:
            go.Figure: Plotly figure with multiple subplots
        """
        self._log_progress("Creating statistical plots...")
        
        # Determine if temperature data is available and usable
        has_temperature = (self.temperature_data is not None and 
                          'feels_like_temperature' in self.merged_data.columns and 
                          not self.merged_data['feels_like_temperature'].isna().all())
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Cluster Size Distribution',
                'Geographic Distribution',
                'Cluster Statistics',
                'Temperature Distribution' if has_temperature else 'Store Distribution'
            ),
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "box"}, {"type": "histogram"}]]
        )
        
        # Plot 1: Cluster size distribution
        cluster_counts = self.merged_data['Cluster'].value_counts().sort_index()
        fig.add_trace(
            go.Bar(
                x=cluster_counts.index,
                y=cluster_counts.values,
                name='Store Count',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        # Plot 2: Geographic distribution
        fig.add_trace(
            go.Scatter(
                x=self.merged_data['longitude'],
                y=self.merged_data['latitude'],
                mode='markers',
                marker=dict(
                    color=self.merged_data['Cluster'],
                    colorscale='Viridis',
                    size=8,
                    opacity=0.6
                ),
                text=self.merged_data['str_code'],
                name='Stores'
            ),
            row=1, col=2
        )
        
        # Plot 3: Cluster statistics (box plot of cluster sizes)
        cluster_size_data = []
        for cluster_id in sorted(self.merged_data['Cluster'].unique()):
            cluster_stores = self.merged_data[self.merged_data['Cluster'] == cluster_id]
            cluster_size_data.extend([len(cluster_stores)] * len(cluster_stores))
        
        fig.add_trace(
            go.Box(
                y=cluster_size_data,
                name='Cluster Sizes',
                marker_color='lightgreen'
            ),
            row=2, col=1
        )
        
        # Plot 4: Temperature distribution or store distribution
        if has_temperature:
            fig.add_trace(
                go.Histogram(
                    x=self.merged_data['feels_like_temperature'].dropna(),
                    name='Temperature',
                    marker_color='orange'
                ),
                row=2, col=2
            )
        else:
            # Alternative: Show distribution of stores by cluster
            fig.add_trace(
                go.Histogram(
                    x=self.merged_data['Cluster'],
                    name='Stores per Cluster',
                    marker_color='purple'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text=f"{self.clustering_type.title()} Clustering Analysis Dashboard",
            showlegend=False,
            height=800
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Cluster ID", row=1, col=1)
        fig.update_yaxes(title_text="Number of Stores", row=1, col=1)
        
        fig.update_xaxes(title_text="Longitude", row=1, col=2)
        fig.update_yaxes(title_text="Latitude", row=1, col=2)
        
        fig.update_yaxes(title_text="Cluster Size", row=2, col=1)
        
        if has_temperature:
            fig.update_xaxes(title_text="Temperature (°F)", row=2, col=2)
            fig.update_yaxes(title_text="Frequency", row=2, col=2)
        else:
            fig.update_xaxes(title_text="Cluster ID", row=2, col=2)
            fig.update_yaxes(title_text="Frequency", row=2, col=2)
        
        self._log_progress("Statistical plots created successfully")
        
        return fig
    
    def export_results(self, map_obj: folium.Map, plots_fig: go.Figure, analysis: Dict) -> Dict[str, str]:
        """
        Export all visualization results to files.
        
        Args:
            map_obj (folium.Map): Interactive map object
            plots_fig (go.Figure): Statistical plots figure
            analysis (Dict): Cluster analysis results
            
        Returns:
            Dict[str, str]: Dictionary of output file paths
        """
        self._log_progress("Exporting visualization results...")
        
        output_files = {}
        
        # Export interactive map
        map_file = os.path.join(VIZ_OUTPUT_DIR, f"cluster_map_{self.clustering_type}.html")
        map_obj.save(map_file)
        output_files['interactive_map'] = map_file
        
        # Export statistical plots
        plots_file = os.path.join(VIZ_OUTPUT_DIR, f"cluster_plots_{self.clustering_type}.html")
        plots_fig.write_html(plots_file)
        output_files['statistical_plots'] = plots_file
        
        # Export static plots (with fallback)
        static_plots_file = os.path.join(VIZ_OUTPUT_DIR, f"cluster_plots_{self.clustering_type}.png")
        try:
            plots_fig.write_image(static_plots_file, width=1200, height=800)
            output_files['static_plots'] = static_plots_file
        except Exception as e:
            self._log_progress(f"Warning: Could not export PNG (kaleido may not be installed): {e}")
            output_files['static_plots'] = "Not generated - install kaleido for PNG export"
        
        # Export analysis summary
        summary_file = os.path.join(VIZ_OUTPUT_DIR, f"cluster_analysis_{self.clustering_type}.csv")
        summary_df = pd.DataFrame([analysis])
        summary_df.to_csv(summary_file, index=False)
        output_files['analysis_summary'] = summary_file
        
        # Export detailed cluster data
        detailed_file = os.path.join(VIZ_OUTPUT_DIR, f"cluster_detailed_data_{self.clustering_type}.csv")
        self.merged_data.to_csv(detailed_file, index=False)
        output_files['detailed_data'] = detailed_file
        
        self._log_progress(f"All results exported to {VIZ_OUTPUT_DIR}")
        
        return output_files
    
    def create_comprehensive_report(self, analysis: Dict, output_files: Dict[str, str]) -> None:
        """
        Create a comprehensive markdown report.
        
        Args:
            analysis (Dict): Cluster analysis results
            output_files (Dict): Paths to output files
        """
        self._log_progress("Creating comprehensive report...")
        
        report_content = f"""# {self.clustering_type.title()} Clustering Visualization Report

## Executive Summary

This report presents a comprehensive visualization analysis of the {self.clustering_type} clustering results.

### Key Metrics
- **Total Stores Analyzed**: {analysis['total_stores']:,}
- **Number of Clusters**: {analysis['n_clusters']}
- **Average Cluster Size**: {analysis['avg_cluster_size']:.1f}
- **Cluster Size Range**: {analysis['min_cluster_size']} - {analysis['max_cluster_size']}
- **Geographic Coverage**: {analysis.get('lat_range', 'N/A'):.2f}° latitude × {analysis.get('lng_range', 'N/A'):.2f}° longitude

## Clustering Quality Assessment

### Size Distribution
- **Standard Deviation**: {analysis['std_cluster_size']:.2f}
- **Coefficient of Variation**: {(analysis['std_cluster_size'] / analysis['avg_cluster_size'] * 100):.1f}%

### Geographic Analysis
- **Map Center**: ({analysis.get('center_lat', 'N/A'):.4f}, {analysis.get('center_lng', 'N/A'):.4f})

## Output Files Generated

1. **Interactive Map**: [`{os.path.basename(output_files['interactive_map'])}`]({output_files['interactive_map']})
   - Full interactive cluster visualization
   - Store-level popup information
   - Multiple map layers and controls

2. **Statistical Dashboard**: [`{os.path.basename(output_files['statistical_plots'])}`]({output_files['statistical_plots']})
   - Comprehensive statistical analysis
   - Interactive plots and visualizations

3. **Static Plots**: [`{os.path.basename(output_files['static_plots'])}`]({output_files['static_plots']})
   - High-resolution static images
   - Suitable for reports and presentations

4. **Detailed Data**: [`{os.path.basename(output_files['detailed_data'])}`]({output_files['detailed_data']})
   - Complete merged dataset
   - Store coordinates and cluster assignments

## Methodology

This visualization was created using the following approach:

1. **Data Integration**: Merged clustering results with store coordinates and optional temperature data
2. **Quality Assessment**: Analyzed cluster size distribution and geographic spread
3. **Interactive Visualization**: Created Folium-based maps with detailed popups
4. **Statistical Analysis**: Generated comprehensive plots using Plotly
5. **Export Pipeline**: Produced multiple output formats for different use cases

## Usage Recommendations

### For Strategic Planning
- Use the interactive map to identify geographic clustering patterns
- Analyze the statistical dashboard for cluster quality metrics
- Review cluster size distribution for operational planning

### For Operational Implementation
- Reference the detailed data export for store-level decisions
- Use static plots for presentations and documentation
- Leverage geographic insights for logistics optimization

## Technical Details

- **Clustering Type**: {self.clustering_type}
- **Visualization Libraries**: Folium, Plotly
- **Export Formats**: HTML (interactive), PNG (static), CSV (data)
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

*This report was automatically generated by the Cluster Map Visualization Tool.*
"""
        
        # Add temperature analysis if available
        if 'temperature_by_cluster' in analysis:
            report_content += f"""

## Temperature Analysis

Temperature data was available and incorporated into the analysis:

### Cluster Temperature Summary
"""
            temp_data = analysis['temperature_by_cluster']
            for metric in ['mean', 'std', 'min', 'max']:
                if metric in temp_data:
                    report_content += f"- **{metric.title()} by Cluster**: "
                    values = [f"C{i}: {temp_data[metric][i]:.1f}°F" for i in sorted(temp_data[metric].keys())]
                    report_content += ", ".join(values[:5])  # Show first 5 clusters
                    if len(values) > 5:
                        report_content += f" ... (+{len(values)-5} more)"
                    report_content += "\n"
        
        # Save report
        report_file = os.path.join(VIZ_OUTPUT_DIR, f"cluster_visualization_report_{self.clustering_type}.md")
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self._log_progress(f"Comprehensive report saved to {report_file}")
    
    def run_full_analysis(self) -> Dict[str, str]:
        """
        Run the complete cluster visualization pipeline.
        
        Returns:
            Dict[str, str]: Dictionary of output file paths
        """
        self._log_progress(f"Starting comprehensive cluster visualization for {self.clustering_type}")
        
        # Load data
        self.load_data()
        
        # Analyze clusters
        analysis = self.analyze_clusters()
        
        # Create visualizations
        map_obj = self.create_interactive_map(analysis)
        plots_fig = self.create_statistical_plots(analysis)
        
        # Export results
        output_files = self.export_results(map_obj, plots_fig, analysis)
        
        # Create comprehensive report
        self.create_comprehensive_report(analysis, output_files)
        
        self._log_progress("Cluster visualization pipeline completed successfully!")
        
        return output_files


def main() -> None:
    """
    Main function to run cluster map visualization.
    
    This function can be modified to run visualization for specific clustering types
    or to process multiple clustering types in sequence.
    """
    print("=" * 80)
    print("ADVANCED CLUSTER MAP VISUALIZATION TOOL")
    print("=" * 80)
    
    # Available clustering types to process
    clustering_types_to_process = [
        "subcategory",
        "spu", 
        "category_agg"
    ]
    
    all_results = {}
    
    for clustering_type in clustering_types_to_process:
        try:
            print(f"\n{'-' * 60}")
            print(f"Processing {clustering_type.upper()} clustering visualization...")
            print(f"{'-' * 60}")
            
            # Create visualizer
            visualizer = ClusterMapVisualizer(clustering_type)
            
            # Run full analysis
            output_files = visualizer.run_full_analysis()
            
            # Store results
            all_results[clustering_type] = output_files
            
            print(f"\n✅ {clustering_type.title()} visualization completed successfully!")
            print(f"   Interactive Map: {output_files['interactive_map']}")
            print(f"   Statistical Plots: {output_files['statistical_plots']}")
            
        except FileNotFoundError as e:
            print(f"\n⚠️  Skipping {clustering_type} - Required files not found: {e}")
            continue
        except Exception as e:
            print(f"\n❌ Error processing {clustering_type}: {e}")
            continue
    
    # Summary
    print(f"\n{'=' * 80}")
    print("VISUALIZATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Successfully processed {len(all_results)} clustering types:")
    
    for clustering_type, files in all_results.items():
        print(f"  • {clustering_type.title()}: {len(files)} output files")
    
    print(f"\nAll outputs saved to: {VIZ_OUTPUT_DIR}")
    print("View the interactive maps in your web browser!")


if __name__ == "__main__":
    main()
