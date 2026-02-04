---
description: Iterate on failed implementation - restart RPI loop with grading feedback
---

# Iterate After Failure

When grading returns < 100, use this to restart the RPI loop with context from the failure.

## Step 0: Read Previous Grading

1. Find the latest grading: `ls -lt grading/`
2. Read `grading/V{n}.md` completely
3. Identify blocking issues

## Step 1: Extract Failure Information

From the grading, identify:
- Which rubric criteria failed?
- What was the actual test output?
- What's the root cause analysis?
- What specific fix is needed?

## Step 2: Research the Fix

Start a NEW research phase focused on the failure:

```bash
# If the issue was in labels.c
cat src/labels.c | head -100

# If CSV parsing issue
head -3 data/tmp/powered_premier_games.csv

# Search for the problematic code
grep -n "relevant_function" src/*.c
```

## Step 3: Create Updated Research

Add to or update `research/US-X_research.md`:

```markdown
## Root Cause Analysis (V{n} Failure)

### What Failed
- Criterion: [Rx]
- Test output: [From grading]
- Expected: [What should have happened]

### Root Cause
[Why it failed - be specific]

### Investigation

```c
// Found at src/file.c:XX
[problematic code]
```

### Fix Strategy
[What needs to change]
```

## Step 4: Update Plan

Modify `plans/US-X_plan.md` to fix the issue:

1. Keep working steps
2. Add/modify steps that address the failure
3. Update tests to catch the specific issue

## Step 5: Continue Loop

After updating research and plan:
1. Run `/implement` with V{n+1}
2. Run `/grade` to verify fix

## Iteration Checklist

- [ ] Read grading feedback completely
- [ ] Understand root cause (not just symptoms)
- [ ] Research the actual code involved
- [ ] Update plan with specific fix
- [ ] Increment version number
- [ ] Run full test sequence

## Anti-Patterns

- **Don't**: Make random changes hoping something works
- **Don't**: Skip researching the actual root cause
- **Don't**: Ignore the grading feedback
- **Don't**: Repeat the same approach that failed

## When to Escalate

If after 3 iterations the same issue persists:
1. Document all attempts
2. Request human review
3. Consider if the story needs to be split
