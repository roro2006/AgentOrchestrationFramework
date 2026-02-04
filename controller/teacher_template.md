# TEACHER Feedback Template

---

## Header

```markdown
# Grading: V{n}
**Date:** {YYYY-MM-DD}
**Submission Reviewed:** submission/V{n}/
**Rubric Version:** v{x.y}
```

---

## Score Summary

# Score: {X}/100

**Status:** {BLOCKED | IN PROGRESS | COMPLETE}

---

## Rubric Evaluation Table

| ID | Criterion | Weight | Status | Evidence Provided | Notes |
|----|-----------|--------|--------|-------------------|-------|
| R1 | Requirements Coverage | 20 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R2 | Correctness | 25 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R3 | Reliability | 15 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R4 | Performance | 10 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R5 | Code Quality | 10 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R6 | Documentation | 10 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R7 | Reproducibility | 5 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |
| R8 | Safety/Compliance | 5 | ✅ PASS / ❌ FAIL | {Yes/No + ref} | {Specific note} |

---

## Blocking Issues (Must Fix)

These MUST be resolved before score can exceed 79:

1. **[R{x}]** {Issue description}
   - **What's wrong:** {Specific problem}
   - **Required fix:** {Exact change needed}
   - **Acceptance test:** {How to verify it's fixed}

2. **[R{y}]** {Issue description}
   - **What's wrong:** {Specific problem}
   - **Required fix:** {Exact change needed}
   - **Acceptance test:** {How to verify it's fixed}

---

## Non-Blocking Improvements

These prevent 100/100 but don't cap the score:

1. **[R{x}]** {Improvement needed}
   - **Current state:** {What exists}
   - **Required state:** {What's needed}

---

## Acceptance Tests for V{n+1}

The next submission MUST demonstrate:

### Mandatory (Blocking)
- [ ] {Test 1}: {Exact command or verification step}
- [ ] {Test 2}: {Exact command or verification step}

### Required for 100
- [ ] {Test 3}: {Exact command or verification step}
- [ ] {Test 4}: {Exact command or verification step}

---

## Pass/Fail Checklist for Next Submission

Student must provide evidence for each:

```
□ [R1] {Specific requirement to demonstrate}
□ [R2] {Specific test to pass}
□ [R3] {Specific error case to handle}
□ [R4] {Specific benchmark to meet}
□ [R5] {Specific quality check to pass}
□ [R6] {Specific documentation to include}
□ [R7] {Specific reproduction step to work}
□ [R8] {Specific compliance check to pass}
```

---

## Rubric Updates (If Any)

**Change:** {Description of refinement}
**Rationale:** {Why more testable, NOT more permissive}
**New criterion text:** {Updated wording}

*(Only include if rubric needs refinement for testability)*

---

## Iteration Status

- **Current iteration:** {n} of 10 max
- **Trajectory:** {Improving / Stalled / Regressing}
- **Recommendation:** {Continue / Split scope / Escalate}

---

## Sign-Off (Only for Score = 100)

```
✅ DEFINITION OF DONE MET
All rubric criteria satisfied with evidence.
Submission V{n} is ACCEPTED as final deliverable.

Signed: TEACHER
Date: {YYYY-MM-DD}
```
