#!/usr/bin/env python3
"""
Pipeline File Pattern Analysis Script

This script analyzes all pipeline steps to identify:
1. Steps that read timestamped files (problematic)
2. Steps that only output timestamped files without generic versions
3. File dependency chains and potential breaks

Author: Pipeline Team
Date: 2025-10-01
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime
import json

def log_progress(message):
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def analyze_step_file(step_file):
    """Analyze a single step file for input/output patterns"""
    step_name = Path(step_file).stem
    
    with open(step_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    analysis = {
        'step': step_name,
        'file_path': step_file,
        'inputs': {
            'timestamped_reads': [],
            'generic_reads': [],
            'manifest_reads': []
        },
        'outputs': {
            'timestamped_only': [],
            'generic_only': [],
            'both_versions': []
        },
        'issues': []
    }
    
    # Find all file reads (pd.read_csv, open, etc.)
    read_patterns = [
        r'pd\.read_csv\(["\']([^"\']+)["\']',
        r'open\(["\']([^"\']+)["\']',
        r'with open\(["\']([^"\']+)["\']',
        r'\.read_csv\(["\']([^"\']+)["\']',
        r'Path\(["\']([^"\']+)["\']'
    ]
    
    for pattern in read_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if re.search(r'\d{8}_\d{6}', match):  # Timestamped pattern
                analysis['inputs']['timestamped_reads'].append(match)
            elif match.startswith(('output/', 'data/')):
                analysis['inputs']['generic_reads'].append(match)
    
    # Find manifest-based reads
    manifest_patterns = [
        r'manifest\.get\(["\']([^"\']+)["\']',
        r'step\d+.*get\(["\']([^"\']+)["\']',
        r'register_step_output\(["\'][^"\']*["\'],\s*["\']([^"\']+)["\']'
    ]
    
    for pattern in manifest_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        analysis['inputs']['manifest_reads'].extend(matches)
    
    # Find file outputs
    output_patterns = [
        r'\.to_csv\(["\']([^"\']+)["\']',
        r'\.to_excel\(["\']([^"\']+)["\']',
        r'\.to_json\(["\']([^"\']+)["\']',
        r'with open\(["\']([^"\']+)["\'].*["\']w["\']'
    ]
    
    for pattern in output_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if re.search(r'\d{8}_\d{6}', match):  # Timestamped pattern
                analysis['outputs']['timestamped_only'].append(match)
            elif match.startswith(('output/', 'data/')):
                analysis['outputs']['generic_only'].append(match)
    
    # Look for both timestamped and generic output patterns
    timestamped_vars = re.findall(r'(\w+)\s*=\s*f?["\'][^"\']*\d{8}_\d{6}[^"\']*["\']', content)
    generic_vars = re.findall(r'(\w+)\s*=\s*["\']output/[^"\']*\.csv["\']', content)
    
    # Find variables that are used for both patterns
    for var in timestamped_vars:
        if var in generic_vars:
            analysis['outputs']['both_versions'].append(var)
    
    # Identify issues
    if analysis['inputs']['timestamped_reads']:
        analysis['issues'].append(f"Reads {len(analysis['inputs']['timestamped_reads'])} timestamped files directly")
    
    if analysis['outputs']['timestamped_only'] and not analysis['outputs']['generic_only']:
        analysis['issues'].append("Only outputs timestamped files, no generic versions")
    
    return analysis

def find_file_dependencies():
    """Find which steps depend on outputs from other steps"""
    dependencies = {}
    
    # Common file patterns that steps expect
    expected_files = {
        'product_role_classifications.csv': {'producer': 'step25', 'consumers': ['step26', 'step27', 'step28']},
        'price_band_analysis.csv': {'producer': 'step26', 'consumers': ['step27', 'step28']},
        'gap_analysis_detailed.csv': {'producer': 'step27', 'consumers': ['step28']},
        'gap_matrix_summary.json': {'producer': 'step27', 'consumers': ['step28']},
        'supply_demand_gap_detailed.csv': {'producer': 'step29', 'consumers': ['step31']},
        'enhanced_fast_fish_format.csv': {'producer': 'step14', 'consumers': ['step17']},
        'fast_fish_with_sell_through_analysis.csv': {'producer': 'step18', 'consumers': ['step32']},
        'consolidated_spu_rule_results.csv': {'producer': 'step13', 'consumers': ['step14']},
        'clustering_results_spu.csv': {'producer': 'step6', 'consumers': ['step32', 'step25', 'step26']}
    }
    
    return expected_files

def analyze_all_steps():
    """Analyze all pipeline steps"""
    log_progress("🔍 Starting comprehensive pipeline file pattern analysis")
    
    step_files = glob.glob("src/step*.py")
    step_files = [f for f in step_files if not f.endswith('_test.py') and not f.endswith('_TEST.py')]
    step_files.sort()
    
    all_analyses = []
    problematic_steps = []
    
    for step_file in step_files:
        try:
            analysis = analyze_step_file(step_file)
            all_analyses.append(analysis)
            
            if analysis['issues']:
                problematic_steps.append(analysis)
                
        except Exception as e:
            log_progress(f"   ❌ Error analyzing {step_file}: {e}")
    
    return all_analyses, problematic_steps

def generate_report(all_analyses, problematic_steps):
    """Generate comprehensive report"""
    
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'total_steps_analyzed': len(all_analyses),
        'problematic_steps_count': len(problematic_steps),
        'summary': {
            'steps_reading_timestamped_files': 0,
            'steps_only_outputting_timestamped': 0,
            'steps_with_both_output_versions': 0
        },
        'detailed_findings': [],
        'recommendations': []
    }
    
    # Detailed analysis
    for analysis in all_analyses:
        finding = {
            'step': analysis['step'],
            'issues': analysis['issues'],
            'timestamped_inputs': len(analysis['inputs']['timestamped_reads']),
            'generic_inputs': len(analysis['inputs']['generic_reads']),
            'manifest_inputs': len(analysis['inputs']['manifest_reads']),
            'timestamped_outputs': len(analysis['outputs']['timestamped_only']),
            'generic_outputs': len(analysis['outputs']['generic_only']),
            'both_output_versions': len(analysis['outputs']['both_versions'])
        }
        
        # Update summary counts
        if analysis['inputs']['timestamped_reads']:
            report['summary']['steps_reading_timestamped_files'] += 1
        
        if analysis['outputs']['timestamped_only'] and not analysis['outputs']['generic_only']:
            report['summary']['steps_only_outputting_timestamped'] += 1
            
        if analysis['outputs']['both_versions']:
            report['summary']['steps_with_both_output_versions'] += 1
        
        report['detailed_findings'].append(finding)
    
    # Generate recommendations
    dependencies = find_file_dependencies()
    
    for file_pattern, info in dependencies.items():
        producer = info['producer']
        consumers = info['consumers']
        
        # Check if producer only outputs timestamped version
        producer_analysis = next((a for a in all_analyses if a['step'] == producer), None)
        if producer_analysis:
            if (producer_analysis['outputs']['timestamped_only'] and 
                not producer_analysis['outputs']['generic_only']):
                
                report['recommendations'].append({
                    'type': 'CRITICAL',
                    'issue': f"{producer} only outputs timestamped {file_pattern}",
                    'impact': f"Consumers {consumers} cannot find generic file",
                    'solution': f"Modify {producer} to output both timestamped and generic versions"
                })
    
    return report

def save_report(report):
    """Save the analysis report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_file = f"output/pipeline_file_pattern_analysis_{timestamp}.json"
    os.makedirs("output", exist_ok=True)
    
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Markdown report
    md_file = f"output/pipeline_file_pattern_analysis_{timestamp}.md"
    
    with open(md_file, 'w') as f:
        f.write("# Pipeline File Pattern Analysis Report\n\n")
        f.write(f"**Generated**: {report['analysis_timestamp']}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Steps Analyzed**: {report['total_steps_analyzed']}\n")
        f.write(f"- **Problematic Steps**: {report['problematic_steps_count']}\n")
        f.write(f"- **Steps Reading Timestamped Files**: {report['summary']['steps_reading_timestamped_files']}\n")
        f.write(f"- **Steps Only Outputting Timestamped**: {report['summary']['steps_only_outputting_timestamped']}\n")
        f.write(f"- **Steps With Both Output Versions**: {report['summary']['steps_with_both_output_versions']}\n\n")
        
        f.write("## Critical Issues\n\n")
        critical_recs = [r for r in report['recommendations'] if r['type'] == 'CRITICAL']
        for rec in critical_recs:
            f.write(f"### {rec['issue']}\n")
            f.write(f"- **Impact**: {rec['impact']}\n")
            f.write(f"- **Solution**: {rec['solution']}\n\n")
        
        f.write("## Detailed Findings\n\n")
        for finding in report['detailed_findings']:
            if finding['issues']:  # Only show problematic steps
                f.write(f"### {finding['step']}\n")
                f.write(f"- **Issues**: {', '.join(finding['issues'])}\n")
                f.write(f"- **Timestamped Inputs**: {finding['timestamped_inputs']}\n")
                f.write(f"- **Generic Inputs**: {finding['generic_inputs']}\n")
                f.write(f"- **Timestamped Outputs**: {finding['timestamped_outputs']}\n")
                f.write(f"- **Generic Outputs**: {finding['generic_outputs']}\n\n")
    
    return json_file, md_file

