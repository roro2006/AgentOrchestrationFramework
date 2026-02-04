---
description: Run full RPI loop - Research, Plan, Implement, Grade
---

# Full RPI Loop

Execute the complete Research-Plan-Implement-Grade cycle.

## Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  RESEARCH   │ → │    PLAN     │ → │  IMPLEMENT  │ → │    GRADE    │
│             │    │             │    │             │    │             │
│ Explore     │    │ Create plan │    │ Execute     │    │ RUN & verify│
│ codebase    │    │ with code   │    │ step by     │    │ against     │
│             │    │ snippets    │    │ step        │    │ rubric      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      ↓                  ↓                  ↓                  ↓
  research/          plans/           submission/         grading/
```

## Step 1: Determine Context

```bash
# Check current story
cat PROJECT_STATUS.md | grep -A5 "Current Story"

# Check if this is a retry
ls -la grading/ 2>/dev/null
```

Determine version number:
- If no grading exists: V1
- If grading exists: V{n+1}

## Step 2: RESEARCH Phase

Read `.claude/commands/research.md` and execute:

1. Read PROJECT_STATUS.md and PROJECT_PROMPT.md
2. If retry, read previous grading
3. Explore codebase for relevant code
4. Analyze data formats
5. Output: `research/US-X_research.md`

**Checkpoint**: Research document created?

## Step 3: PLAN Phase

Read `.claude/commands/plan.md` and execute:

1. Read research document
2. Read rubric.md
3. Design implementation approach
4. Create step-by-step plan with code snippets
5. Output: `plans/US-X_plan.md`

**Checkpoint**: Plan has actual code snippets and tests?

## Step 4: IMPLEMENT Phase

Read `.claude/commands/implement.md` and execute:

1. Read the plan
2. Verify prerequisites
3. Execute steps in order
4. Run test after each step
5. Output: `submission/V{n}/SUBMISSION.md`

**Checkpoint**: All tests pass?

## Step 5: GRADE Phase

Read `.claude/commands/grade.md` and execute:

1. Run mandatory test sequence
2. Evaluate against rubric
3. Document with evidence
4. Output: `grading/V{n}.md`

**Checkpoint**: Score calculated with evidence?

## Step 6: Evaluate Result

```
Score >= 100? ──YES──→ Story Complete! Update PROJECT_STATUS.md
     │
    NO
     │
     └──→ Back to Step 2 (RESEARCH) with grading feedback
```

## Context Management

Each phase should:
1. Start by reading only its input artifacts
2. Stay focused on the current phase
3. Create compressed output for next phase

## Phase Artifacts

| Phase | Input | Output |
|-------|-------|--------|
| Research | PROJECT_*.md, src/, grading/ | research/US-X_research.md |
| Plan | research/US-X_research.md, rubric.md | plans/US-X_plan.md |
| Implement | plans/US-X_plan.md | submission/V{n}/, code changes |
| Grade | rubric.md, plan, submission, src/ | grading/V{n}.md |

## Emergency Stop

If any phase fails catastrophically:
1. Document what happened
2. Save partial work
3. Report to user
4. Wait for guidance

## Success Criteria

Loop completes when:
- Score = 100
- All R1-R4 blocking criteria pass
- Test output shows actual working code
