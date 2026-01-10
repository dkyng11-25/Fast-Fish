# **Fast Fish × Web3 — Working Checklist**

*(ready to drop into a doc or one-slide-per-item deck)*

---

## **PART A · AB-Testing Launch Acceptance Criteria**

*(Fast Fish 原验收标准 — Acceptance Modules & Dimensions)*

### **1\. Core Logic – KPI Alignment**

* **Requirement / 需求**

  * *EN*: Optimisation engine must maximise **active-sales-rate** (sell-through).

  * *中*: 优化引擎必须以 **售罄率** 为目标函数。

* **Where We Were / 之前状态**

  * *EN*: Objective focused on “relevance”; sell-through not included.

  * *中*: 目标函数仅关注“相关性”，未纳入售罄率。

* **Where We Are Now / 当前状态**   
  **Dedicated sell-through step**

* EN A new **Step 18** adds three turnover metrics to every recommendation.

* 中 新增 **步骤 18**，为每条建议写入 3 个售罄指标。

* ✅ \[ progress \]

  **How the rate is calculated**

* EN Sell-through % \= (historical SPU-store-days with sales) ÷ (projected SPU-store-days of inventory) × 100\.

* 中 售罄率 % \= 历史「SKU-店-天」销量 ÷ 预测库存「SKU-店-天」× 100。

* ✅ \[ progress \]

  **Optimiser now ranks by turnover**

* EN Products with the **highest predicted sell-through** rise to the top; slow-movers drop out.

* 中 系统**优先推荐高售罄率**商品，低周转商品自动降权。

* ✅ \[ progress \]

  **Business-rule upgrades**

* EN Rules on “missing category,” “over/under capacity,” etc. now check sell-through before acting.

* 中 “缺品类”“超/欠配”等规则现先看售罄再决策。

* ✅ \[ progress \]

  **Safe fallback for sparse data**

* EN When history is thin, a conservative floor (≥ 1 unit/day across 15 days) prevents over-buying.

* 中 历史数据不足时，用保守下限（15 天≥ 1 件/天）避免过量订货。

* ✅ \[ progress \]

  **Business impact**

* EN Shifted from “Do we carry it?” → “How fast will it sell?” enabling inventory **velocity-first** decisions.

* 中 从“有没有”转为“卖得快不快”，真正实现**周转优先**的库存决策。


---

### **2\. Store Clustering – Dimension Completeness**

* **Requirement / 需求**

  * *EN*: Input features must include **store style** & **rack capacity / display class**.

  * *中*: 聚类输入特征必须包含 **门店风格** 与 **陈列容量/高低架分类**。

* **Where We Were / 之前状态**

  * *EN*: Only climate captured; style & capacity missing.

  * *中*: 仅使用温区，缺少风格与容量维度。

* **Where We Are Now / 当前状态**

* #### **Where We Are Now / 当前状态**

* Fill the progress boxes (✓ / ✗) and add evidence links or dates as you close gaps.

| Dimension | Present? | Notes |
| ----- | ----- | ----- |
| **Product-level style tags** (season, gender, display location, big / sub class) | ✓ | Extracted in **Step 1**; used in business-rule analysis. |
| **Enhanced climate data** (store GPS \+ “feels-like” temp) | ✓ | Temp-aware clustering in **Step 6** (≤ 5 °C bands). |
| **Store style profile** (Basic vs Fashion, aesthetic, demographic) | ✗ | Still inferred from past sales; no explicit tag yet. |
| **Rack capacity / display class** (fixture count, space limits) | ✗ | Quantities not checked against physical space. |


---

### **3\. Store Clustering – Business Interpretability**

* **Requirement / 需求**

  * *EN*: Provide plain-language **store-group profile report**, silhouette ≥ 0.5, and temperature-zone label.

  * *中*: 需提供易读的 **门店群画像报告**，核心簇 Silhouette≥0.5，并输出温区标签。

* **Where We Were / 之前状态**

  * *EN*: No profile deck; silhouette \< 0.5; labels absent.

  * *中*: 无画像报告，Silhouette＜0.5，缺少温区标签。

* **Where We Are Now / 当前状态**

  #### **Where We Were / 之前状态**

* **EN** No profiles, no silhouette metric, no temperature context.

* **中** 无画像报告、无 Silhouette 指标、无温区信息。

