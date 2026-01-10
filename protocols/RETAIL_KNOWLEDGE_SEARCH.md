# Retail Knowledge Search Protocol

**Depth Level:** 1 (Meta-thinking)  
**Last Updated:** 2025-01-05  
**References:** FAST_FISH_THINKING_STRATEGY.md, PERSPECTIVES_NEEDED.md

---

## Purpose

Define HOW we systematically recall and apply retail optimization knowledge when working on Fast Fish pipeline steps. This protocol ensures we leverage domain expertise effectively.

---

## Relevant Knowledge Domains

### 1. **Retail Science & Category Management**

**Why Relevant:**
- Core domain for product mix optimization
- Provides frameworks for assortment planning
- Guides sell-through optimization strategies

**Key Concepts:**
- **Assortment Breadth:** Number of different product types (SPUs) in a category
- **Assortment Depth:** Quantity of each product type available
- **Sell-Through Rate:** Percentage of inventory sold in a period
- **Category Performance:** Revenue and margin contribution by category
- **Store Clustering:** Grouping similar stores for coordinated strategy

**Knowledge Recall Prompts:**
- "What retail principles apply to this assortment decision?"
- "How do successful retailers optimize sell-through?"
- "What category management frameworks are relevant?"
- "How do store clusters affect merchandise planning?"

---

### 2. **Fast Fish Business Model**

**Why Relevant:**
- Specific business context for all decisions
- Defines constraints and objectives
- Provides real data foundation

**Key Concepts:**
- **Store Groups:** 46 groups with 50-53 stores each
- **Product Categories:** 126 categories with individual optimization
- **Time Periods:** 15-day periods (Period A/B per month)
- **Core KPI:** Sell-through rate optimization
- **Uniform Assortment:** Same product mix within store groups

**Knowledge Recall Prompts:**
- "How does Fast Fish's store group model work?"
- "What are Fast Fish's primary business objectives?"
- "What constraints does Fast Fish's business model impose?"
- "How does Fast Fish measure success?"

---

### 3. **Pipeline Architecture**

**Why Relevant:**
- Technical foundation for implementation
- Defines step structure and patterns
- Guides code organization

**Key Concepts:**
- **36-Step Pipeline:** Complete data processing workflow
- **5 Main Phases:** Data Collection → Weather → Clustering → Business Rules → Visualization
- **4-Phase Step Pattern:** setup → apply → validate → persist
- **Repository Pattern:** Data access abstraction
- **Dependency Injection:** Flexible component wiring

**Knowledge Recall Prompts:**
- "What pipeline step handles this functionality?"
- "How should this step be structured?"
- "What repositories are needed for this step?"
- "How does this step connect to others?"

---

### 4. **Business Rules (Steps 7-12)**

**Why Relevant:**
- Core optimization logic
- Identifies improvement opportunities
- Drives recommendations

**Key Concepts:**
- **Rule 7 - Missing Categories:** Identifies stores missing high-performing categories
- **Rule 8 - Imbalanced Allocation:** Detects over/under-allocated products
- **Rule 9 - Below Minimum:** Finds categories below threshold levels
- **Rule 10 - Smart Overcapacity:** Identifies overcapacity opportunities
- **Rule 11 - Missed Sales:** Detects missed sales opportunities
- **Rule 12 - Sales Performance:** Analyzes performance gaps

**Knowledge Recall Prompts:**
- "Which business rule applies to this scenario?"
- "What optimization opportunity does this rule identify?"
- "How do we measure rule effectiveness?"
- "What actions should result from this rule?"

---

### 5. **Weather & Climate Integration**

**Why Relevant:**
- Affects product demand patterns
- Drives store clustering decisions
- Enables seasonal optimization

**Key Concepts:**
- **Feels-Like Temperature:** Perceived temperature for product demand
- **Temperature Bands:** Climate-based store groupings
- **Seasonal Patterns:** Summer/Winter product demand shifts
- **Weather Data Integration:** API-based weather data collection

**Knowledge Recall Prompts:**
- "How does weather affect product demand?"
- "What temperature bands are relevant for clustering?"
- "How should seasonal patterns influence assortment?"
- "What weather data is needed for this analysis?"

---

### 6. **Mathematical Optimization**

**Why Relevant:**
- Replaces rule-based approaches
- Maximizes sell-through under constraints
- Provides rigorous decision framework

**Key Concepts:**
- **Objective Function:** Maximize sell-through rate
- **Capacity Constraints:** Store fixture and shelf limits
- **Lifecycle Constraints:** Product introduction/growth/mature stages
- **Price-Band Constraints:** Price tier considerations
- **Supply-Demand Gap:** Difference between supply and demand

