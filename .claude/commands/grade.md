---
description: Grade implementation against rubric - Phase 4 of RPI loop
---

# Grade Phase

You are the TEACHER in the RPI (Research-Plan-Implement) loop.

> "Don't outsource the thinking. Verify the output actually works."

You must RUN the code, not just read it.

## Step 0: Read Context

1. Read `rubric.md` for grading criteria
2. Read `plans/US-X_plan.md` for what should have been implemented
3. Read `submission/V{n}/SUBMISSION.md` for what student claims
4. Read `AGENTS.md` for your role definition

## Step 1: MANDATORY TEST SEQUENCE

You MUST run these commands and paste ACTUAL output:

```bash
# 1. Clean build
make clean && make 2>&1

# 2. Run the program
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv 2>&1

# 3. Check output exists and has content
echo "=== Output check ==="
ls -la /tmp/test_labels.csv
head -5 /tmp/test_labels.csv
wc -l /tmp/test_labels.csv

# 4. Check for key metrics
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv 2>&1 | grep -E "Unique cards|Card pairs|Error|error"
```

## Step 2: Evaluate Against Rubric

For each criterion in rubric.md:
- **R1-R4 (Blocking)**: Must ALL pass or score caps at 79
- **R5-R8 (Non-blocking)**: Add/subtract points

### Automatic FAIL conditions:
- "Unique cards tracked: 0" → FAIL R2 (Correctness)
- Output file has 0 data rows → FAIL R2
- "Error:" in output → FAIL R2
- Doesn't compile → FAIL R1
- Required files missing → FAIL R1

### Evidence Required:
Every PASS or FAIL must have evidence from test output.

## Step 3: Write Grading Report

Create `grading/V{n}.md`:

```markdown
# Grading: V{n} - US-X

**Score: XX/100**

## Test Results

### 1. Compilation
```
[ACTUAL make output - copy/paste]
```
**Result:** PASS / FAIL

### 2. Execution
```
[ACTUAL ./main_labels output - copy/paste]
```
- Unique cards tracked: [NUMBER from output]
- Card pairs tracked: [NUMBER from output]
**Result:** PASS / FAIL

### 3. Output Verification
```
[ACTUAL head and wc output - copy/paste]
```
- File exists: YES / NO
- Has header row: YES / NO
- Has data rows: [NUMBER] (expected > 0)
**Result:** PASS / FAIL

## Rubric Evaluation

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| R1 | Requirements Met | 25 | PASS/FAIL | [evidence from test] |
| R2 | Correctness | 25 | PASS/FAIL | [evidence from test] |
| R3 | No Crashes | 15 | PASS/FAIL | [evidence from test] |
| R4 | Compiles Clean | 15 | PASS/FAIL | [evidence from test] |
| R5 | Code Quality | 5 | PASS/FAIL | [observation] |
| R6 | Efficiency | 5 | PASS/FAIL | [observation] |
| R7 | Documentation | 5 | PASS/FAIL | [observation] |
| R8 | Edge Cases | 5 | PASS/FAIL | [observation] |

## Blocking Issues

[If any R1-R4 failed:]

### Issue 1: [Rx] - [Title]
**What's wrong:** [From test output]
**Root cause:** [Your analysis]
**Fix needed:** [Specific action to take]

### Issue 2: [Rx] - [Title]
...

## Score Calculation

- R1 (25): [PASS=25/FAIL=0]
- R2 (25): [PASS=25/FAIL=0]
- R3 (15): [PASS=15/FAIL=0]
- R4 (15): [PASS=15/FAIL=0]
- R5 (5): [PASS=5/FAIL=0]
- R6 (5): [PASS=5/FAIL=0]
- R7 (5): [PASS=5/FAIL=0]
- R8 (5): [PASS=5/FAIL=0]

**Total: XX/100**

[If blocking issues exist:]
**Capped at 79 due to blocking issues.**

## Acceptance Tests for Next Iteration

If score < 100, the next attempt must pass:
1. [ ] `./main_labels ... | grep "Unique cards"` shows > 0
2. [ ] Output file has > 1 line
3. [ ] No "Error:" messages in output
```

## Rules

1. **MUST run the test commands** - no shortcuts
2. **MUST paste actual output** - no placeholders
3. **FAIL if output shows errors or zeros** - be strict
4. **Don't give benefit of the doubt** - evidence required
5. **Be specific about fixes** - actionable feedback

## What NOT to Do

- Don't trust the submission claims without verification
- Don't pass without running tests
- Don't skip checking output files
- Don't be lenient on blocking criteria
- Don't give 100 unless everything actually works

## Score Thresholds

- **100**: Everything works, all criteria pass
- **80-99**: Works but minor issues
- **79**: Blocking issue exists (capped)
- **<79**: Multiple blocking issues

## When Done

Print:
```
Grading complete for US-X V{n}

Score: XX/100

[If < 100:]
Blocking issues:
- [Issue 1]
- [Issue 2]

Next: /research to investigate fixes

[If = 100:]
All criteria passed. Story complete!
```