#### 

Tick ✓ / ⚠ / ✗ and add evidence or date as you progress.

| Item | Status | Notes (简要说明) |
| ----- | ----- | ----- |
| Plain-language store-group profile | ✗ / ⚠ / ✓ | *EN* Technical doc only; needs business narrative. *中* 仅技术文档，缺商业语言。 |
| Silhouette ≥ 0.50 | ✗ / ⚠ / ✓ | *EN* Metric calculated, but current score \< 0.50. *中* 已计算，但得分低于 0.50。 |
| Temperature-zone label | ✗ / ⚠ / ✓ | *EN* Implemented with “15-20 °C” etc. *中* 已实现温区标签（如 15-20 °C）。 |

* 

---

### **4\. Product Analysis – Supply-Demand Gap**

* **Requirement / 需求**

  * *EN*: Gap analysis for ≥ 3 representative store-groups across category, display, season, gender, price-band, style…

  * *中*: 针对 ≥3 个代表性店群，按大/小类、陈列、季节、性别、价格带、风格等维度做供需差距分析。

* **Where We Were / 之前状态**

  * *EN*: Only high-level price-band chart; no cluster × role matrix.

  * *中*: 仅有价格带概览，未做店群×商品角色矩阵。

* **Where We Are Now / 当前状态**

  #### **Where We Were / 之前状态**

* **EN** Only surface-level cluster profiling; no systematic gap detection or executive report.

* **中** 仅有基础簇画像，无系统化缺口识别，也无面向业务的报告。

  ---

  #### **Where We Are Now / 当前状态**

Update the ❑ / ⚠ / ✓ symbols and add links or dates as progress is made.

| Dimension to check | Status | Notes (简要说明) |
| ----- | ----- | ----- |
| **Representative-cluster selection (≥ 3\)** | ❑ | No algorithm to pick “most distinct” clusters. |
| **Category coverage** | ❑ | Missing list of present vs. absent categories. |
| **Display-location coverage** | ❑ | No front-desk / back-area adequacy check. |
| **Season & gender balance** | ❑ | No over/under-representation analysis. |
| **Price-band analysis** | ❑ | No premium / mid / budget breakdown. |
| **Style diversity metrics** | ❑ | No measure of style variety. |
| **Executive gap report** | ❑ | No plain-language summary or visuals. |
| **Foundations in place** | ✓ | Clusters exist; product style tags captured; rule-level “sales gap” field in code. |

---

### **5\. Allocation Logic – True Optimisation**

* **Requirement / 需求**

  * *EN*: Use constraint-aware optimiser (e.g., MILP); live “what-if” demo when constraints change.

  * *中*: 必须采用约束优化算法（如 MILP），并演示约束变化时的实时“情景模拟”。

* **Where We Were / 之前状态**

  * *EN*: Rule-based weights only; no optimiser; no demo.

  * *中*: 仅靠规则权重，没有优化器，也无情景演示。

* **Where We Are Now / 当前状态**  
* **EN** Six sequential **rule-based** checks (missing category, z-score imbalance, etc.); no objective function, no solver, no what-if capability.

* **中** 仅靠 6 条 **规则顺序处理**（缺品类、Z 分值失衡等）；无目标函数、无求解器、无情景模拟。

Mark each line ✓ 已完成, ⚠ 部分完成, ✗ 未开始；旁边可附日期或证据链接。

* Objective function to maximise sell-through …… ✗

* Capacity / lifecycle / budget constraints encoded …… ✗

* Optimisation solver integrated (MILP / LP / heuristics) …… ✗

* Global allocation solved in one pass …… ✗

* Live “what-if” re-optimisation demo …… ✗

##### **Impact / 影响**

* **EN** Allocations are still threshold tweaks, not true optimisation—risk of over-stocking, under-stocking, and missed profit.

* **中** 当前仍为阈值式调整，非真正优化―易造成过/欠配与利润流失。

---

### **6\. System Output – Usable Format & Content**

* **Requirement / 需求**

  * *EN*: Output must include timing (Y/M/Half-Month), store-group ID, product-tag combo, **integer** SPU qty per store, plus meta fields.

  * *中*: 输出文件须含推荐时点（年/月/上下旬）、店群ID、标签组合、**整数**SPU数量（分配到店），及元信息字段。

