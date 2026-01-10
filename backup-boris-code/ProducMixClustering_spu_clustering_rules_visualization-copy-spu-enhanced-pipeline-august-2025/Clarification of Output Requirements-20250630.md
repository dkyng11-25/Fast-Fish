**Clarification of Output Requirements: Aggregate Store Group
Merchandise Planning by Style_Tags**

Thank you for providing the sample of the store merchandise planning
results. After analyzing the file, we found that the current results
still focus on inventory adjustment recommendations at the individual
SPU_Code (SKU) level. This differs significantly from our actual
business needs. Please adjust the output direction as follows:

**1. Key Requirement**

We do **not** need inventory adjustments at the SKU level. Instead, we
require the output to be **at the "Store Group + Style_Tags combination"
level**, specifying the **target number of SPU_Codes** (SKUs) to be
allocated for each combination. In other words, for each product
combination label (for example: \[Summer, Women, Back-of-store, Casual
Pants, Cargo Pants\]), the output should show how many SPU_Codes should
be allocated as the configuration target for each store group.

**2. Core Principles for Data Aggregation**

- **Aggregation Dimension**: Please aggregate and output the **target
  > SPU quantity by "Store Group + Style_Tags combination"**.

- **Quantity aggregation is not a simple sum or subtraction**. The
  > recommended target SPU quantity for each combination should be
  > determined **based on historical sales performance, business
  > strategies, and actual operational needs**.

  - For SPU_Codes with strong sales performance, please consider
    > **increasing** the target SPU quantity under the corresponding
    > Style_Tags combination.

  - For SPU_Codes with average or weaker sales performance, please
    > consider **reducing** the target SPU quantity under the
    > corresponding combination.

- Note that this "increase" or "decrease" should **not** be a mechanical
  > +1/-1 per SKU, but should be the result of comprehensive evaluation
  > of sales contribution, business rules, and professional judgment,
  > arriving at a final, reasonable target SPU quantity for each Store
  > Group + Style_Tags combination.

- **Final Objective**: For each "Store Group + Style_Tags combination +
  > period", output a single, aggregated and actionable target SPU
  > quantity, **not SKU-level recommendations**.

**3. Output Data Format and Example (Strictly Required)**

| **Year** | **Month** | **Period (A/B)** | **Store Group Name** | **Target Style Tags (Combination)**                         | **Target SPU Quantity** |
|----------|-----------|------------------|----------------------|-------------------------------------------------------------|-------------------------|
| 2025     | 08        | A                | Store Group 1        | \[Summer, Women, Back-of-store, Casual Pants, Cargo Pants\] | 6                       |

- The "Target Style Tags" field **must be enclosed in English square
  > brackets \[ \]**, and include the full label combination.

- **Each row** should represent a single "Store Group + half-month +
  > Style_Tags combination" target. **No SKU fields are required**.

- All fields, data types, and formats **must strictly follow** this
  > template.