def main():
    """Main execution function"""
    log_progress("🚀 STARTING PIPELINE FILE PATTERN ANALYSIS")
    
    # Analyze all steps
    all_analyses, problematic_steps = analyze_all_steps()
    
    log_progress(f"📊 Analyzed {len(all_analyses)} steps, found {len(problematic_steps)} with issues")
    
    # Generate comprehensive report
    report = generate_report(all_analyses, problematic_steps)
    
    # Save reports
    json_file, md_file = save_report(report)
    
    log_progress(f"📄 Reports saved:")
    log_progress(f"   • JSON: {json_file}")
    log_progress(f"   • Markdown: {md_file}")
    
    # Print summary
    log_progress("🎯 KEY FINDINGS:")
    log_progress(f"   • Steps reading timestamped files: {report['summary']['steps_reading_timestamped_files']}")
    log_progress(f"   • Steps only outputting timestamped: {report['summary']['steps_only_outputting_timestamped']}")
    log_progress(f"   • Critical recommendations: {len([r for r in report['recommendations'] if r['type'] == 'CRITICAL'])}")
    
    if report['recommendations']:
        log_progress("⚠️  CRITICAL ISSUES FOUND - Review the report for detailed recommendations")
    else:
        log_progress("✅ No critical file pattern issues detected")

if __name__ == "__main__":
    main()