* **Where We Were / 之前状态**

  * *EN*: Timing seasonal only; quantities not integer; store list missing.

  * *中*: 仅季节粒度；数量为浮点；缺少门店清单。

* **Where We Are Now / 当前状态** 

#### **Where We Were / 之前状态**

* **EN** Only cluster-level CSV; no store-level allocations; product tags in one concatenated string; minimal metadata.

* **中** 仅输出店群汇总；无门店级配额；商品标签为一串文本；元数据缺失。

---

#### **Where We Are Now / 当前状态**

Mark each line ✓ 已完成 | ⚠ 部分 | ✗ 未做，并在旁边加日期 / 证据链接。

| Output component | Status | Notes (简要说明) |
| ----- | ----- | ----- |
| **Timing** (Y/M/Period) | ✓ | Year-Month-Period present; clustering-date still missing. |
| **Store-group ID \+ explicit store list** | ✗ | Only “Cluster\_0”; no “STR001, STR002 …”. |
| **Store-level integer quantities** | ✗ | Quantities aggregated at cluster level. |
| **Structured product tags (separate cols)** | ⚠ | Tags captured but still concatenated “夏-中-前台-上装-T恤”. |
| **Full metadata (valid-until, sell-through %)** | ✗ | Basic Year/Month only; lifecycle fields absent. |
| **Bilingual headers & styling** | ✓ | Excel output has CN/EN headers, multi-sheet format. |

---

## **PART B · Delivery Gap Analysis (Milestone-1)**

*(阶段差异 — 使用 Fast Fish 评估语言)*

### **① Alignment with Core Objective & KPI**

* **Task / 任务**

  * Align all logic and reports to sell-through KPI.

  * 所有模型与报告需对齐售罄率 KPI。

* **Before / 之前**

  * Sell-through not optimised; flagged “⚠ Mis-aligned”.

  * 未优化售罄率，被标记“⚠未对齐”。

* **Now / 当前**  
  **Step 18 · Sell-Through Analysis**

  * **EN** Calculates SPU-store-day inventory & sales → writes three columns (`Inventory_Days`, `Sales_Days`, `Sell_Through_Rate`) into every recommendation; highlights top / bottom performers.

  * **中** 计算 SKU-店-天 库存与销量，生成三列 turnover 指标；自动标记售罄率最高 / 最低的商品。

**Contains Sell-Through, but Doesn’t Drive Decisions**

* **Enhanced Fast Fish CSV / Excel**

  * **EN** `Historical_ST%` already exported, yet sort / filter logic still powered by revenue gaps, Z-scores, etc.

  * **中** `Historical_ST%` 字段已输出，但排序与筛选仍以销售额、Z 分值为主。

  * **Next step / 下一步** Raise the weight of `Sell_Through_Rate` in ranking rules.

**Rules & Modules That Must Be Retargeted (keep the rule, change the KPI)**

1. **Rule 7 · Missing Category / 缺品类**

   * **Current KPI** revenue gap.

   * **改造** only recommend products that lift predicted sell-through.

2. **Rule 8 · Imbalanced Allocation / 配额失衡**

   * **Current KPI** Z-score balance.

   * **改造** rebalance *only if* it raises post-adjustment sell-through.

3. **Rule 9 · Below Minimum / 低于最低存量**

   * **Current KPI** coverage.

   * **改造** top-up inventory **when** model shows turnover will improve.

4. **Rule 10 · Over-capacity / 超容量**

   * **Current KPI** capacity utilisation.

   * **改造** cut stock that drags sell-through below target, not just capacity %.

5. **Rule 11 · Missed Sales / 错失销售**

   * **Current KPI** revenue opportunity.

   * **改造** add items only if they speed up turnover.

6. **Rule 12 · Sales Performance / 业绩差距**

   * **Current KPI** sales vs. top quartile.

   * **改造** chase **sell-through gap** instead of sales gap.

**Clustering engine / 聚类引擎** currently temperature-led (neutral). Optional upgrade: add historical sell-through as an extra feature so “fast-turn stores” group together.

**Illustrative Comparison**

* **Current logic** Store A sells ¥1 k @ 50 % ST%, Store B sells ¥2 k @ 20 % ST% → Rule 12 thinks A “under-performs” and sends *more* stock there.

* **Sell-through logic** same data → send more stock to **Store A** because its turnover is faster.

