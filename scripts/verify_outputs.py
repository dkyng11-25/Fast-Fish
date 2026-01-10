#!/usr/bin/env python3
import os, json, sys
import pandas as pd

def main():
    target_yyyymm = os.environ.get('VERIFY_YYYYMM', '202509')
    periods = ['A','B']
    manifest_path = os.path.join('output','pipeline_manifest.json')
    man = json.load(open(manifest_path))

    def get(step, key):
        return man.get('steps',{}).get(step,{}).get('outputs',{}).get(key, {})

    report = {}
    # Step 14, 17, 18, 22 minimal checks
    for p in periods:
        pl = f"{target_yyyymm}{p}"
        checks = {}
        # Step 14
        step14 = get('step14', f'enhanced_fast_fish_format_{pl}')
        path14 = step14.get('file_path')
        checks['step14'] = {'path': path14, 'ok': bool(path14 and os.path.exists(path14))}
        # Step 17
        step17 = get('step17', f'augmented_recommendations_{pl}')
        path17 = step17.get('file_path')
        checks['step17'] = {'path': path17, 'ok': bool(path17 and os.path.exists(path17))}
        # Step 18
        step18 = get('step18', f'sell_through_analysis_{pl}')
        path18 = step18.get('file_path')
        checks['step18'] = {'path': path18, 'ok': bool(path18 and os.path.exists(path18))}
        # Step 22
        step22 = get('step22', f'enriched_store_attributes_{pl}')
        path22 = step22.get('file_path')
        checks['step22'] = {'path': path22, 'ok': bool(path22 and os.path.exists(path22))}
        report[pl] = checks
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()















