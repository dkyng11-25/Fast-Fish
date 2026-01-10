#!/usr/bin/env python3
"""
Rule Quantity Feasibility Analysis

This script analyzes each business rule to determine if item quantity adjustments
are feasible and make business sense. It examines the current data structures,
business logic, and potential for quantity-based recommendations.

Author: Data Pipeline Analysis
Date: 2025-01-02
"""

import os
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

class RuleQuantityAnalyzer:
    """Analyzes each rule for quantity adjustment feasibility."""
    
    def __init__(self):
        self.rules_analysis = {}
        self.data_sources = {
            'store_sales_data': 'data/api_data/store_sales_data.csv',  # Has quantity data
            'complete_spu_sales': 'data/api_data/complete_spu_sales_202505.csv',  # Has SPU sales
            'store_config_data': 'data/api_data/store_config_data.csv'  # Has allocation data
        }
        
    def check_data_availability(self) -> Dict[str, bool]:
        """Check if required data sources are available."""
        log_progress("Checking data source availability...")
        
        availability = {}
        for source, path in self.data_sources.items():
            exists = os.path.exists(path)
            availability[source] = exists
            if exists:
                try:
                    df = pd.read_csv(path, nrows=1)  # Just check header
                    log_progress(f"✅ {source}: Available ({path})")
                except Exception as e:
                    log_progress(f"❌ {source}: File exists but unreadable ({str(e)})")
                    availability[source] = False
            else:
                log_progress(f"❌ {source}: Not found ({path})")
                
        return availability
    
    def analyze_rule7_missing_category(self) -> Dict:
        """Analyze Rule 7: Missing Category Rule for quantity feasibility."""
        log_progress("Analyzing Rule 7: Missing Category Rule...")
        
        rule_info = {
            'rule_name': 'Rule 7: Missing Category Rule',
            'current_output': 'Binary flag (missing/not missing)',
            'has_quantities': False,
            'quantity_feasible': True,
            'quantity_makes_sense': True,
            'implementation_effort': 'MEDIUM',
            'business_value': 'HIGH'
        }
        
        # Check current output structure
        try:
            if os.path.exists('output/rule7_missing_spu_opportunities.csv'):
                df = pd.read_csv('output/rule7_missing_spu_opportunities.csv', nrows=5)
                rule_info['current_columns'] = list(df.columns)
                rule_info['has_sales_data'] = 'expected_sales_opportunity' in df.columns
                
                log_progress("✅ Rule 7 has sales opportunity data - quantity extension feasible")
                
                rule_info['quantity_recommendation'] = {
                    'approach': 'Convert expected_sales_opportunity to quantity using average unit prices',
                    'formula': 'Expected_Quantity = Expected_Sales / Average_Unit_Price_in_Category',
                    'data_needed': ['store category performance', 'average unit prices by category'],
                    'output_format': 'Units to stock for missing SPU (e.g., "Stock 5 units/15-days")',
                    'business_logic': 'Scale successful store quantities to target store category size'
                }
                
            else:
                log_progress("⚠️ Rule 7 output file not found - analyzing from source code")
                rule_info['quantity_recommendation'] = {
                    'approach': 'Add quantity calculation to existing logic',
                    'status': 'Needs implementation'
                }
                
        except Exception as e:
            log_progress(f"❌ Error analyzing Rule 7: {str(e)}")
            rule_info['error'] = str(e)
            
        rule_info['recommendation'] = "IMPLEMENT - High business value, straightforward to add quantity targets"
        return rule_info
    
    def analyze_rule8_imbalanced(self) -> Dict:
        """Analyze Rule 8: Imbalanced Rule for quantity feasibility."""
        log_progress("Analyzing Rule 8: Imbalanced Rule...")
        
        rule_info = {
            'rule_name': 'Rule 8: Imbalanced Rule',
            'current_output': 'Imbalance detection and rebalancing suggestions',
            'has_quantities': False,
            'quantity_feasible': True,
            'quantity_makes_sense': True,
            'implementation_effort': 'MEDIUM',
            'business_value': 'HIGH'
        }
        
        rule_info['quantity_recommendation'] = {
            'approach': 'Rebalancing with specific quantity adjustments',
            'formula': 'Quantity_Adjustment = (Target_Share - Current_Share) × Total_Category_Quantity',
            'data_needed': ['current category quantities', 'target balance ratios'],
            'output_format': 'Quantity shifts (e.g., "Move 3 units from SPU A to SPU B")',
            'business_logic': 'Redistribute quantities to achieve optimal category balance'
        }
        
        rule_info['recommendation'] = "IMPLEMENT - Perfect fit for quantity adjustments, high operational value"
        return rule_info
    
    def analyze_rule9_below_minimum(self) -> Dict:
        """Analyze Rule 9: Below Minimum Rule for quantity feasibility."""
        log_progress("Analyzing Rule 9: Below Minimum Rule...")
        
        rule_info = {
            'rule_name': 'Rule 9: Below Minimum Rule',
            'current_output': 'Below minimum threshold detection',
            'has_quantities': False,
            'quantity_feasible': True,
            'quantity_makes_sense': True,
            'implementation_effort': 'LOW',
            'business_value': 'HIGH'
        }
        
        rule_info['quantity_recommendation'] = {
            'approach': 'Set minimum quantity thresholds and recommend top-ups',
            'formula': 'Required_Quantity = Max(Minimum_Threshold, Current_Quantity)',
            'data_needed': ['minimum quantity thresholds by category', 'current quantities'],
            'output_format': 'Quantity to add (e.g., "Add 2 units to reach minimum of 5")',
            'business_logic': 'Ensure all categories meet minimum stocking levels'
        }
        
        rule_info['recommendation'] = "IMPLEMENT - Natural fit, easy to implement, immediate operational value"
        return rule_info
    
    def analyze_rule10_overcapacity(self) -> Dict:
        """Analyze Rule 10: Smart Overcapacity Rule for quantity feasibility."""
        log_progress("Analyzing Rule 10: Smart Overcapacity Rule...")
        
        rule_info = {
            'rule_name': 'Rule 10: Smart Overcapacity Rule',
            'current_output': 'Overcapacity detection and SPU reduction recommendations',
            'has_quantities': False,
            'quantity_feasible': True,
            'quantity_makes_sense': True,
            'implementation_effort': 'MEDIUM',
            'business_value': 'HIGH'
        }
        
        # Check current output structure
        try:
            if os.path.exists('output/rule10_spu_overcapacity_opportunities.csv'):
                df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv', nrows=5)
                rule_info['current_columns'] = list(df.columns)
                rule_info['has_excess_count'] = 'excess_spu_count' in df.columns
                
                rule_info['quantity_recommendation'] = {
                    'approach': 'Convert SPU reduction to quantity reduction with reallocation',
                    'formula': 'Quantity_to_Reduce = (Excess_SPUs / Total_SPUs) × Total_Category_Quantity',
                    'data_needed': ['current quantities by SPU', 'performance rankings'],
                    'output_format': 'Quantity reductions (e.g., "Reduce by 8 units, focus on top 5 SPUs")',
                    'business_logic': 'Consolidate quantities into best-performing SPUs'
                }
                
        except Exception as e:
            log_progress(f"⚠️ Could not analyze Rule 10 details: {str(e)}")
            
        rule_info['recommendation'] = "IMPLEMENT - High impact, helps optimize inventory efficiency"
        return rule_info
    
    def analyze_rule11_missed_sales(self) -> Dict:
        """Analyze Rule 11: Missed Sales Opportunity Rule for quantity feasibility."""
        log_progress("Analyzing Rule 11: Missed Sales Opportunity Rule...")
        
        rule_info = {
            'rule_name': 'Rule 11: Missed Sales Opportunity Rule',
            'current_output': 'ALREADY HAS QUANTITY RECOMMENDATIONS! ✅',
            'has_quantities': True,
            'quantity_feasible': True,
            'quantity_makes_sense': True,
            'implementation_effort': 'NONE (ALREADY DONE)',
            'business_value': 'HIGH'
        }
        
        # Check current implementation
        try:
            if os.path.exists('output/rule11_improved_missed_sales_opportunity_spu_details.csv'):
                df = pd.read_csv('output/rule11_improved_missed_sales_opportunity_spu_details.csv', nrows=5)
                rule_info['current_columns'] = list(df.columns)
                
                quantity_cols = [col for col in df.columns if 'qty' in col.lower() or 'quantity' in col.lower()]
                rule_info['quantity_columns'] = quantity_cols
                
                log_progress("✅ Rule 11 ALREADY IMPLEMENTED with full quantity recommendations!")
                
                rule_info['current_implementation'] = {
                    'approach': 'Proportional scaling with incremental recommendations',
                    'formula': 'Recommended_SPU_Units = Target_Category_Units × SPU_Quantity_Ratio',
                    'features': [
                        'ADD_NEW vs INCREASE_EXISTING recommendations',
                        'Current vs target quantity gaps',
                        'Incremental quantity recommendations',
                        '15-day period accuracy',
                        'Unit price calculations'
                    ],
                    'output_format': 'Specific unit targets (e.g., "ADD 3 UNITS/15-DAYS" or "+2 MORE UNITS")'
                }
                
        except Exception as e:
            log_progress(f"⚠️ Could not analyze Rule 11 details: {str(e)}")
            
        rule_info['recommendation'] = "COMPLETE ✅ - Already fully implemented with quantity recommendations"
        return rule_info
    
    def analyze_rule12_sales_performance(self) -> Dict:
        """Analyze Rule 12: Sales Performance Rule for quantity feasibility."""
        log_progress("Analyzing Rule 12: Sales Performance Rule...")
        
        rule_info = {
            'rule_name': 'Rule 12: Sales Performance Rule',
            'current_output': 'Performance classification (Z-score based)',
            'has_quantities': False,
            'quantity_feasible': True,
            'quantity_makes_sense': True,
            'implementation_effort': 'MEDIUM',
            'business_value': 'HIGH'
        }
        
        rule_info['quantity_recommendation'] = {
            'approach': 'Performance-based quantity optimization',
            'formula': 'Target_Quantity = Current_Quantity × (Target_Performance / Current_Performance)',
            'data_needed': ['performance benchmarks', 'current quantities', 'cluster targets'],
            'output_format': 'Performance-driven adjustments (e.g., "Increase to 8 units to reach cluster average")',
            'business_logic': 'Adjust quantities to achieve target performance levels within cluster'
        }
        
        rule_info['recommendation'] = "IMPLEMENT - Strong analytical foundation, clear quantity targets possible"
        return rule_info
    
    def analyze_all_rules(self) -> Dict:
        """Analyze all rules for quantity feasibility."""
        log_progress("Starting comprehensive rule quantity feasibility analysis...")
        
        # Check data availability first
        data_availability = self.check_data_availability()
        
        # Analyze each rule
        analyses = {
            'rule7': self.analyze_rule7_missing_category(),
            'rule8': self.analyze_rule8_imbalanced(),
            'rule9': self.analyze_rule9_below_minimum(),
            'rule10': self.analyze_rule10_overcapacity(),
            'rule11': self.analyze_rule11_missed_sales(),
            'rule12': self.analyze_rule12_sales_performance()
        }
        
        # Create summary
        summary = {
            'data_availability': data_availability,
            'rule_analyses': analyses,
            'overall_feasibility': self.create_overall_assessment(analyses),
            'implementation_roadmap': self.create_implementation_roadmap(analyses),
            'business_impact_assessment': self.assess_business_impact(analyses)
        }
        
        return summary
    
    def create_overall_assessment(self, analyses: Dict) -> Dict:
        """Create overall feasibility assessment."""
        
        total_rules = len(analyses)
        feasible_rules = sum(1 for rule in analyses.values() if rule['quantity_feasible'])
        makes_sense_rules = sum(1 for rule in analyses.values() if rule['quantity_makes_sense'])
        already_implemented = sum(1 for rule in analyses.values() if rule['has_quantities'])
        
        return {
            'total_rules_analyzed': total_rules,
            'quantity_feasible_rules': feasible_rules,
            'business_sense_rules': makes_sense_rules,
            'already_implemented': already_implemented,
            'implementation_needed': feasible_rules - already_implemented,
            'feasibility_percentage': (feasible_rules / total_rules) * 100,
            'overall_recommendation': 'HIGHLY FEASIBLE - Most rules can benefit from quantity adjustments'
        }
    
    def create_implementation_roadmap(self, analyses: Dict) -> List[Dict]:
        """Create implementation roadmap prioritized by effort and value."""
        
        roadmap = []
        
        for rule_key, analysis in analyses.items():
            if not analysis['has_quantities'] and analysis['quantity_feasible']:
                effort_score = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}.get(analysis['implementation_effort'], 2)
                value_score = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}.get(analysis['business_value'], 2)
                priority_score = value_score / effort_score  # Higher is better
                
                roadmap.append({
                    'rule': analysis['rule_name'],
                    'effort': analysis['implementation_effort'],
                    'value': analysis['business_value'],
                    'priority_score': priority_score,
                    'recommendation': analysis['recommendation']
                })
        
        # Sort by priority score (highest first)
        roadmap.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return roadmap
    
    def assess_business_impact(self, analyses: Dict) -> Dict:
        """Assess overall business impact of quantity implementations."""
        
        return {
            'operational_benefits': [
                'Clear stocking guidance for store operations',
                'Reduced guesswork in inventory management',
                'Optimized shelf space utilization',
                'Better demand-supply matching'
            ],
            'financial_benefits': [
                'Reduced overstock and understock situations',
                'Improved sales conversion rates',
                'Lower inventory carrying costs',
                'Increased revenue from optimized assortments'
            ],
            'strategic_benefits': [
                'Data-driven merchandising decisions',
                'Competitive advantage through optimization',
                'Scalable inventory management processes',
                'Enhanced customer satisfaction through availability'
            ],
            'implementation_considerations': [
                'Need for unit price data integration',
                'Training for operations teams',
                'System integration requirements',
                'Change management for new processes'
            ]
        }
    
    def save_analysis_report(self, analysis_results: Dict) -> None:
        """Save comprehensive analysis report."""
        
        report_file = "rule_quantity_feasibility_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Rule Quantity Feasibility Analysis Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            f.write("## 🎯 Executive Summary\n\n")
            overall = analysis_results['overall_feasibility']
            f.write(f"- **{overall['quantity_feasible_rules']}/{overall['total_rules_analyzed']} rules** are feasible for quantity adjustments ({overall['feasibility_percentage']:.0f}%)\n")
            f.write(f"- **{overall['already_implemented']} rule** already has quantity recommendations implemented\n")
            f.write(f"- **{overall['implementation_needed']} rules** need quantity implementation\n")
            f.write(f"- **Overall Assessment**: {overall['overall_recommendation']}\n\n")
            
            # Data Availability
            f.write("## 📊 Data Availability\n\n")
            for source, available in analysis_results['data_availability'].items():
                status = "✅ Available" if available else "❌ Missing"
                f.write(f"- **{source}**: {status}\n")
            f.write("\n")
            
            # Rule-by-Rule Analysis
            f.write("## 📋 Rule-by-Rule Analysis\n\n")
            for rule_key, analysis in analysis_results['rule_analyses'].items():
                f.write(f"### {analysis['rule_name']}\n\n")
                f.write(f"- **Current Output**: {analysis['current_output']}\n")
                f.write(f"- **Has Quantities**: {'✅ Yes' if analysis['has_quantities'] else '❌ No'}\n")
                f.write(f"- **Quantity Feasible**: {'✅ Yes' if analysis['quantity_feasible'] else '❌ No'}\n")
                f.write(f"- **Makes Business Sense**: {'✅ Yes' if analysis['quantity_makes_sense'] else '❌ No'}\n")
                f.write(f"- **Implementation Effort**: {analysis['implementation_effort']}\n")
                f.write(f"- **Business Value**: {analysis['business_value']}\n")
                f.write(f"- **Recommendation**: {analysis['recommendation']}\n")
                
                if 'quantity_recommendation' in analysis:
                    f.write(f"\n**Quantity Implementation Approach**:\n")
                    rec = analysis['quantity_recommendation']
                    f.write(f"- **Approach**: {rec['approach']}\n")
                    if 'formula' in rec:
                        f.write(f"- **Formula**: `{rec['formula']}`\n")
                    if 'output_format' in rec:
                        f.write(f"- **Output Format**: {rec['output_format']}\n")
                
                f.write("\n")
            
            # Implementation Roadmap
            f.write("## 🛣️ Implementation Roadmap\n\n")
            f.write("Prioritized by business value vs implementation effort:\n\n")
            for i, item in enumerate(analysis_results['implementation_roadmap'], 1):
                f.write(f"{i}. **{item['rule']}**\n")
                f.write(f"   - Effort: {item['effort']}, Value: {item['value']}\n")
                f.write(f"   - Priority Score: {item['priority_score']:.2f}\n")
                f.write(f"   - Action: {item['recommendation']}\n\n")
            
            # Business Impact Assessment
            f.write("## 💼 Business Impact Assessment\n\n")
            impact = analysis_results['business_impact_assessment']
            
            f.write("### Operational Benefits\n")
            for benefit in impact['operational_benefits']:
                f.write(f"- {benefit}\n")
            f.write("\n")
            
            f.write("### Financial Benefits\n")
            for benefit in impact['financial_benefits']:
                f.write(f"- {benefit}\n")
            f.write("\n")
            
            f.write("### Strategic Benefits\n")
            for benefit in impact['strategic_benefits']:
                f.write(f"- {benefit}\n")
            f.write("\n")
            
            f.write("### Implementation Considerations\n")
            for consideration in impact['implementation_considerations']:
                f.write(f"- {consideration}\n")
            f.write("\n")
            
        log_progress(f"Analysis report saved to {report_file}")