**Priority Actions (双语)**

1. **Unified objective function**

   * **EN** `max Predicted_Sell_Through_Rate` shared by every rule.

   * **中** 所有规则统一调用 `max 预测售罄率` 目标函数。

2. **Common prediction module** for Δ sell-through.

3. **Dashboard & reports** show only sell-through uplift, inventory-days saved.

---

### **② Data Input & Structure Design – Store Attributes**

* **Task / 任务**

  * Full coverage of climate, style, capacity in dataset.

  * 数据需完整覆盖温区、风格、容量。

* **Before / 之前**

  * Climate OK; style & capacity missing → “⚠ Cluster dimension gap”.

  * 温区已覆盖，风格/容量缺失 → “⚠ 聚类维度缺口”。

### **Now / 当前** 

### **Store-Attribute Dimensions – Climate · Style · Capacity**

*(English / 简体中文并排，可直接用于文档或幻灯片)*

**Requirement / 需求**

* **EN** Clustering & rules need **three store-level dimensions**:

  1. Climate / temperature zone

  2. **Store type / style** (Fashion / Basic / Balanced)

  3. **Store capacity / size** (floor area, rack count, size tier)

* **中** 聚类与业务规则必须含 **三大门店维度**：

  1. 气候温区

  2. **门店类型 / 风格**（时尚 / 基础 / 混合）

  3. **门店容量 / 规模**（面积、货架数、级别）

**Current Coverage Snapshot**

| Dimension | Status | What’s in place / 已实现 | Critical gaps / 缺口 |
| ----- | ----- | ----- | ----- |
| **Climate / Temperature** | ✅ 完成 | • 5 °C “feels-like” bands• Label examples “20 – 25 °C”• Temp-aware clustering constraint | — |
| **Store type / Style** | ❌ 缺失 | — | • 无显式字段：Fashion / Basic / Balanced• 仅在 Step 13 临时计算比例，未写入属性  |
| **Capacity / Size** | ❌ 缺失 | — | • 无 floor area、rack\_capacity、size\_tier• 规则未考虑实际陈列空间 |
| **Cluster-level roll-up** | ⚠ 部分 | • Temp zone aggregated | • 未汇总 dominant store-type & capacity tier |

#### **Impact / 影响**

* **EN** Without style & capacity, clusters ignore real store differences; rules may push products that don’t fit the shop floor.

* **中** 缺少风格与容量，聚类无法体现门店差异；配货可能超出实际陈列空间或违背店铺定位。

**Road-map / 实施路线**

1. **Store-type classification** (High)

   * Extract fashion/basic ratios → tag **FASHION / BASIC / BALANCED**.

   * Persist in store table; add to clustering features & rules.

2. **Capacity estimation** (High)

   * Build size tiers (Small / Medium / Large) from sales \+ SKU breadth or fixture data.

   * Add capacity checks to allocation logic.

3. **Cluster roll-up enhancement** (Medium)

   * Aggregate dominant type, average size tier, total capacity per cluster.

   * Include in profile reports & recommendation rationale.

**Overall coverage** 1 / 3 dimensions ready → **33 %** complete.  
 **Goal** All three dimensions fully captured and used in clustering *and* business rules to unlock context-aware, capacity-safe recommendations.

###  

---

### **③ Output Design – Optimisation Target Visibility**

* **Task / 任务**

  * Ensure outputs clearly reflect sell-through optimisation under constraints.

  * 输出需清晰体现在约束下最大化售罄率。

* **Before / 之前**

  * Rule-logic dominated; optimisation target absent.

  * 以规则为主，缺少优化目标。

### **Now / 当前** 

* ### **EN Rationale talked about “optimised performance” but only cited sales revenue, not sell-through. No constraint fields, no turnover metrics up front.** 

* ### **中 理由文本提到“优化表现”，却只用销售额衡量；缺少任何约束字段，也未突出周转指标。** 

### ---

#### **Where We Are Now / 当前状态**

### **Tick ✓ 完成 ⚠ 部分 ✗ 未做；在旁写日期 / 链接。**

