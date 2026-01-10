#!/usr/bin/env bash
set -euo pipefail

# Configuration
YYYYMM=${1:-202508}
HALF=${2:-A}
PERIOD_LABEL="${YYYYMM}${HALF}"
ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

log() { printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# 0) Python environment
if [ ! -d .venv ]; then
  log "Creating virtualenv .venv"
  python3 -m venv .venv
fi
. .venv/bin/activate
pip -q install -U pip >/dev/null
if [ -f requirements-dev.txt ]; then
  log "Installing requirements-dev.txt"
  pip -q install -r requirements-dev.txt >/dev/null || true
fi
if [ -f requirements.txt ]; then
  log "Installing requirements.txt"
  pip -q install -r requirements.txt >/dev/null
else
  log "Installing minimal deps (numpy, pandas, openpyxl, pytest)"
  pip -q install numpy pandas openpyxl pytest >/dev/null
fi

# 1) Backup existing deterministic inputs Step 36 resolves by exact name
bk="output/backup_step36_fixtures_$(date +%s)"
mkdir -p "$bk"
backup_if_exists() {
  local f="$1"
  if [ -f "$f" ]; then
    log "Backing up $f -> $bk/"
    mv "$f" "$bk/"
  fi
}
backup_if_exists "output/fast_fish_with_sell_through_analysis_${PERIOD_LABEL}.csv"
backup_if_exists "output/store_tags_${PERIOD_LABEL}.csv"
backup_if_exists "output/enriched_store_attributes.csv"

# 2) Inject fixtures
mkdir -p output
log "Writing fixture: fast_fish_with_sell_through_analysis_${PERIOD_LABEL}.csv"
cat > "output/fast_fish_with_sell_through_analysis_${PERIOD_LABEL}.csv" << 'CSV'
Store_Group_Name,Target_Style_Tags,Category,Subcategory,ΔQty,Current_SPU_Quantity,Target_SPU_Quantity,Season,Gender,Location
Group 1,"[Summer, Women, Back, T恤, 合体圆领T恤, 夏, 女, 后台]",T恤,合体圆领T恤,5,10,15,Summer,Women,Back
CSV

log "Writing fixture: store_level_allocation_results_${PERIOD_LABEL}_zzfixture.csv"
cat > "output/store_level_allocation_results_${PERIOD_LABEL}_zzfixture.csv" << 'CSV'
Store_Code,Store_Group_Name,Target_Style_Tags,Category,Subcategory,Allocated_ΔQty,Allocated_ΔQty_Rounded
11017,Group 1,"[Summer, Women, Back, T恤, 合体圆领T恤, 夏, 女, 后台]",T恤,合体圆领T恤,5.0,5
CSV

log "Writing fixture: store_tags_${PERIOD_LABEL}.csv"
cat > "output/store_tags_${PERIOD_LABEL}.csv" << 'CSV'
str_code,temperature_band,feels_like_temperature
11017,15°C to 20°C,16.0
CSV

log "Writing fixture: enriched_store_attributes.csv"
cat > output/enriched_store_attributes.csv << 'CSV'
str_code,temperature_band,feels_like_temperature
11017,15°C to 20°C,16.0
CSV

# 3) Run Step 36
log "Running Step 36 for ${PERIOD_LABEL}"
export STEP36_OVERRIDE_STEP18="output/fast_fish_with_sell_through_analysis_${PERIOD_LABEL}.csv"
export STEP36_OVERRIDE_ALLOC="output/store_level_allocation_results_${PERIOD_LABEL}_zzfixture.csv"
export STEP36_OVERRIDE_STORE_TAGS="output/store_tags_${PERIOD_LABEL}.csv"
export STEP36_OVERRIDE_ATTRS="output/enriched_store_attributes.csv"
PYTHONPATH=. python src/step36_unified_delivery_builder.py --target-yyyymm "$YYYYMM" --target-period "$HALF"

# 4) Run pytest for Step 36
if [ -f tests/step36/test_step36_planning_and_temperature.py ]; then
  log "Running pytest for Step 36 planning/temperature"
  pytest -q tests/step36/test_step36_planning_and_temperature.py -q || true
else
  log "Test file tests/step36/test_step36_planning_and_temperature.py not found; skipping pytest"
fi

# 5) Restore backups and cleanup fixture-only files
restore_or_remove() {
  local name="$1"
  if [ -f "$bk/$name" ]; then
    log "Restoring output/$name from backup"
    mv "$bk/$name" "output/$name"
  else
    log "Removing fixture output/$name"
    rm -f "output/$name"
  fi
}
restore_or_remove "fast_fish_with_sell_through_analysis_${PERIOD_LABEL}.csv"
restore_or_remove "store_tags_${PERIOD_LABEL}.csv"
restore_or_remove "enriched_store_attributes.csv"
log "Removing fixture allocation file"
rm -f "output/store_level_allocation_results_${PERIOD_LABEL}_zzfixture.csv" || true

# 6) Show latest unified CSV summary
latest_csv=$(ls -1t "output/unified_delivery_${PERIOD_LABEL}_"*.csv | grep -v "_top_" | head -n 1 || true)
if [ -n "${latest_csv:-}" ]; then
  CSV_PATH="$latest_csv" python - << 'PY'
import pandas as pd, os
p=os.environ.get("CSV_PATH")
df=pd.read_csv(p)
print("Latest:", p)
print("Rows:", len(df), "Cols:", len(df.columns))
print("Planning_Season unique:", df["Planning_Season"].dropna().unique()[:5])
print("Temperature_Zone coverage:", f"{df['Temperature_Zone'].notna().mean()*100:.1f}%")
PY
else
  log "No unified_delivery CSV found to summarize"
fi

log "Done."
