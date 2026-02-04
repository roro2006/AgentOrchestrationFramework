# Two-Role Loop Controller

## Overview
This system orchestrates an iterative spec→submit→grade→revise workflow with strict stopping criteria.

---

## ROLE DEFINITIONS

### STUDENT Agent
**Responsibilities:**
1. Produce versioned deliverables in `submission/V{n}/`
2. Include claims list + known gaps list
3. Provide evidence (tests, outputs, benchmarks)
4. Reference previous version and list changes (V2+)
5. Map fixes to specific rubric items

**Constraints:**
- Cannot modify the rubric
- Must include at least one NEW piece of evidence per iteration
- Must provide "diff summary" on revisions

### TEACHER Agent
**Responsibilities:**
1. Grade ONLY against `rubric.md` (no subjective judgments)
2. Require evidence for each rubric item
3. Return structured revision plan with acceptance tests
4. Never award 100 unless ALL criteria satisfied
5. May refine rubric (only to make it MORE testable, not more permissive)

**Constraints:**
- Must cite rubric ID for every feedback point
- Must provide deterministic pass/fail checklist
- Cannot produce work product (only instructs)

---

## WORKFLOW LOOP

```
┌─────────────────────────────────────────────────────────────┐
│  STEP A: TEACHER sets assignment                            │
│  → Assignment spec, Rubric v1, Definition of Done (DoD)     │
│  → Constraints, Required evidence types                     │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP B: STUDENT submission (V1)                            │
│  → Work product in submission/V1/                           │
│  → Evidence, Self-grade, Claims, Known gaps                 │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP C: TEACHER grading                                    │
│  → Score + rubric pass/fail table                           │
│  → Blocking issues + Required revisions                     │
│  → Acceptance tests for next submission                     │
│  → Output to grading/V1.md                                  │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Score = 100?         │
              └───────────┬───────────┘
                    │           │
                   NO          YES
                    │           │
                    ▼           ▼
         ┌──────────────┐  ┌──────────────┐
         │ STEP D:      │  │ COMPLETE     │
         │ STUDENT      │  │ DoD met      │
         │ revision     │  │ Sign-off     │
         │ → V(n+1)     │  └──────────────┘
         └──────┬───────┘
                │
                └────────► Back to STEP C
```

---

## STOP CONDITIONS

1. **Success**: Teacher returns 100/100 with DoD sign-off
2. **Max iterations**: 10 per milestone (then scope must be split)
3. **Irreconcilable**: Teacher explicitly marks assignment as infeasible

---

## GUARDRAILS

1. Max 10 iterations per milestone
2. Teacher must cite rubric ID for all feedback
3. Student must include diff summary (V2+)
4. At least one NEW evidence item per iteration
5. Teacher cannot rubber-stamp (must verify evidence exists)

---

## EXECUTION COMMAND

To start a loop, the controller invokes:
1. TEACHER: "Set assignment for: {TASK_DESCRIPTION}"
2. Then alternates STUDENT→TEACHER until score=100 or max iterations

---

## FILE CONVENTIONS

```
/submission/V{n}/       # Student deliverables
/grading/V{n}.md        # Teacher feedback
/rubric.md              # Current rubric (versioned)
```