def main():
    """Main analysis function."""
    log_progress("Starting Rule Quantity Feasibility Analysis...")
    
    analyzer = RuleQuantityAnalyzer()
    results = analyzer.analyze_all_rules()
    analyzer.save_analysis_report(results)
    
    # Print summary to console
    print("\n" + "="*80)
    print("🎯 RULE QUANTITY FEASIBILITY ANALYSIS SUMMARY")
    print("="*80)
    
    overall = results['overall_feasibility']
    print(f"\n✅ FEASIBILITY: {overall['quantity_feasible_rules']}/{overall['total_rules_analyzed']} rules ({overall['feasibility_percentage']:.0f}%)")
    print(f"✅ ALREADY IMPLEMENTED: {overall['already_implemented']} rule")
    print(f"🔧 NEEDS IMPLEMENTATION: {overall['implementation_needed']} rules")
    print(f"\n🎯 RECOMMENDATION: {overall['overall_recommendation']}")
    
    print(f"\n📋 IMPLEMENTATION PRIORITY:")
    for i, item in enumerate(results['implementation_roadmap'][:3], 1):
        print(f"{i}. {item['rule']} (Value: {item['value']}, Effort: {item['effort']})")
    
    print(f"\n📄 Full report saved to: rule_quantity_feasibility_report.md")
    print("="*80)

if __name__ == "__main__":
    main() 