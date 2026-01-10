# Fast Fish Protocols

**Meta Agent Protocol Implementation for Retail Optimization**

---

## 📖 Overview

This directory contains the **Meta Agent Protocol** documents for the Fast Fish project. These protocols guide HOW we think about and approach retail product mix optimization, following the methodology from the meta-agent-protocol-tutorial.

---

## 📁 Protocol Documents

### Level 1: Meta-Thinking (HOW to Think)

| Document | Purpose |
|----------|---------|
| **[FAST_FISH_THINKING_STRATEGY.md](FAST_FISH_THINKING_STRATEGY.md)** | Defines the overall thinking approach for retail optimization |
| **[PERSPECTIVES_NEEDED.md](PERSPECTIVES_NEEDED.md)** | Lists expert perspectives to simulate when making decisions |
| **[RETAIL_KNOWLEDGE_SEARCH.md](RETAIL_KNOWLEDGE_SEARCH.md)** | Protocol for recalling and applying domain knowledge |

### Level 2: Problem-Solving (WHAT to Do)

| Document | Purpose |
|----------|---------|
| **[PIPELINE_EXECUTION_PROTOCOL.md](PIPELINE_EXECUTION_PROTOCOL.md)** | Structured approach for executing pipeline steps |
| **[PLANNING_TEMPLATE.md](PLANNING_TEMPLATE.md)** | Template for creating and reviewing plans |
| **[ORDER_CHECK_TEMPLATE.md](ORDER_CHECK_TEMPLATE.md)** | Periodic verification to maintain order |

---

## 🎯 How to Use These Protocols

### Before Starting Work

1. **Read FAST_FISH_THINKING_STRATEGY.md** - Understand the thinking approach
2. **Review PERSPECTIVES_NEEDED.md** - Know which expert lenses to use
3. **Check RETAIL_KNOWLEDGE_SEARCH.md** - Recall relevant domain knowledge

### During Work

1. **Follow PIPELINE_EXECUTION_PROTOCOL.md** - Execute steps correctly
2. **Use PLANNING_TEMPLATE.md** - Create structured plans
3. **Run ORDER_CHECK_TEMPLATE.md** - Verify order periodically

### After Work

1. **Reflect on effectiveness** - What worked, what didn't
2. **Update protocols if needed** - Max 2 revisions per protocol
3. **Document learnings** - Capture insights for future

---

## 🔄 Three-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: META-THINKING                                     │
│  "How should we think about retail optimization?"           │
│  ├── FAST_FISH_THINKING_STRATEGY.md                        │
│  ├── PERSPECTIVES_NEEDED.md                                 │
│  └── RETAIL_KNOWLEDGE_SEARCH.md                            │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 2: PROBLEM-SOLVING                                   │
│  "What's the solution approach?"                            │
│  ├── PIPELINE_EXECUTION_PROTOCOL.md                        │
│  ├── PLANNING_TEMPLATE.md                                   │
│  └── ORDER_CHECK_TEMPLATE.md                               │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 3: IMPLEMENTATION                                    │
│  "How do we execute?"                                       │
│  ├── src/step*.py (pipeline steps)                         │
│  ├── tests/features/*.feature (BDD scenarios)              │
│  └── output/*.csv (results)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 Loop Prevention

**Critical:** These protocols include loop prevention mechanisms:

- **Depth Limit:** Max 3 levels of meta-thinking
- **Iteration Limits:** Max 2-3 revisions per document
- **Time Budget:** 10% meta-thinking, 70% execution, 20% reflection
- **Emergency Break:** "STOP THINKING, START DOING"

If you find yourself:
- Revising protocols more than twice
- Spending more than 20% of time on meta-thinking
- Not making concrete progress

**STOP and execute with current protocols.**

---

## 📊 Key Principles

1. **Sell-through is primary** - All optimization focuses on sell-through rate
2. **Data-driven decisions** - Use real sales data, not assumptions
3. **Mathematical optimization** - Prefer optimization over static rules
4. **Customer feedback integration** - Iterate based on customer scores
5. **Modular architecture** - 4-phase pattern, repository pattern, DI

---

## 🔗 Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Project Overview | `../FAST_FISH_PROJECT_OVERVIEW.md` | Executive summary |
| Code Guide | `../CODE_SUMMARIZATION_GUIDE.md` | Code documentation |
| Requirements | `../CLIENT_REQUIREMENTS_CHECKLIST.md` | Compliance tracking |
| Plans | `../plans/` | Implementation plans |

---

## ✅ Protocol Checklist

Before major work, verify:

- [ ] Read FAST_FISH_THINKING_STRATEGY.md
- [ ] Identified relevant perspectives
- [ ] Recalled domain knowledge
- [ ] Created plan using template
- [ ] Understand pipeline execution protocol
- [ ] Know when to run order checks

---

**Version:** 1.0  
**Based on:** meta-agent-protocol-tutorial  
**Last Updated:** 2025-01-05