**Knowledge Recall Prompts:**
- "What is the optimization objective for this decision?"
- "What constraints must be satisfied?"
- "How do we formulate this as an optimization problem?"
- "What trade-offs exist in this optimization?"

---

## Expert Simulation Protocol

### When to Simulate Experts

1. **Before major decisions** - Get multiple perspectives
2. **When stuck** - Fresh viewpoints can unlock progress
3. **During validation** - Verify approach from different angles
4. **After implementation** - Evaluate effectiveness

### Expert Simulation Templates

#### Retail Strategist Simulation
```
"I am a retail strategist with 15 years of experience.
Looking at this problem: [problem description]

As a retail strategist, I would:
- First consider the business impact...
- Then evaluate the customer experience...
- The key success metrics are...
- My recommendation would be...
- The risks to watch for are..."
```

#### Data Scientist Simulation
```
"I am a data scientist specializing in retail analytics.
Looking at this data: [data description]

As a data scientist, I would:
- First examine the data quality...
- Then identify patterns and correlations...
- The statistical approach should be...
- The validation method would be...
- The confidence level is..."
```

#### Operations Researcher Simulation
```
"I am an operations research expert.
Looking at this optimization problem: [problem description]

As an OR expert, I would:
- Formulate the objective function as...
- Define the constraints as...
- The optimization approach should be...
- The expected solution quality is...
- The computational considerations are..."
```

---

## Knowledge Recall Procedures

### Procedure 1: Conceptual Knowledge Recall

**When to Use:** Understanding fundamental concepts

```
Prompt: "What do I know about [concept]?

Let me recall:
- Fundamental principles...
- Key theories...
- Important distinctions...
- Common misconceptions...
- Related concepts..."
```

### Procedure 2: Pattern Knowledge Recall

**When to Use:** Finding similar problems and solutions

```
Prompt: "What similar problems have been solved?

Let me think of analogous situations:
- In retail optimization, similar problems include...
- In data science, analogous patterns are...
- The common structure across these is...
- The successful approaches were...
- The failures taught us..."
```

### Procedure 3: Procedural Knowledge Recall

**When to Use:** Implementing solutions

```
Prompt: "What frameworks and methodologies exist for [problem type]?

Let me recall established approaches:
- Framework 1: [Description, when to use]
- Framework 2: [Description, when to use]
- Methodology 1: [Description, strengths/weaknesses]
- Best practices: [List]
- Common pitfalls: [List]"
```

### Procedure 4: Cautionary Knowledge Recall

**When to Use:** Avoiding mistakes

```
Prompt: "What mistakes are common when solving [problem type]?

Let me recall warnings:
- Mistake 1: [Description, why it happens, how to avoid]
- Mistake 2: [Description, why it happens, how to avoid]
- Dangerous assumptions: [List]
- Red flags to watch for: [List]"
```

---

## Knowledge Gaps

### Known Gaps in Current System

1. **Store Capacity Data:** Missing fixture count and shelf space data
2. **Style Validation:** No confidence scores for style labels
3. **Lifecycle States:** Missing product lifecycle classification
4. **Price-Band Effects:** Limited substitution effect analysis

### How to Address Gaps

1. **Acquire missing data** - Work with Fast Fish to obtain
2. **Implement proxies** - Use available data as approximations
3. **Document assumptions** - Be explicit about limitations
4. **Plan for future** - Design for data availability improvements

---

## Knowledge Application Checklist

Before making major decisions, verify:

### Domain Knowledge
- [ ] Retail principles considered
- [ ] Fast Fish business model understood
- [ ] Pipeline architecture followed
- [ ] Business rules applied correctly

### Technical Knowledge
- [ ] Optimization objectives defined
- [ ] Constraints identified
- [ ] Data quality verified
- [ ] Validation approach planned

### Practical Knowledge
- [ ] Implementation feasibility assessed
- [ ] Operational constraints considered
- [ ] Customer impact evaluated
- [ ] Risk mitigation planned

---

## Loop Prevention

**Knowledge Search Limits:**
- Max 3 knowledge recall procedures per decision
- Each procedure: max 5 minutes
- If knowledge is insufficient, proceed with best available
- Don't search for perfect knowledge when good enough exists

**Sanity Check:**
- "Am I searching for knowledge or avoiding action?"
- "Is this knowledge search helping or delaying?"

---

**Version:** 1.0  
**Status:** Active  
**Next Review:** After major pipeline milestone
