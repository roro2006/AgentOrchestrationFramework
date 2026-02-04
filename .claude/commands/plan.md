---
description: Create implementation plan - Phase 2 of RPI loop
---

# Plan Phase

You are the PLANNER in the RPI (Research-Plan-Implement) loop.

> "A plan so clear the dumbest model won't screw it up."

## Step 0: Read Research

1. Read `research/US-X_research.md` (the compressed research)
2. Read `rubric.md` to understand grading criteria
3. Read `AGENTS.md` for your role definition

## Step 1: Design the Approach

Based on the research:
- What specific changes are needed?
- What files need modification?
- What's the order of operations?
- How will we verify each step?

## Step 2: Create Detailed Plan

Create `plans/US-X_plan.md` with **ACTUAL CODE SNIPPETS**:

```markdown
# Plan: US-X - [Story Name]

## Goal
[1-2 sentences - what success looks like]

## Prerequisites
- [ ] Data files exist: `ls data/tmp/*.csv`
- [ ] Code compiles: `make clean && make`

## Implementation Steps

### Step 1: [Description]
**File:** `src/labels.c`
**Lines:** 67-82

**Current code:**
```c
// Copy EXACT current code from research document
```

**New code:**
```c
// Write EXACT replacement code
```

**Test:**
```bash
make && ./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test.csv 2>&1 | grep "Unique cards"
# Expected: Unique cards tracked: > 0
```

### Step 2: [Description]
**File:** `src/xxx.c`
**Lines:** X-Y

**Current code:**
```c
[exact code]
```

**New code:**
```c
[exact replacement]
```

**Test:**
```bash
[command]
# Expected: [output]
```

## Final Verification

```bash
# Full test sequence
make clean && make
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv

# Check output
head -5 /tmp/test_labels.csv
wc -l /tmp/test_labels.csv  # Should be > 1

# Check metrics
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv 2>&1 | grep -E "Unique cards|Card pairs"
```

## Success Criteria

### Automated (Implementer can verify)
- [ ] `make` compiles without errors
- [ ] `./main_labels` runs without crashes
- [ ] Output file has > 1 line
- [ ] "Unique cards tracked" > 0

### Manual (Teacher will verify)
- [ ] Output CSV has correct columns
- [ ] Synergy values are reasonable

## Rollback
```bash
git checkout src/labels.c  # Revert changes if needed
```
```

## Rules

1. **Include ACTUAL code snippets** - copy from research
2. **Each step must be independently testable**
3. **Be EXACT** - file paths, line numbers, code
4. **Don't be vague** - "improve parsing" is BAD, "change line 67 from X to Y" is GOOD
5. **Separate automated vs manual verification**

## What NOT to Do

- Don't use vague descriptions
- Don't skip test commands
- Don't assume - be explicit
- Don't over-engineer - minimal changes only
- Don't add features not in the story

## When Done

Print:
```
Plan complete for US-X

Created: plans/US-X_plan.md

Implementation steps:
1. [Step 1 summary]
2. [Step 2 summary]

Ready for /implement
```