| Output element | Status | What still needs doing / 待补内容 |
| ----- | ----- | ----- |
| **Explicit optimisation target field** | **✗** | **Add column `Optimization_Target = "Maximize Sell-Through Rate Under Constraints"`** |
| **Sell-through metrics first (current, target, Δ)** | **✗** | **Replace revenue columns as primary KPI** |
| **Constraint visibility (capacity %, store-type, climate)** | **✗** | **Columns: `Capacity_Utilization`, `Store_Type_Alignment`, `Temperature_Suitability`, `Constraint_Status`** |
| **Transparent rationale (why turnover improves)** | **✗** | **e.g. “ST% 68.5 → 85.2 (+16.7 pp) ; constraints OK”** |
| **Trade-off & confidence score** | **✗** | **Show benefit vs. risk \+ prediction confidence** |

### **Legend ✓ \= Done ⚠ \= Partial ✗ \= Not yet**

##### **Impact / 影响**

* ### **EN Until these fields exist, downstream users cannot see what is being optimised or why a recommendation is safe to act on.** 

* ### **中 缺少这些字段，业务方无法直观看到“优化了什么”及“是否符合约束”，难以放心执行。** 

### **Next Steps / 下一步**

1. ### **Rewrite output builder → insert optimisation target, sell-through KPI set, constraint status.** 

2. ### **Promote sell-through columns to top of Excel / CSV, demote revenue figures to support role.** 

3. ### **Generate confidence & trade-off fields using existing prediction error stats.** 

### **Adopting this enhanced format will turn the outputs into a transparent, trust-worthy feed that clearly shows how each recommendation improves inventory turnover while respecting real-world limits.**

### ---

### **④ Clustering Key Requirements**

* **a. Style Validation / 风格验证** — Now: In progress 

* **b. Capacity Consideration / 容量维度纳入** — Now: In progress  
* **c. Dynamic Clustering / 动态聚类机制** — Now:  DONE- seasonal clustering 

---

### **⑤  Product Structure Optimisation Module**

#### **Requirement / 需求**

### The module must deliver **three capabilities**:

1. ### **Cluster × Role Gap Analysis** – 店群 × 商品角色供需缺口 

2. ### **Price-Band & Substitution Analysis** – 价格带 & 替代性分析 

3. ### **What-If Scenario Simulation** – 情景模拟与敏感性分析 

### ---

#### **Where We Are Now / 当前状态**

| Capability | Status | Comment (简要说明) |
| ----- | ----- | ----- |
| Cluster × Role Gap | ✗ | 无商品角色定义，无供需矩阵。 |
| Price-Band & Substitution | ✗ | 未分价格带，无交叉替代弹性模型。 |
| What-If Scenario | ✗ | 无“若…则…”模拟框架；无法评估约束改变。 |

###   

---

### **⑥Store-Merchandise Matching & Allocation Optimisation**

* **a. Dynamic timing / 动态时机** — Now: \_\_\_\_\_\_\_\_\_\_

* **b. Lifecycle forecasting / 生命周期预测** — Now: \_\_\_\_\_\_\_\_\_\_

* **c. Role-specific strategy / 角色差异策略** — Now: \_\_\_\_\_\_\_\_\_\_

* **d. Optimisation under constraints / 约束下最优解** — Now: \_\_\_\_\_\_\_\_\_\_

#### **Requirement / 需求**

1. **Dynamic allocation & timing** – 动态配货与时机判断

2. **Time-series & lifecycle analysis** – 时间序列与生命周期分析

3. **Role- & lifecycle-aware strategies** – 商品角色 / 生命周期差异化策略

4. **Mathematical optimisation under constraints** – 约束下的最优解

---

#### **Current Coverage Snapshot**

| Module | Status | What exists / 已实现 | Major gaps / 主要缺口 |
| ----- | ----- | ----- | ----- |
| Dynamic allocation \+ timing | ⚠ 30 % | • 15-day fixed periods • Season tag in clustering | • 无动态算法 • 无最优时机模型 • 无实时回调 |
| Time-series / lifecycle | ✗ 15 % | • 简单同比分析 | • 无预测模型 • 无生命周期分段 |
| Role \+ lifecycle strategy | ✗ 5 % | • 品类 / 子类标签 | • 无 CORE / SEASONAL 等角色 • 策略一刀切 |
| Optimisation under constraints | ✗ 10 % | • 6 条 if-then 规则 • 温区硬约束 | • 无 MILP / LP 求解器 • 无多目标优化 |

### 

---

### **⑦** 

---

### **⑧ Deliverables Quality & Scoring (D-A … D-H)**

