#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR" || exit 1

log() { echo "[$(date +%Y-%m-%d' '%H:%M:%S)] $*"; }

wait_for_file() {
  local path="$1"; shift
  local min_bytes="${1:-1048576}"; shift || true
  local tries=0
  while true; do
    if [ -f "$path" ]; then
      local sz
      sz=$(stat -f %z "$path" 2>/dev/null || stat -c %s "$path" 2>/dev/null || echo 0)
      if [ "$sz" -ge "$min_bytes" ]; then
        log "✓ File ready: $path ($sz bytes)"
        return 0
      fi
    fi
    tries=$((tries+1))
    if [ $((tries % 60)) -eq 0 ]; then
      log "… waiting for $path (tries=$tries)"
    fi
    sleep 5
  done
}

ensure_store_sales_from_spu() {
  local label="$1"
  local spu="output/complete_spu_sales_${label}.csv"
  local out="output/store_sales_${label}.csv"
  if [ -f "$out" ]; then
    log "✓ store_sales exists: $out"; return 0
  fi
  log "Aggregating store_sales from SPU: $spu -> $out"
  python - <<PY || { log "ERROR building store_sales for ${label}"; return 1; }
import pandas as pd
from pathlib import Path
spu=Path("$spu"); out=Path("$out")
df=pd.read_csv(spu)
lower={c.lower():c for c in df.columns}
str_col = lower.get('str_code') or lower.get('store_code') or 'str_code'
amt_col = lower.get('spu_sales_amt') or lower.get('sales_amt') or lower.get('sal_amt')
qty_col = lower.get('quantity') or lower.get('sales_qty') or lower.get('sal_qty')
for c in [amt_col, qty_col]:
    if c and c in df.columns:
        df[c]=pd.to_numeric(df[c], errors='coerce').fillna(0)
agg = {}
if amt_col: agg['total_sal_amt']=(amt_col,'sum')
if qty_col: agg['total_sal_qty']=(qty_col,'sum')
store=df.groupby(df[str_col].astype(str), as_index=False).agg(**agg).rename(columns={str_col:'str_code'})
store.to_csv(out, index=False)
print('WROTE', out, len(store))
PY
}

run_step22() {
  local yyyymm="$1"; local period="$2"
  log "▶ Step 22 for ${yyyymm}${period}"
  PIPELINE_YYYYMM="$yyyymm" PIPELINE_PERIOD="$period" PYTHONPATH=. \
    python src/step22_store_attribute_enrichment.py --target-yyyymm "$yyyymm" --target-period "$period" | tee -a "runlogs/step22_${yyyymm}${period}_$(date +%Y%m%d_%H%M%S).log"
}

run_step28() {
  local yyyymm="$1"; local period="$2"
  log "▶ Step 28 for ${yyyymm}${period}"
  PIPELINE_YYYYMM="$yyyymm" PIPELINE_PERIOD="$period" PYTHONPATH=. \
    python src/step28_scenario_analyzer.py --target-yyyymm "$yyyymm" --target-period "$period" --scenario AUTO | tee -a "runlogs/step28_${yyyymm}${period}_$(date +%Y%m%d_%H%M%S).log"
}

maybe_run_step36() {
  local yyyymm="$1"; local period="$2"; local label="${yyyymm}${period}"
  # Require allocation and period-specific attrs
  local alloc
  alloc=$(ls -1t output/store_level_allocation_results_${label}_*.csv 2>/dev/null | head -1 || true)
  local attrs
  attrs=$(ls -1t output/enriched_store_attributes_${label}_*.csv 2>/dev/null | head -1 || true)
  if [ -n "$alloc" ] && [ -n "$attrs" ]; then
    log "▶ Step 36 for ${label} (alloc=$(basename "$alloc"), attrs=$(basename "$attrs"))"
    PIPELINE_YYYYMM="$yyyymm" PIPELINE_PERIOD="$period" PYTHONPATH=. \
      python src/step36_unified_delivery_builder.py --target-yyyymm "$yyyymm" --target-period "$period" | tee -a "runlogs/step36_${label}_$(date +%Y%m%d_%H%M%S).log"
  else
    log "ℹ️ Skipping Step 36 for ${label} (missing allocation or attrs)"
  fi
}

process_label() {
  local label="$1"; local yyyymm="${label:0:6}"; local period="${label:6:1}"
  log "==== Orchestrating ${label} ===="
  local spu="output/complete_spu_sales_${label}.csv"
  wait_for_file "$spu" 1048576
  ensure_store_sales_from_spu "$label" || return 1
  run_step22 "$yyyymm" "$period"
  run_step28 "$yyyymm" "$period"
  maybe_run_step36 "$yyyymm" "$period"
}

labels=("202509A" "202509B")
for L in "${labels[@]}"; do
  ( process_label "$L" ) &
done
wait
log "✅ September orchestration completed"


