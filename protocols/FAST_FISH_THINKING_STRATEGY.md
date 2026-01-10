# Fast Fish Thinking Strategy

**Depth Level:** 1 (Meta-thinking)  
**Last Updated:** 2025-01-05  
**Loop Prevention:** Max 2 revisions to this strategy  
**Mode:** Retail Product Mix Optimization & Sell-Through Maximization

---

## Purpose

Define HOW we should think about retail product mix optimization before analyzing or implementing pipeline steps. This guides the entire Fast Fish project protocol.

**Current Focus:** Optimizing sell-through rate through store clustering, business rule analysis, and SPU (Stock Keeping Unit) allocation optimization.

---

## Theoretical Foundation

### Retail Analytics Approach to Product Mix Optimization

Drawing from established frameworks in retail science and operations research:

1. **Store Clustering Theory** (Levy & Weitz, 2012)
   - Grouping similar stores for coordinated merchandise strategy
   - Weather-aware clustering for seasonal product alignment
   - Temperature-band analysis for climate-appropriate assortment

2. **Assortment Optimization** (Kök et al., 2015)
   - Category-level planning with performance-based adjustments
   - Supply-demand gap analysis by cluster × product role
   - Sell-through rate as primary optimization objective

3. **Business Rule Analysis** (Fisher & Raman, 2010)
   - Missing category identification
   - Imbalanced allocation detection
   - Below-minimum threshold analysis
   - Overcapacity opportunity identification

4. **Mathematical Optimization** (Bertsimas & Kallus, 2020)
   - Constraint-based allocation logic
   - Dynamic baseline weight adjustment
   - Capacity and lifecycle constraint enforcement

---

## Problem Type: Retail Product Mix Optimization

**Classification:** Analytical + Optimization + Pattern-based + Data-Driven

**Characteristics:**
- Requires understanding of retail business metrics (sell-through, revenue, allocation)
- Involves weather and geographic clustering
- Balances store capacity with product assortment breadth
- Depends on historical sales patterns and seasonal trends
- Measurable through sell-through rate and revenue lift

---

## Thinking Approach

### Primary Mode: **Multi-Perspective Analytical with Optimization Focus**

We approach retail optimization through multiple expert lenses:

1. **Retail Strategist Perspective** (Business)
   - Focus: What drives sell-through and revenue?
   - Strength: Understanding store group dynamics and category performance
   - Application: Evaluating business rule effectiveness

2. **Data Scientist Perspective** (Analytical)
   - Focus: How do patterns emerge from sales data?
   - Strength: Clustering algorithms, statistical analysis
   - Application: Store grouping, trend identification

3. **Operations Research Perspective** (Optimization)
   - Focus: How do we maximize objectives under constraints?
   - Strength: Mathematical optimization, constraint satisfaction
   - Application: SPU allocation, capacity optimization

4. **Store Manager Perspective** (Operational)
   - Focus: How are recommendations implemented at store level?
   - Strength: Understanding practical constraints and execution
   - Application: Validating feasibility of recommendations

5. **Customer Perspective** (Demand)
   - Focus: What products do customers want?
   - Strength: Understanding demand patterns and preferences
   - Application: Assortment breadth and depth decisions

### Reasoning Style: **Inductive + Optimization-Based**

- **Inductive:** Generalize patterns from historical sales data
- **Optimization:** Maximize sell-through under capacity constraints
- **Avoid Purely Rule-Based:** Use mathematical optimization over static rules

### Depth vs. Breadth: **Balanced with Optimization Focus**

- **Depth:** Analyze each pipeline step thoroughly
- **Breadth:** Consider all 36+ pipeline steps holistically
- **Balance:** Don't over-engineer simple steps, focus optimization on high-impact areas

---

## Knowledge Search Strategy

### Relevant Knowledge Domains

1. **Retail Science**
   - Store clustering methodologies
   - Assortment planning principles
   - Sell-through optimization
   - Category management

2. **Data Engineering**
   - Pipeline architecture (36-step process)
   - Data validation and quality
   - API integration patterns
   - Weather data integration

3. **Operations Research**
   - Mathematical optimization models
   - Constraint satisfaction
   - Supply-demand gap analysis
   - Scenario planning

4. **Software Engineering**
   - BDD (Behavior-Driven Development)
   - 4-phase step pattern (setup → apply → validate → persist)
   - Repository pattern for data access
   - Dependency injection

### Knowledge Recall Protocol

**When analyzing pipeline steps:**
1. Simulate retail strategist: "What business value does this step provide?"
2. Simulate data scientist: "What patterns are we extracting?"
3. Simulate operations researcher: "How does this contribute to optimization?"
4. Recall domain knowledge: "What retail principles apply?"

**When implementing improvements:**
1. Recall successful patterns from existing steps
2. Simulate expert: "How would a retail optimization expert approach this?"
3. Check constraints: "Does this satisfy capacity and lifecycle constraints?"
4. Validate mechanism: "Does this improve sell-through rate?"