### ***Deliverables Quality Snapshot***

*(English / 简体中文)*

***D-A · Seasonal Cluster Snapshot***

* ***Status** ✅ Implemented | 已实现*

* ***Score** 7 / 10*

* ***Key gap** Add capacity & store-style attributes.*

* ***关键缺口** 补充容量与店铺风格维度。*

***D-B · Cluster Descriptor Dictionary***

* ***Status** ✅ Implemented | 已实现*

* ***Score** 6 / 10*

* ***Key gap** Descriptors are technical; need richer business context.*

* ***关键缺口** 描述偏技术，缺乏业务化语言。*

***D-C · Cluster Stability Report***

* ***Status** ❌ Missing | 未实现*

* ***Score** 2 / 10*

* ***Key gap** No temporal-consistency or robustness analysis.*

* ***关键缺口** 缺少时序稳定性与稳健性评估。*

***D-D · Back-Test Evaluation (sell-through KPI)***

* ***Status** ⚠ Partially | 部分完成*

* ***Score** 5 / 10*

* ***Key gap** Sell-through metric exists, but no systematic back-test.*

* ***关键缺口** 有售罄指标，无完整回测框架。*

***D-E · Target-SPU Suggestion (sell-through focus)***

* ***Status** ⚠ Partially | 部分完成*

* ***Score** 4 / 10*

* ***Key gap** Rule-based; needs optimisation engine tied to sell-through.*

* ***关键缺口** 基于规则，缺少卖向售罄的优化模型。*

***D-F · Tag Suggestion Table***

* ***Status** ✅ Implemented | 已实现*

* ***Score** 8 / 10*

* ***Key gap** Minor: could link tags to role / lifecycle insights.*

* ***关键缺口** 可进一步关联商品角色与生命周期。*

***D-G · Baseline Logic & Auto-Weights***

* ***Status** ❌ Missing | 未实现*

* ***Score** 3 / 10*

* ***Key gap** Weights are hard-coded; need auto-weight baseline logic.*

* ***关键缺口** 权重手动设置，缺少自动基线算法。*

***D-H · Interactive Dashboard***

* ***Status** ❌ Missing | 未实现*

* ***Score** 2 / 10*

* ***Key gap** Only static reports; no real-time visualisation.*

* ***关键缺口** 仅静态报告，无实时可视化仪表盘。*

  ---

  #### ***Critical Gaps to Address First***

*(score \< 5 / 得分低于 5 的优先补缺)*

* ***Cluster Stability Report (D-C)** – build robustness & temporal-drift analysis.*

* ***Target-SPU Optimisation (D-E)** – add sell-through–driven optimisation model.*

* ***Baseline Auto-Weights (D-G)** – implement automatic weighting framework.*

* ***Interactive Dashboard (D-H)** – develop live KPI & constraint visualisation.*

*Addressing these items will lift overall deliverable quality from **“work-in-progress” to “contract-ready.”***

* 

---

### **9\. *Evidence Package***

* *Logic & algorithm docs*

* *Feature-importance / clustering comparison visuals*

* *Store-group profile deck with metrics*

* *Gap-analysis workbook*

* *Live optimisation demo recording*

* *Example output file \+ specification*

TASKLIST \- minimal 

## **0 · Governance & Prep**

* **Task 0-1 Sign-off “Fix-Road-Map”**

  * *Why* freeze scope, dates, owners.

  * *Input* this checklist; Fast Fish comments.

  * *Done-when* PDF signed by both PMs.

---

## **1 · Data \+ Store-Attribute Enrichment**

| ID | Task | Why | Owner | Input | Done-when |
| ----- | ----- | ----- | ----- | ----- | ----- |
| 1-1 | Add **store\_type / style** column (Fashion / Basic / Balanced) | Required feature for clustering & rules | \_\_\_ | Step 13 ratios | New field in `stores.csv` |
| 1-2 | Add **rack\_capacity / size\_tier** columns | Capacity constraints | \_\_\_ | Fixture counts OR sales-SKU proxy | Capacity table merged |
| 1-3 | Update **clustering feature list** to include 1-1 & 1-2 | Dimension completeness | \_\_\_ | Tasks 1-1, 1-2 | YAML / JSON config updated |
| 1-4 | Refresh **temp-aware clustering** with new features | Higher silhouette | \_\_\_ | Task 1-3 | Silhouette ≥ 0.50 logged |

