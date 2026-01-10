# Road-map for Enhancing the Store-Planning Reasonableness Engine

This document outlines the notes and conversation we had and the adjustments we will make as well as some additional recommendations and suggestions. We also updated the tolerances of the store clusters to 50 to allow for more flexibility and easier integration with the business team.

## Business Rules Implementation Details

The following sections detail the mathematical foundation and implementation approach for each business rule in our enhanced reasonableness engine.

---

## 1. Dynamic Capacity/Sales Validation - Instead of Overcapacity Rule

**Rule 8: Imbalanced Allocation Detection (Z-Score Based)**

Swap the provisional capacity table/face limit for live capacity data captured per store ID × display location.
This new system will evaluate the capacity based on other stores in the cluster instead of hard coded rules using statistical Z-Score analysis.

**Mathematical Foundation:**
- **Z-Score Calculation**: `Z_score = (Store_Allocation - Cluster_Mean) / Cluster_StdDev`
- **Threshold**: |Z-Score| > 2.0 flags imbalanced allocation (captures ~95% of normal distribution)
- **Classification**: EXTREME (>3.0), HIGH (>2.5), MODERATE (>2.0) severity levels
- **Recommendation**: Adjust allocation to cluster mean for balanced distribution

**Business Logic:**
If capacity is missing for a store, engine flags "Data Needed" rather than forcing an "unreasonable" verdict.
Uses peer benchmarking within homogeneous clusters to identify over/under-allocated subcategories.
This helps validate store assortment in the cluster as well as making this an easier change for us to implement.

**Added extra column yes or no for imbalance detection.**

---

## 2. Performance Thresholds Tied to Commercial Targets

**Rule 10: Smart Overcapacity Rule (Multi-Profile Threshold Analysis)**

Replace the hard-coded 30% sell-through trigger with a parameterised target that merchandise leads can reset each season.
Provide three ready-made profiles – strict (40%), standard (30%), lenient (20%) – selectable in the dashboard for quick scenario testing.

**Mathematical Foundation:**
- **Performance Score**: `Performance_Score = Sales / Allocation`
- **Profile Thresholds**:
  - Strict (Conservative): 40% gap threshold, targets high-performance reallocations
  - Standard (Balanced): 30% gap threshold, moderate reallocation sensitivity  
  - Lenient (Aggressive): 20% gap threshold, growth-focused reallocation strategies
- **Detection Logic**: Multi-stage filtering ensures high-confidence recommendations
  1. Local underperformance: Store performance ≤ 50%
  2. Cluster underperformance: Cluster average ≤ 50%
  3. External alternative exists: Other clusters > 200% performance

**Business Logic:**
Optional seasonality multipliers allow lower early-season thresholds for slow-build categories (e.g., outerwear).
Profile-based approach enables scenario testing for different business strategies.
Considers both local and cluster-wide performance for sophisticated reallocation decisions.

---

## 3. Missed-Sales Opportunity Rule

**Rule 11: Missed Sales Opportunity Detection (Cluster Peer Performance Analysis)**

New check: If 70%+ of peer stores in the same AI cluster exceed the sell-through target for a sub-category, but a given store's rate is <20%, label "Opportunity Missed".
Recommendation logic suggests increasing facing count or triggering a local promotion rather than pruning assortment.

**Mathematical Foundation:**
- **Sell-Through Rate**: `Sell_Through_Rate = Sales / Allocation`
- **Peer Success Rate**: `Peer_Success_Rate = Stores_Exceeding_Target / Total_Cluster_Stores`
- **Detection Criteria**:
  - Store sell-through rate < 20% (underperformance threshold)
  - Peer success rate ≥ 70% (cluster success threshold)
  - Minimum 3 peer stores for valid analysis
- **Supplementary Measures**:
  - Cluster relative underperformance: Store < (Cluster_Average - 15%)
  - Cluster misjudgment detection for poorly-formed clusters

**Business Logic:**
"Too little choice relative to other stores in the cluster"
This follows the inverse logic of the overcapacity rule - instead of reallocating away from underperformers, we boost underperformers in strong cluster contexts.
Implementation leverages existing aggregated matrices, adding < 1 day of dev time.

---

## 4. Missing Category Opportunity Detection

**Rule 7: Missing Category Rule (Cluster-Based Opportunity Detection)**

Identifies stores missing subcategories that are well-selling among peer stores in the same cluster, representing missed sales opportunities.

**Mathematical Foundation:**
- **Store Penetration**: `Store_Penetration = Stores_Selling_Category / Total_Cluster_Stores`
- **Well-Selling Criteria**:
  - Store penetration ≥ 70% (cluster stores must sell this subcategory)
  - Total cluster sales ≥ 100 units (minimum sales threshold)
  - Expected sales ≥ 50 units (minimum opportunity value)
- **Expected Sales**: `Expected_Sales = Total_Cluster_Sales / Stores_Selling_Category`

**Business Logic:**
Uses cluster peer benchmarking for opportunity identification with statistical significance requirements.
Quantifies financial opportunity value for prioritization.
Focuses on proven categories with demonstrated demand rather than speculative additions.

---

## 5. Commercial Viability Enforcement

**Rule 9: Below Minimum Rule (Viability Threshold)**

Identifies stores/subcategories with positive but below-minimum viable style counts that should either be increased to minimum viable levels or eliminated.

