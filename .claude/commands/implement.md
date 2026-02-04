---
description: Execute implementation plan - Phase 3 of RPI loop
---

# Implement Phase

You are the IMPLEMENTER in the RPI (Research-Plan-Implement) loop.

> "The implement phase is the least exciting part."

If the plan is good, implementation should be straightforward.

## Step 0: Read the Plan

1. Read `plans/US-X_plan.md` completely
2. Read `AGENTS.md` for your role definition
3. Understand what needs to be done

## Step 1: Verify Prerequisites

Run the prerequisite checks from the plan:
```bash
# Check data files exist
ls -la data/tmp/*.csv

# Check code compiles
make clean && make
```

If prerequisites fail, STOP and report.

## Step 2: Execute Steps IN ORDER

For each step in the plan:

1. **Read the current code** to verify it matches the plan
2. **Make the change** exactly as specified
3. **Run the test** immediately after
4. **If test fails**, STOP and report

### Example Workflow:
```bash
# Step 1: Modify src/labels.c
# [Use Edit tool to make the change]

# Run step test
make && ./main_labels ... | grep "Unique cards"
# Verify output matches expected

# Step 2: Modify next file
# [Continue...]
```

## Step 3: Run Final Verification

After all steps, run the full verification from the plan:
```bash
make clean && make
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv

# Check output
head -5 /tmp/test_labels.csv
wc -l /tmp/test_labels.csv
```

## Step 4: Create Submission

Create `submission/V{n}/SUBMISSION.md`:

```markdown
# Submission V{n} - US-X

## Steps Completed
- [x] Step 1: [What was done]
- [x] Step 2: [What was done]

## Test Output

### Compilation
```
[ACTUAL make output]
```

### Execution
```
[ACTUAL ./main_labels output]
```

### Output Verification
```
[ACTUAL head and wc output]
```

## Files Modified
| File | Change |
|------|--------|
| src/labels.c | Added card tracking in process_row() |

## Known Issues
[Be honest if something doesn't work perfectly]

## Deviation from Plan
[Note any changes you had to make]
```

## Rules

1. **Follow the plan EXACTLY** - don't improvise
2. **Run tests after EVERY step** - verify as you go
3. **Include ACTUAL output** - not placeholders
4. **If something fails, STOP** - don't continue blindly
5. **Be honest** - report issues truthfully

## What NOT to Do

- Don't "improve" beyond the plan
- Don't skip tests
- Don't make up output
- Don't ignore failures
- Don't add features not in the plan

## If You Get Stuck

```markdown
## Issue Encountered

**Step:** [Which step]
**Expected:** [What plan said would happen]
**Actual:** [What actually happened]

**Error:**
```
[actual error message]
```

**Analysis:**
[Your analysis of why it failed]
```

Then STOP and wait for guidance.

## When Done

Print:
```
Implementation complete for US-X V{n}

Created: submission/V{n}/SUBMISSION.md

Results:
- Compilation: PASS/FAIL
- Execution: PASS/FAIL
- Output check: PASS/FAIL

Ready for /grade
```