---

## Order Maintenance Strategy

### How to Avoid Creating a Mess

1. **Keep pipeline steps modular** - Each step < 500 LOC
2. **Follow 4-phase pattern** - setup → apply → validate → persist
3. **Use repository pattern** - All I/O through repositories
4. **Maintain clear documentation** - Feature files + code comments
5. **Regular testing** - BDD tests for each step

### Structure to Maintain

```
Clear separation:
- Meta-thinking (this document)
- Problem-solving (protocols)
- Implementation (pipeline steps)

No mixing:
- Don't put meta-thinking in step code
- Don't put implementation in protocols
- Keep levels distinct
```

### Order Check Frequency

- After every pipeline step refactoring
- After every major feature addition
- When feeling confused or lost
- Before major changes to architecture

---

## Reflection Strategy

### When to Reflect

1. **During execution** - Quick notes on what's working
2. **After each step** - What did we learn from this step?
3. **After customer feedback** - How do we incorporate feedback?
4. **Weekly** - What patterns are emerging?

### What to Reflect On

**Problem-Level:**
- Are the pipeline steps effective?
- Is sell-through improving?
- What business rules work best?
- What optimization opportunities exist?

**Meta-Level:**
- Is our thinking strategy appropriate?
- Should we add/remove perspectives?
- Is knowledge recall working?
- Are we maintaining order?

**System-Level:**
- How is the overall system evolving?
- What have we learned about retail optimization?
- How can we improve the meta-protocol itself?

### How to Capture Learnings

- **Immediate:** Quick notes in session logs
- **Daily:** Update PROGRESS_LOG.md
- **Weekly:** Create REFLECTION.md
- **Monthly:** Update SYSTEM_IMPROVEMENTS.md

---

## Loop Prevention

### Depth Limit: 3 Levels Maximum

1. **Level 1:** Implement/analyze pipeline steps
2. **Level 2:** Think about how we implement/analyze
3. **Level 3:** Think about our thinking strategy
4. **Level 4+:** FORBIDDEN - Stop and execute

### Iteration Limits

- **This strategy:** Max 2 revisions
- **Pipeline steps:** Max 3 refactoring iterations
- **Individual features:** Max 3 iterations
- **Customer feedback integration:** Max 2 iterations per feedback cycle

### Time Budget

- **Meta-thinking:** 10% of time
- **Protocol execution:** 70% of time
- **Reflection:** 20% of time

**If meta-thinking exceeds 20% of time, STOP and execute.**

### Progress Indicators

Every meta-thinking session must produce:
- [ ] Clearer thinking strategy
- [ ] Better knowledge recall
- [ ] Improved protocols
- [ ] Actionable insights

**If no progress indicators checked, it's a loop. STOP.**

---

## Sanity Checks

### Before Meta-Thinking

1. **Is this actually helping?**
   - Will this improve sell-through optimization?
   - Or am I avoiding the actual work?

2. **Am I overthinking?**
   - Is retail optimization simpler than I'm making it?
   - Am I creating complexity to justify the process?

3. **What if I just implemented the step?**
   - Would it be worse without this meta-thinking?
   - Is perfect strategy preventing good execution?

**If answers suggest overthinking, STOP meta-thinking and implement.**

---

## Key Principles

1. **Sell-through is primary** - All optimization focuses on sell-through rate
2. **Data-driven decisions** - Use real sales data, not assumptions
3. **Store groups are unified** - Coordinated assortment within groups
4. **Constraints matter** - Capacity, lifecycle, price-band constraints
5. **Mathematical optimization** - Prefer optimization over static rules
6. **Customer feedback integration** - Iterate based on customer scores
7. **Modular architecture** - 4-phase pattern, repository pattern, DI

---

## Success Criteria for This Strategy

This thinking strategy is successful if:

- [ ] Pipeline steps are coherent and maintainable
- [ ] Sell-through optimization is measurable
- [ ] Customer satisfaction improves (target: 8/10)
- [ ] Business rules are effective and validated
- [ ] System learns from successes and failures
- [ ] We don't get stuck in meta-thinking loops

---

## Fast Fish-Specific Thinking

When thinking about Fast Fish optimization:

1. **Business Model:** Store group-based uniform assortment planning
2. **Core KPI:** Sell-through rate optimization
3. **Store Groups:** 46 groups, 50-53 stores per group
4. **Categories:** 126 product categories with individual optimization
5. **Time Horizon:** 15-day periods (Period A/B per month)
6. **Data Foundation:** 100% real business data

---

## Next Steps

1. Use this strategy to guide pipeline step implementation
2. Simulate experts when analyzing business rules
3. Recall knowledge explicitly
4. Reflect on effectiveness
5. Revise strategy if needed (max 2 times)

---

**Remember: The goal is to optimize sell-through rate and achieve 8/10 customer satisfaction. When in doubt, execute and learn from reality.**

---

**Version:** 1.0  
**Revisions Remaining:** 2  
**Status:** Active
