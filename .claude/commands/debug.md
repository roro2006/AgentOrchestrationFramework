---
description: Debug a failing test or runtime issue
---

# Debug Issue

Systematic approach to debugging failures.

## Step 1: Reproduce the Issue

```bash
# Run the failing command
make clean && make
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test.csv 2>&1

# Capture exact error
./main_labels ... 2>&1 | tee /tmp/debug_output.txt
```

## Step 2: Isolate the Problem

### If Compilation Error
```bash
# Check specific file
gcc -Wall -Wextra -c src/file.c -o /tmp/test.o 2>&1

# Check includes
grep -n "#include" src/file.c
```

### If Runtime Error
```bash
# Check if data files exist
ls -la data/tmp/*.csv data/raw/*.csv

# Check file permissions
head -1 data/tmp/powered_premier_games.csv

# Check for obvious issues
./main_labels 2>&1 | head -20
```

### If Wrong Output
```bash
# Check what we got vs expected
head -5 /tmp/test.csv

# Look for the specific metric
./main_labels ... 2>&1 | grep -E "Unique|pairs|Error"

# Trace through the code
grep -n "function_that_might_fail" src/*.c
```

## Step 3: Trace the Code Path

Use the researcher agent to understand:
1. What function is failing?
2. What's the input to that function?
3. What's the expected output?
4. Where does it diverge?

## Step 4: Form Hypothesis

Based on investigation:
```markdown
## Debug Hypothesis

**Symptom:** [What's failing]
**Location:** `src/file.c:line`
**Hypothesis:** [Why it might be failing]
**Test:** [How to verify this hypothesis]
```

## Step 5: Test Hypothesis

```bash
# Add debug output (temporary)
# Or use existing debug info
# Or trace through logic manually
```

## Step 6: Document Finding

```markdown
## Debug Report

### Issue
[Description of the problem]

### Root Cause
[What's actually wrong]
**File:** `src/file.c`
**Line:** XX
**Problem:** [Specific issue]

### Evidence
```
[Output that proves this is the issue]
```

### Fix
[What needs to change]

### Verification
```bash
[Command to verify fix works]
```
```

## Common Issues in This Codebase

### "Unique cards tracked: 0"
- Check CSV column parsing in `src/csv.c`
- Verify column indices match actual CSV headers
- Check if cards are being found in `cards.csv` lookup

### Compilation Errors
- Check header includes
- Verify struct definitions match usage
- Check function signatures

### Segmentation Fault
- Check NULL pointer handling
- Verify array bounds
- Check malloc/free pairs

## Debug Tools

```bash
# Compile with debug info
gcc -g -Wall -Wextra src/*.c -o main_debug

# Run with basic trace
./main_debug 2>&1 | head -50

# Check memory (if valgrind available)
valgrind ./main_labels ...
```
