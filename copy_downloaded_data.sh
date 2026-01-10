#!/bin/bash
# Copy downloaded data from other branches to avoid re-downloading

set -e

echo "🔄 Copying downloaded data from other branches..."
echo ""

# Source directories
API_DATA_SOURCE="$HOME/Desktop/Dev/ais-129-issues-found-when-running-main/data/api_data"
WEATHER_DATA_SOURCE="$HOME/Desktop/Dev/ais-96-step36-fast-compliance/data/weather_data"

# Target directories
API_DATA_TARGET="./data/api_data"
WEATHER_DATA_TARGET="./data/weather_data"

# Create target directories if they don't exist
mkdir -p "$API_DATA_TARGET"
mkdir -p "$WEATHER_DATA_TARGET"

# Copy API data (Step 1 output)
echo "📥 Copying API data (Step 1 output)..."
if [ -d "$API_DATA_SOURCE" ]; then
    cp -v "$API_DATA_SOURCE"/*.csv "$API_DATA_TARGET/" 2>/dev/null || echo "  ⚠️  Some files may already exist"
    echo "  ✅ API data copied"
else
    echo "  ❌ Source not found: $API_DATA_SOURCE"
    exit 1
fi

echo ""

# Copy weather data (Step 4 output)
echo "📥 Copying weather data (Step 4 output)..."
if [ -d "$WEATHER_DATA_SOURCE" ]; then
    # Only copy CSV files, not quarantine directories
    cp -v "$WEATHER_DATA_SOURCE"/*.csv "$WEATHER_DATA_TARGET/" 2>/dev/null || echo "  ⚠️  Some files may already exist"
    echo "  ✅ Weather data copied"
else
    echo "  ❌ Source not found: $WEATHER_DATA_SOURCE"
    exit 1
fi

echo ""
echo "✅ All downloaded data copied successfully!"
echo ""
echo "📊 Summary:"
echo "  API data files: $(ls -1 $API_DATA_TARGET/*.csv 2>/dev/null | wc -l)"
echo "  Weather data files: $(ls -1 $WEATHER_DATA_TARGET/*.csv 2>/dev/null | wc -l)"
echo ""
echo "🎯 Next steps:"
echo "  1. Run legacy steps 2, 3, 5, 6"
echo "  2. Run legacy step 7 and backup results"
echo "  3. Run refactored step 7"
echo "  4. Compare results"