---

## **2 · Clustering Interpretability**

| ID | Task | Done-when |
| ----- | ----- | ----- |
| 2-1 | Generate **plain-language store-group deck** (one slide / cluster) | PPT with name, style, capacity, temp, top SKUs |
| 2-2 | Write **auto silhouette report** to `/output/cluster_stability.csv` | Metric \> 0.50; red-flag if \< 0.40 |
| 2-3 | Build **stability script** (same clusters vs. last run) | Jupyter notebook with drift % |

---

## **3 · Product-Structure Optimisation Module**

| ID | Task | Done-when |
| ----- | ----- | ----- |
| 3-1 | Code **product role classifier** (CORE / SEASONAL / FILLER / CLEARANCE) | Column `product_role` in SKU table |
| 3-2 | Build **Cluster × Role Gap Matrix** | `gap_matrix.xlsx` auto-colour gaps \> 10 % |
| 3-3 | Implement **price-band classifier** \+ substitution-elasticity calc | `price_band` & `elasticity` fields saved |
| 3-4 | Create **What-If Scenario Analyzer** class | Returns Δ ST%, revenue, inventory |

---

## **4 · Allocation Optimiser (critical path)**

| ID | Task | Done-when |
| ----- | ----- | ----- |
| 4-1 | Draft **MILP formulation** (objective \= max predicted ST%) | Markdown spec reviewed |
| 4-2 | Encode **constraints** (capacity, budget, lifecycle, climate) | Unit tests pass |
| 4-3 | Integrate **solver (PuLP / OR-Tools)** into pipeline | `optimal_allocation.csv` produced |
| 4-4 | Build **live “what-if” API** (change constraint → re-solve) | Demo video \< 2 min |

---

## **5 · Output Redesign**

| ID | Task | Done-when |
| ----- | ----- | ----- |
| 5-1 | Add column `Optimization_Target` (= “Max ST Rate Under Constraints”) | Shown in CSV header |
| 5-2 | Promote `Current_ST% / Target_ST% / Δ` to top of file | Columns A-C |
| 5-3 | Append **constraint fields** `Capacity_Utilization`, `Store_Type_Alignment`, `Temp_Suitability`, `Constraint_Status` | Values populated |
| 5-4 | Add **confidence\_score & trade\_off** columns | Calculated via historical error |
| 5-5 | Update Excel/CSV exporter & unit tests | CI passes; sample file attached |

---

## **6 · Baseline Auto-Weights & Back-Testing**

| ID | Task | Done-when |
| ----- | ----- | ----- |
| 6-1 | Build **auto-weight learner** (e.g., ridge regression on past ST%) | YAML of learned weights saved |
| 6-2 | Develop **back-test harness** (train / test split, KPI chart) | HTML report with ST uplift curve |

---

## **7 · Interactive Dashboard**

| ID | Task | Done-when |
| ----- | ----- | ----- |
| 7-1 | Choose stack (Plotly Dash / Streamlit) | Tech note approved |
| 7-2 | Build KPI cards (overall ST%, gap count, inventory-at-risk) | Dashboard live on staging URL |
| 7-3 | Add slicers (cluster, role, price band) \+ what-if panel | Live filter works \< 1 s |

---

## **8 · Documentation & Evidence Package**

* **8-1 Logic & code docs** → `/docs/algorithms.md`

* **8-2 Cluster comparison visuals** → `/output/cluster_vis/*.png`

* **8-3 Gap-analysis workbook** (template above)

* **8-4 Optimiser demo recording** (`.mp4`)

* **8-5 Sample output \+ spec** → `/deliverables/output_spec_v2.xlsx`

---

### **Suggested Timeline (high-level)**

| Phase | Sprint 1 | Sprint 2 | Sprint 3 |
| ----- | ----- | ----- | ----- |
| Data & clustering (Tasks 1–2) | ✓ |  |  |
| Product module (Tasks 3-1 → 3-3) | ✓ | ✓ |  |
| Optimiser core (4-1 → 4-3) |  | ✓ | ✓ |
| Output redesign & back-test (5-1 → 5-5, 6-1 → 6-2) |  |  | ✓ |
| Dashboard & docs (7-1 → 7-3, 8-\*) |  |  | ✓ |

