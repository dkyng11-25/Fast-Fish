#!/usr/bin/env bash
set -euo pipefail

YYYYMM=202509
PERIODS=(A B)

run_step () { local step="$1"; shift; echo "=== $(date) :: ${step} ${YYYYMM}${PERIOD} ==="; eval "$@" | tee -a "output/log_${step}_${YYYYMM}${PERIOD}.txt"; echo; }

for PERIOD in "${PERIODS[@]}"; do
  export PIPELINE_TARGET_YYYYMM="${YYYYMM}"
  export PIPELINE_TARGET_PERIOD="${PERIOD}"

  run_step step14 "PYTHONPATH=. python src/step14_create_fast_fish_format.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"

  run_step step15 "PYTHONPATH=. python src/step15_download_historical_baseline.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD} --baseline-yyyymm 202407 --baseline-period A"
  run_step step16 "PYTHONPATH=. python src/step16_create_comparison_tables.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"

  run_step step17 "PYTHONPATH=. python src/step17_augment_recommendations.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD} --current-analysis-file output/enhanced_fast_fish_format_${YYYYMM}${PERIOD}.csv"
  run_step step18 "PYTHONPATH=. python src/step18_validate_results.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"

  run_step step20 "PYTHONPATH=. python src/step20_data_validation.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step22 "PYTHONPATH=. python src/step22_store_attribute_enrichment.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step24 "PYTHONPATH=. python src/step24_comprehensive_cluster_labeling.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step25 "PYTHONPATH=. python src/step25_product_role_classifier.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step27 "PYTHONPATH=. python src/step27_gap_matrix_generator.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step29 "PYTHONPATH=. python src/step29_supply_demand_gap_analysis.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step30 "PYTHONPATH=. python src/step30_sellthrough_optimization_engine.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step31 "PYTHONPATH=. python src/step31_gap_analysis_workbook.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"
  run_step step33 "PYTHONPATH=. python src/step33_store_level_plugin_output.py --target-yyyymm ${YYYYMM} --target-period ${PERIOD}"

  echo "✅ Done ${YYYYMM}${PERIOD}"
done

echo "=== $(date) :: step34_unify ${YYYYMM}AB ==="
PYTHONPATH=. python src/step34_unify_outputs.py --target-yyyymm ${YYYYMM} --periods A,B --source enhanced | tee -a "output/log_step34_${YYYYMM}AB.txt"
echo
echo "=== $(date) :: validate_step34 ${YYYYMM}AB ==="
python scripts/validate_step34_unified.py --target-yyyymm ${YYYYMM} --periods A,B --source enhanced | tee -a "output/log_validate_step34_${YYYYMM}AB.txt"
echo

echo "🎯 All steps completed for ${YYYYMM}A and ${YYYYMM}B"
