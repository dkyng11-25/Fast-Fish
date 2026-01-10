# Order Check Template - Fast Fish Pipeline

**Depth Level:** 2 (Problem-solving)  
**Last Updated:** 2025-01-05  
**Purpose:** Periodic verification that the project maintains order and avoids mess

---

## When to Run Order Check

- After completing each pipeline step refactoring
- After major feature additions
- When feeling lost or confused
- Before major architectural decisions
- Weekly during active development

---

## Meta-Level Order Check

### Thinking Strategy Coherence
- [ ] Thinking strategy is still appropriate for retail optimization
- [ ] Perspectives are still relevant (Retail Strategist, Data Scientist, OR Expert)
- [ ] Not overthinking or underthinking

### Meta-Document Status
- [ ] FAST_FISH_THINKING_STRATEGY.md is current
- [ ] PERSPECTIVES_NEEDED.md is current
- [ ] RETAIL_KNOWLEDGE_SEARCH.md is being followed

### Meta-Mess Indicators
- [ ] Changing thinking strategy too often?
- [ ] Adding too many perspectives?
- [ ] Meta-thinking becoming the problem?

**If any indicators checked, STOP and simplify.**

---

## Problem-Level Order Check

### Plan Coherence
- [ ] Implementation plan still makes sense
- [ ] Haven't deviated from customer requirements without reason
- [ ] Success criteria (8/10 customer satisfaction) still valid

### Problem-Document Status
- [ ] DELIVERABLES_IMPLEMENTATION_PLAN.md is current
- [ ] README_PLANS_INDEX.md is up to date
- [ ] Customer feedback is integrated

### Problem-Mess Indicators
- [ ] Scope creep beyond customer requirements?
- [ ] Too many course corrections?
- [ ] Lost sight of sell-through optimization goal?

**If any indicators checked, STOP and refocus on customer requirements.**

---

## Implementation-Level Order Check

### Pipeline Organization
- [ ] All steps follow 4-phase pattern (setup → apply → validate → persist)
- [ ] No files exceed 500 LOC
- [ ] Repository pattern used for all I/O
- [ ] Dependency injection properly implemented

### Code Quality Status
- [ ] BDD tests exist for refactored steps
- [ ] Tests actually test real code (not just mocks)
- [ ] Documentation is current

### Implementation-Mess Indicators
- [ ] Too many half-finished refactorings?
- [ ] Unclear what's done vs. in-progress?
- [ ] Code doesn't match documentation?

**If any indicators checked, STOP and complete current work before starting new.**

---

## Document Structure Check

### Required Documents Present
- [ ] protocols/FAST_FISH_THINKING_STRATEGY.md
- [ ] protocols/PERSPECTIVES_NEEDED.md
- [ ] protocols/RETAIL_KNOWLEDGE_SEARCH.md
- [ ] protocols/PIPELINE_EXECUTION_PROTOCOL.md
- [ ] plans/DELIVERABLES_IMPLEMENTATION_PLAN.md
- [ ] plans/README_PLANS_INDEX.md

### Document Cross-References Valid
- [ ] All document references point to existing files
- [ ] No orphaned documents
- [ ] Document index is current

### Document Mess Indicators
- [ ] Too many documents?
- [ ] Conflicting information between documents?
- [ ] Unclear relationships between documents?

**If any indicators checked, consolidate or remove unnecessary documents.**

---

## Customer Alignment Check

### Customer Requirements Status
- [ ] Sell-through rate as primary optimization objective
- [ ] Mathematical optimization model (not rule-based)
- [ ] Store capacity integration in clustering
- [ ] Style validation with confidence scores
- [ ] Dynamic baseline weight adjustment
- [ ] Supply-demand gap analysis
- [ ] Scenario planning capability

### Customer Satisfaction Tracking
- [ ] D-D Back-test: Target 8/10 (from 4/10)
- [ ] D-E Target-SPU: Target 8/10 (from 5/10)
- [ ] D-G Baseline Logic: Target 8/10 (from 6/10)
- [ ] Overall: Target 8/10

### Customer Alignment Mess Indicators
- [ ] Implementing features customer didn't request?
- [ ] Ignoring customer feedback?
- [ ] Not tracking customer satisfaction scores?

**If any indicators checked, STOP and re-read customer requirements.**

---

## Technical Debt Check

### Code Quality Metrics
- [ ] No files exceed 500 LOC
- [ ] All refactored steps have tests
- [ ] No TODO/FIXME comments older than 1 week
- [ ] All imports at top of files

### Architecture Consistency
- [ ] All steps use repository pattern
- [ ] All steps use dependency injection
- [ ] All steps follow 4-phase pattern
- [ ] Consistent error handling

### Technical Debt Indicators
- [ ] Accumulating TODO comments?
- [ ] Skipping tests to save time?
- [ ] Hardcoding values that should be configurable?

**If any indicators checked, address technical debt before continuing.**

---

## Cleanup Actions

If mess is detected:

1. **Stop and assess** - Don't make it worse
2. **Identify root cause** - Why did mess occur?
3. **Simplify** - Remove unnecessary complexity
4. **Reorganize** - Fix structure
5. **Update documents** - Reflect new order
6. **Prevent recurrence** - Adjust processes

---

## Order Check Summary

**Date:** _______________

### Overall Status
- [ ] 🟢 All checks passed - Continue work
- [ ] 🟡 Minor issues - Address before next major milestone
- [ ] 🔴 Major issues - STOP and fix immediately

### Issues Found
1. _______________
2. _______________
3. _______________

### Actions Taken
1. _______________
2. _______________
3. _______________

### Next Order Check Scheduled
Date: _______________

---

**Version:** 1.0  
**Status:** Active  
**Frequency:** Weekly or after major milestones
