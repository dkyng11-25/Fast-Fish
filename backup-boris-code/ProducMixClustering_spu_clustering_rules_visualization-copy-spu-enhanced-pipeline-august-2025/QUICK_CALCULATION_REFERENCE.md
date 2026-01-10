# Quick Calculation Reference Card

## 🎯 **Core Formulas**

### **Sell-Through Rate**
```
Sell-Through Rate = (SPU-store-days with sales ÷ SPU-store-days with inventory) × 100%

Components:
• SPU-store-days with inventory = Target SPUs × Stores × 15 days
• SPU-store-days with sales = Daily SPUs sold × Stores × 15 days
```

### **ROI Calculation**
```
ROI = (Net Profit ÷ Total Investment) × 100%
Net Profit = Expected Benefits - Investment Required

Current System:
• Expected Benefits: ¥10,170,485
• Investment: ¥8,870,406
• ROI: 14.7%
```

### **Investment Calculation**
```
Method 1 (SPU-Based): SPUs × ¥50/unit
Method 2 (Sales-Based): Current Sales × 5%
```

## 📊 **Key Files**

| Calculation | Script Location | Function |
|-------------|----------------|----------|
| Sell-Through | `src/step18_validate_results.py` | `add_sell_through_calculations()` |
| ROI | `calculate_all_presentation_numbers.py` | `calculate_recommendation_metrics()` |
| Business Rules | `data/pipeline/rules/unified_business_rules.py` | Various rule functions |

## ✅ **Validation Status**

- ✅ **Sell-Through**: Client-verified formula, 98.1% data coverage
- ✅ **ROI**: Corrected from 282.0% to realistic 14.7%
- ✅ **Investment**: Conservative estimates, industry-aligned
- ✅ **Benefits**: Real data extraction, no synthetic values 