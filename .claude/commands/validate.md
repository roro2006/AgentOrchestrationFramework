---
description: Validate implementation against plan and verify all success criteria
---

# Validate Implementation

Verify that an implementation matches its plan and all success criteria pass.

## Step 1: Locate Plan and Implementation

1. If plan path provided, use it
2. Otherwise, find recent plans: `ls -lt plans/`
3. Read the plan completely

## Step 2: Run All Automated Checks

Execute every command from the plan's "Automated Verification" section:

```bash
# Typical checks
make clean && make
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv
head -5 /tmp/test_labels.csv
wc -l /tmp/test_labels.csv
```

## Step 3: Verify Each Step

For each implementation step in the plan:
1. Check if the file was modified
2. Verify the change matches what was planned
3. Run the step's test command

## Step 4: Generate Validation Report

```markdown
## Validation Report: US-X

### Implementation Status
- [x] Step 1: [Description] - Verified
- [x] Step 2: [Description] - Verified
- [ ] Step 3: [Description] - Issue found

### Automated Verification Results
| Check | Command | Result |
|-------|---------|--------|
| Build | `make` | PASS |
| Run | `./main_labels ...` | PASS |
| Output | `wc -l /tmp/test.csv` | PASS (1234 lines) |

### Deviations from Plan
- [Any differences between plan and actual implementation]

### Manual Testing Required
- [ ] [Item from plan's manual verification]
- [ ] [Another item]

### Issues Found
1. **[Issue]**: [Description]
   - Expected: [From plan]
   - Actual: [What was found]
   - Impact: [How serious]

### Recommendation
[READY FOR GRADE / NEEDS FIXES]
```

## Rules

- Run ALL automated checks from the plan
- Document every deviation
- Be thorough but practical
- Don't skip manual verification items - list them for the user
