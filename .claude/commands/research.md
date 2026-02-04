---
description: Research current user story - Phase 1 of RPI loop
---

# Research Phase

You are the RESEARCHER in the RPI (Research-Plan-Implement) loop.

## Step 0: Understand Context

1. Read `PROJECT_STATUS.md` to find the current user story
2. Read `PROJECT_PROMPT.md` to understand the full project
3. Read `AGENTS.md` for your role definition
4. Check if there's a previous `grading/V*.md` file (indicates retry)

## Step 1: Understand the Story

From PROJECT_PROMPT.md, identify:
- What does this user story require?
- What are the acceptance criteria?
- What data inputs/outputs are involved?

## Step 2: Explore the Codebase

```bash
# List all source files
ls -la src/

# Check what data files exist
ls -la data/tmp/ data/raw/ data/out/

# Look at the Makefile targets
cat Makefile | grep -E "^[a-z].*:"

# Search for relevant functions
grep -rn "KEYWORD" src/
```

## Step 3: Read Relevant Code

Based on the story, read the actual source files:
- For card tracking: focus on `src/labels.c`, `src/cards.c`
- For CSV parsing: focus on `src/csv.c`
- For data structures: focus on `src/hash.c`

**READ THE ACTUAL CODE** - don't guess!

## Step 4: Analyze Data Formats

```bash
# Check CSV column headers
head -1 data/tmp/powered_premier_games.csv

# Check cards.csv format
head -3 data/raw/cards.csv

# Count rows
wc -l data/tmp/powered_premier_games.csv
```

## Step 5: Check Previous Failure (if retry)

If `grading/V*.md` exists:
1. Read the grading file
2. Understand what failed
3. Research the ROOT CAUSE
4. Focus on fixing the actual problem

## Step 6: Write Research Document

Create `research/US-X_research.md` with:

```markdown
# Research: US-X - [Story Name]

## Story Requirements
[Copy exact requirements from PROJECT_PROMPT.md]

## Relevant Files
| File | Lines | Purpose |
|------|-------|---------|

## Current Implementation
[How it works TODAY]

## Key Code Sections
```c
// exact file:line reference
[actual code]
```

## Data Format
[From head -1 commands]

## Gotchas / Edge Cases
- [List potential issues]

## Root Cause of Previous Failure
[If retry - what went wrong]

## Recommended Approach
[High-level direction]
```

## Rules

- **Read actual code** - never guess
- **Include exact file:line references**
- **Stay objective** - report what IS
- **Be concise** - this is compression
- **Focus on THIS story only**

## When Done

Print:
```
Research complete for US-X

Created: research/US-X_research.md

Key findings:
- [Finding 1]
- [Finding 2]
- [Finding 3]

Ready for /plan
```
