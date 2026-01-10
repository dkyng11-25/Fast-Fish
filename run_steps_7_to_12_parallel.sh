#!/bin/bash

# Run Steps 7-12 in Parallel with Historical Symlinks
# All steps now have access to 202507A-202508B and 202409A-202412B data

cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main

export RECENT_MONTHS_BACK=3
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PYTHONPATH=.

echo "🚀 Running Steps 7-12 in Parallel"
echo "===================================="
echo "All steps have access to historical symlinks:"
echo "  - 202507A, 202507B, 202508A, 202508B"
echo "  - 202509A, 202509B, 202510A"
echo "  - 202409A-202412B"
echo ""

# Run all 6 steps in parallel
echo "▶️  Starting Step 7: Missing Category Rule..."
PYTHONPATH=. RECENT_MONTHS_BACK=3 PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A \
  python3 src/step7_missing_category_rule.py --target-yyyymm 202510 --target-period A \
  > step7_parallel.log 2>&1 &
PID7=$!

echo "▶️  Starting Step 8: Imbalanced Rule..."
PYTHONPATH=. RECENT_MONTHS_BACK=3 PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A \
  python3 src/step8_imbalanced_rule.py --target-yyyymm 202510 --target-period A \
  > step8_parallel.log 2>&1 &
PID8=$!

echo "▶️  Starting Step 9: Below Minimum Rule..."
PYTHONPATH=. RECENT_MONTHS_BACK=3 PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A \
  python3 src/step9_below_minimum_rule.py --target-yyyymm 202510 --target-period A \
  > step9_parallel.log 2>&1 &
PID9=$!

echo "▶️  Starting Step 10: SPU Assortment Optimization..."
PYTHONPATH=. RECENT_MONTHS_BACK=3 PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A \
  python3 src/step10_spu_assortment_optimization.py --yyyymm 202510 --period A --target-yyyymm 202510 --target-period A \
  > step10_parallel.log 2>&1 &
PID10=$!

echo "▶️  Starting Step 11: Missed Sales Opportunity..."
PYTHONPATH=. RECENT_MONTHS_BACK=3 PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A \
  python3 src/step11_missed_sales_opportunity.py --target-yyyymm 202510 --target-period A \
  > step11_parallel.log 2>&1 &
PID11=$!

echo "▶️  Starting Step 12: Sales Performance Rule..."
PYTHONPATH=. RECENT_MONTHS_BACK=3 PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A \
  python3 src/step12_sales_performance_rule.py --target-yyyymm 202510 --target-period A \
  > step12_parallel.log 2>&1 &
PID12=$!

echo ""
echo "⏳ All 6 steps running in parallel..."
echo "   PIDs: $PID7 (Step 7), $PID8 (Step 8), $PID9 (Step 9)"
echo "        $PID10 (Step 10), $PID11 (Step 11), $PID12 (Step 12)"
echo ""
echo "📊 Monitor progress:"
echo "   tail -f step7_parallel.log"
echo "   tail -f step8_parallel.log"
echo "   tail -f step9_parallel.log"
echo "   tail -f step10_parallel.log"
echo "   tail -f step11_parallel.log"
echo "   tail -f step12_parallel.log"
echo ""

# Wait for all processes to complete
echo "⏳ Waiting for all steps to complete..."
wait $PID7
STATUS7=$?
echo "✅ Step 7 completed (exit code: $STATUS7)"

wait $PID8
STATUS8=$?
echo "✅ Step 8 completed (exit code: $STATUS8)"

wait $PID9
STATUS9=$?
echo "✅ Step 9 completed (exit code: $STATUS9)"

wait $PID10
STATUS10=$?
echo "✅ Step 10 completed (exit code: $STATUS10)"

wait $PID11
STATUS11=$?
echo "✅ Step 11 completed (exit code: $STATUS11)"

wait $PID12
STATUS12=$?
echo "✅ Step 12 completed (exit code: $STATUS12)"

echo ""
echo "🎉 =============================================="
echo "🎉 Steps 7-12 Parallel Execution Complete!"
echo "🎉 =============================================="
echo ""
echo "Exit codes:"
echo "  Step 7: $STATUS7"
echo "  Step 8: $STATUS8"
echo "  Step 9: $STATUS9"
echo "  Step 10: $STATUS10"
echo "  Step 11: $STATUS11"
echo "  Step 12: $STATUS12"
echo ""

# Check if any failed
FAILED=0
for code in $STATUS7 $STATUS8 $STATUS9 $STATUS10 $STATUS11 $STATUS12; do
  if [ $code -ne 0 ]; then
    FAILED=1
  fi
done

if [ $FAILED -eq 0 ]; then
  echo "✅ All steps completed successfully!"
  echo ""
  echo "Next: Run Steps 13-36 with:"
  echo "  ./continue_from_step13.sh"
else
  echo "⚠️  Some steps failed. Check the logs above."
  echo ""
  echo "Review logs:"
  echo "  cat step*_parallel.log"
fi
