#!/usr/bin/env bash
set -Eeuo pipefail

YYYYMM=202507
TARGET=202509
SEASONAL_YYYYMM=202409
SEASONAL_WEIGHT=0.60

LOGROOT="runlogs/${YYYYMM}_to_${TARGET}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOGROOT"
echo "Logs: $LOGROOT"

for P in A B; do
  echo "=== Period $P ==="

  LOG="$LOGROOT/step7_${P}.log"
  echo "[RUN] Step 7 -> $LOG"
  python3 -u -m src.step7_missing_category_rule \
    --yyyymm "$YYYYMM" --period "$P" --analysis-level spu \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step8_${P}.log"
  echo "[RUN] Step 8 -> $LOG"
  python3 -u -m src.step8_imbalanced_rule \
    --yyyymm "$YYYYMM" --period "$P" \
    --analysis-level spu \
    --target-yyyymm "$TARGET" --target-period "$P" \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step9_${P}.log"
  echo "[RUN] Step 9 -> $LOG"
  python3 -u -m src.step9_below_minimum_rule \
    --yyyymm "$YYYYMM" --period "$P" \
    --analysis-level spu \
    --seasonal-blending --seasonal-yyyymm "$SEASONAL_YYYYMM" --seasonal-period "$P" --seasonal-weight "$SEASONAL_WEIGHT" \
    --target-yyyymm "$TARGET" --target-period "$P" \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step10_${P}.log"
  echo "[RUN] Step 10 -> $LOG"
  python3 -u -m src.step10_spu_assortment_optimization \
    --yyyymm "$YYYYMM" --period "$P" \
    --analysis-level spu \
    --target-yyyymm "$TARGET" --target-period "$P" \
    --seasonal-blending \
    --max-adj-per-store 30 \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step11_${P}.log"
  echo "[RUN] Step 11 -> $LOG"
  python3 -u -m src.step11_missed_sales_opportunity \
    --yyyymm "$YYYYMM" --period "$P" \
    --target-yyyymm "$TARGET" --target-period "$P" \
    --seasonal-blending \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step12_${P}.log"
  echo "[RUN] Step 12 -> $LOG"
  python3 -u -m src.step12_sales_performance_rule \
    --yyyymm "$YYYYMM" --period "$P" \
    --target-yyyymm "$TARGET" --target-period "$P" \
    --seasonal-blending \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step13_${P}.log"
  echo "[RUN] Step 13 -> $LOG"
  python3 -u -m src.step13_consolidate_spu_rules \
    --target-yyyymm "$TARGET" --target-period "$P" \
    2>&1 | tee "$LOG"

  LOG="$LOGROOT/step14_${P}.log"
  echo "[RUN] Step 14 -> $LOG"
  STEP14_PERIOD="$P" python3 -u -m src.step14_create_fast_fish_format \
    2>&1 | tee "$LOG"

done

echo "Done. Logs in $LOGROOT"
