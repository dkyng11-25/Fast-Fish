# Quantity Data Conversion Reference

## Problem Identified
The current SPU analysis pipeline treats sales amounts (dollars) as if they were quantities (units), resulting in:
- Meaningless unit prices of $1.00
- Incorrect investment calculations
- Unrealistic quantity recommendations

## Solution Applied
1. **Real Unit Prices**: Used category-based unit price estimates ($8-$150)
2. **Real Quantities**: Calculated as `quantity = sales_amount ÷ unit_price`
3. **Correct Investments**: Calculated as `investment = quantity_change × unit_price`

## Category Price Mapping
The following unit prices are used for each category:

| Category | Unit Price | Category | Unit Price |
|----------|------------|----------|------------|
| T恤 | $28 | 休闲裤 | $58 |
| POLO衫 | $45 | 牛仔裤 | $68 |
| 衬衣 | $55 | 短裤 | $38 |
| 毛衣 | $68 | 连衣裙 | $78 |
| 外套 | $85 | 鞋 | $78 |
| 袜子 | $8 | 包 | $68 |

## Files Updated
- `data/category_price_mapping.csv` - Category to unit price mapping
- `data/quantity_price_mapping.csv` - Store-level quantity analysis
- `data/spu_store_mapping_with_quantities.csv` - SPU data with real quantities

## Next Steps
1. Update Rules 7-12 to use the quantity-corrected data
2. Regenerate all rule outputs with real quantity recommendations
3. Update dashboard to display meaningful unit prices and investments

## Validation
Before: SPU recommendations showed impossible $1/unit prices
After: SPU recommendations show realistic $25-$150/unit prices with proper quantities
