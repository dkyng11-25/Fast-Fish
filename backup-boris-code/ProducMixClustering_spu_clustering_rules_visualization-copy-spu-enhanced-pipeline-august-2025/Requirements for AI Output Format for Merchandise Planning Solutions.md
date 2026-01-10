**Subject: Requirements for AI Output Format for Merchandise Planning
Solutions**

To ensure seamless integration with our business operations, please
adhere to the following requirements for the merchandise planning
solutions output by your AI system.

**1. Time Horizon Requirement**

Our business units finalize the merchandise allocation plans **one full
month in advance**. Therefore, it is crucial that the AI system provides
style and quantity recommendations for the period that is **one month
beyond the upcoming month**.

- **Illustrative Example:**

  - If the current date is in the **second half of June (6B)**, our
    merchandise development and purchase orders for July have already
    been mostly completed and can only be slightly adjusted.

  - Consequently, our most urgent need is for the merchandise plan for
    the **first half of August (8A) and the second half of August
    (8B)**. This allows us to initiate the development and procurement
    process for August merchandise in a timely manner.

**2. Data Output Format Requirement**

Please ensure the output data strictly conforms to the following table
structure to allow for automated parsing by our systems.

| **Year (YYYY)** | **Month (MM)** | **Period (A/B)** | **Store Group Name** | **Target Style Tags (Combination)**                           | **Target SPU Quantity** |
|-----------------|----------------|------------------|----------------------|---------------------------------------------------------------|-------------------------|
| **Example:**    |                |                  |                      |                                                               |                         |
| 2025            | 08             | A                | Store Group 1        | \[Summer, Women, Back-of-store, Casual Pants, Cargo Pants\]   | 6                       |
| 2025            | 08             | B                | Store Group 1        | \[Summer, Women, Back-of-store, Casual Pants, Tapered Pants\] | 4                       |
| \...            | \...           | \...             | \...                 | \...                                                          | \...                    |

**Key Summary Points:**

1.  **Output Timing Logic:** The timeframe for the output data should be
    the **current period + 2 half-month cycles**. (e.g., A request made
    in the first half of June should yield data for the first half of
    August).

2.  **Target Style Tags:** This field should be a combination of
    multiple tags. Please enclose the entire set of tags in square
    brackets \[ \].

3.  **Data Consistency:** Please ensure the data type and format for
    each field are strictly consistent with the provided example.

Should you have any questions, please do not hesitate to contact us.