**Mathematical Foundation:**
- **Viability Check**: `Below_Minimum = TRUE if 0 < Allocation < 1.0 styles`
- **Minimum Threshold**: 1.0 styles (commercial viability baseline)
- **Recommendation**: `Increase_Needed = 1.0 - Current_Allocation`
- **Severity Classification**:
  - HIGH: Allocation < 0.5 styles
  - MEDIUM: 0.5 ≤ Allocation < 1.0 styles

**Business Logic:**
Eliminates "limbo" allocations that are too small to be commercially effective.
Simple binary decision framework: increase to minimum viable level or eliminate entirely.
Focuses on commercial viability thresholds rather than complex performance metrics.

---

## 6. Trendiness Handling

Ingest the existing trendy vs non-trendy item flag.
Evaluate mix of trendy vs non-trendy styles (should be labeled as Basic/Fashion)

**Store Type (Basic/Fashion, backcourt only)**: FastFish assumes the store type tag (Basic Mass Market Store vs. Fashion-Oriented Store) is divided based on the ratio of basic and fashion items actually sold in different stores over the past two years. Web3 will assist in validating or optimizing the current assumption-based style tags and their corresponding target customer groups. Required input data may include: current store type tags, customer profile data (member data, or inferred based on geographical location), sales data segmented by product attributes (e.g., style, customer group). Detailed descriptions, formats, and requirements for data needs will be clarified and requested by the Web3 team in document form.

**Mathematical Foundation:**
- **Fashion Ratio**: `Fashion_Ratio = Fashion_Sales / Total_Sales`
- **Store Classification**:
  - Fashion-Heavy: Fashion_Ratio > 60%
  - Balanced: 40% ≤ Fashion_Ratio ≤ 60%
  - Basic-Heavy: Fashion_Ratio < 40%

Graphically represent if a store is fashion heavy vs basic heavy in sales and qty.

---

## 7. Graduated Scoring System (Alert System Update)

Each rule assigns 0-2 penalty points; summed to a Reasonableness Score (0-10):
0-2 = Green, 3-5 = Amber, 6-10 = Red.

**Scoring Matrix:**
- **Rule 8 (Imbalanced)**: 0 points (balanced), 1 point (moderate imbalance), 2 points (extreme imbalance)
- **Rule 9 (Below Minimum)**: 0 points (viable), 1 point (few issues), 2 points (many non-viable allocations)
- **Rule 7 (Missing Category)**: 0 points (complete), 1 point (minor gaps), 2 points (major missed opportunities)
- **Rule 10 (Smart Overcapacity)**: 0 points (efficient), 1 point (some overcapacity), 2 points (significant overcapacity)
- **Rule 11 (Missed Sales)**: 0 points (performing), 1 point (some missed opportunities), 2 points (major underperformance)

"Red" rows still appear as unreasonable in the CSV for backward compatibility, while the dashboard visualises the full scale with colour heat-maps. This allows for details of the reasonableness while also not having so many warnings which could overload the business team.

---

## 8. Geographic Visual Layer

Restore the interactive map: store pins coloured by Reasonableness Score, cluster polygons for context.
Hover tooltip lists top fails (capacity, sell-through, imbalance) so planners spot regional patterns instantly.

**Integration with Rules:**
- **Pin Colors**: Green (0-2), Amber (3-5), Red (6-10) based on combined rule scores
- **Hover Details**: Show specific rule violations and severity levels
- **Cluster Context**: Display cluster boundaries with average performance metrics
- **Regional Patterns**: Identify geographic trends in rule violations

---

## 9. On-site Pilot Launch (Hangzhou)

We propose coming up to Hangzhou Monday the 23rd of June to work with the team on launching the test to work closely with the business team.

**Pilot Scope:**
- Test all 5 business rules with live data
- Validate mathematical formulas with business expectations
- Calibrate thresholds based on merchandise team feedback
- Train business users on graduated scoring interpretation

---

## 10. Post-pilot Follow-up

Virtual meeting early next week to review pilot results, lock in any rule fine-tunes, and prioritise backlog items (data-feed automation, integration hooks).
A one-page action list will circulate 24 h before the call so all stakeholders can prepare.

**Follow-up Activities:**
- Review rule performance metrics and accuracy
- Adjust mathematical thresholds based on pilot feedback
- Optimize computational performance for production scale
- Document final business rule specifications

---

## Additional Implementation Details

### Display Type Integration

Adding the additional display_type for store space and bring this into the rule logic.

**Enhanced Rule Logic:**
- **Display Location Context**: Rules now consider display_location_name in category key formation
- **Space-Aware Calculations**: Performance metrics adjusted for display type characteristics
- **Location-Specific Thresholds**: Different performance expectations for different display locations

### Mathematical Validation Framework

**Common Safeguards Across All Rules:**
1. **Division by Zero Protection**: Safe division operations prevent calculation errors
2. **Sample Size Requirements**: Minimum data points ensure statistical validity
3. **Data Quality Filters**: Remove noise and outliers from calculations
4. **Performance Optimization**: Vectorized operations handle 2M+ records efficiently

### Computational Architecture

**Performance Characteristics:**
- **Time Complexity**: O(n) vectorized operations for all rules
- **Memory Efficiency**: Optimized data types and chunked processing
- **Scalability**: Cluster-based analysis reduces from O(n²) to O(k×n)
- **Production Ready**: Handles full store network with sub-hour execution time

This integrated approach ensures mathematical rigor while maintaining business practicality and user adoption.