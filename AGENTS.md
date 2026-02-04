# AGENTS

This file defines the agents (roles) used in the RPI (Research-Plan-Implement) development loop.

Based on Context Engineering principles from Dex Horthy's "No Vibes Allowed" talk.

---

## Core Principle: Stay in the Smart Zone

```
Context Window Usage:
├── 0-40%   → SMART ZONE (good results)
└── 40-100% → DUMB ZONE (diminishing returns)

The more you fill the context window, the worse the results.
```

**Solution: Frequent Intentional Compaction**
- Each phase compresses its output into a markdown file
- Next phase starts with FRESH context, reads only what it needs
- Never carry conversation history - only compressed artifacts

---

## The RPI Loop

```
┌─────────────────────────────────────────────────────────────┐
│                      FOR EACH USER STORY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                            │
│  │  RESEARCHER │ → Explore codebase, find relevant files    │
│  │             │ → Output: research/US-X_research.md        │
│  └──────┬──────┘                                            │
│         │ (compact)                                         │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │   PLANNER   │ → Read research, create detailed plan      │
│  │             │ → Include ACTUAL CODE SNIPPETS             │
│  │             │ → Output: plans/US-X_plan.md               │
│  └──────┬──────┘                                            │
│         │ (compact)                                         │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │ IMPLEMENTER │ → Execute plan step by step                │
│  │             │ → Keep context minimal                     │
│  │             │ → Output: code + submission/V{n}/          │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │   TEACHER   │ → RUN the code, verify it works            │
│  │             │ → Grade against rubric with EVIDENCE       │
│  │             │ → Output: grading/V{n}.md                  │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│      Score ≥ 100? ──YES──→ Next Story                       │
│         │                                                   │
│        NO                                                   │
│         │                                                   │
│         └──→ Back to RESEARCHER (with grading feedback)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent: RESEARCHER

### Role
Explore the codebase and compress findings into a research document.

### Purpose
> "If you don't onboard your agents, they will make stuff up."

The Researcher creates **on-demand compressed context** - a snapshot of the actually-true parts of the codebase that matter for this story.

### Inputs
- `PROJECT_PROMPT.md` - What we're building
- `PROJECT_STATUS.md` - Current story to research
- `src/` - Actual source code (the source of truth)
- Previous `grading/V{n}.md` - What went wrong last time (if retry)

### Process
1. Read the current user story requirements
2. Search codebase for relevant files
3. Understand how the system currently works
4. Find exact files and line numbers that matter
5. Identify potential gotchas or edge cases
6. **Stay objective** - report what IS, not what should be

### Output: `research/US-X_research.md`
```markdown
# Research: US-X - [Story Name]

## Story Requirements
[What we need to accomplish]

## Relevant Files
| File | Lines | Purpose |
|------|-------|---------|
| src/labels.c | 45-120 | Card parsing logic |
| src/csv.c | 80-95 | Field extraction |

## Current Implementation
[How the system currently works]

## Key Code Sections
```c
// src/labels.c:67-82
[actual code snippet]
```

## Data Format Analysis
[For this project: actual CSV column names, formats]

## Gotchas / Edge Cases
- [Thing that might trip us up]

## Recommended Approach
[High-level direction based on findings]
```

### Rules
- Read ACTUAL code, don't guess
- Include EXACT file paths and line numbers
- Keep output concise - this is COMPRESSION
- Focus on what's relevant to THIS story only
- If previous attempt failed, research WHY it failed

---

## Agent: PLANNER

### Role
Create a detailed implementation plan with actual code snippets.

### Purpose
> "A plan so clear the dumbest model won't screw it up."

Plans should include **actual code snippets** showing exactly what will change. Not vague descriptions.

### Inputs
- `research/US-X_research.md` - Compressed codebase understanding
- `PROJECT_PROMPT.md` - Requirements
- `rubric.md` - What we'll be graded on

### Process
1. Read the research document
2. Design the implementation approach
3. Break into specific, ordered steps
4. For each step, include the EXACT code change
5. Include test commands after each step
6. Estimate which files change and how

### Output: `plans/US-X_plan.md`
```markdown
# Plan: US-X - [Story Name]

## Goal
[1-2 sentences]

## Prerequisites
- [ ] Data files exist in data/tmp/
- [ ] Previous code compiles

## Implementation Steps

### Step 1: [Description]
**File:** `src/labels.c`
**Lines:** 67-82

**Current code:**
```c
[existing code]
```

**New code:**
```c
[replacement code]
```

**Test:**
```bash
make && ./main_labels ... | grep "Unique cards"
# Expected: Unique cards tracked: > 0
```

### Step 2: [Description]
...

## Verification
```bash
# Full test sequence
make clean && make
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test.csv
head -5 /tmp/test.csv
wc -l /tmp/test.csv  # Should be > 1
```

## Rollback
[How to undo if it breaks things]
```

### Rules
- Include ACTUAL code snippets (copy from research)
- Each step must be independently testable
- Be explicit about file paths and line numbers
- Don't be vague - "improve the parsing" ❌, "change line 67 from X to Y" ✅
- A human should be able to review this and know EXACTLY what will happen

---

## Agent: IMPLEMENTER

### Role
Execute the plan step by step, keeping context minimal.

### Purpose
> "The implement phase is the least exciting part."

If the plan is good, implementation should be straightforward.

### Inputs
- `plans/US-X_plan.md` - The detailed plan
- `src/` - Current source code

### Process
1. Read the plan
2. Execute each step in order
3. Run the test after each step
4. If a test fails, STOP and report
5. Create submission document with evidence

### Output
- Modified source files
- `submission/V{n}/SUBMISSION.md` with test output

### Rules
- Follow the plan EXACTLY
- Don't improvise or "improve" beyond the plan
- Run tests after EVERY step
- Include ACTUAL command output as evidence
- If something doesn't work, report it honestly

---

## Agent: TEACHER

### Role
Verify the implementation by RUNNING the code.

### Purpose
> "Don't outsource the thinking. Verify the output actually works."

The Teacher must RUN the code, not just read it.

### Inputs
- `rubric.md` - Grading criteria
- `plans/US-X_plan.md` - What was supposed to happen
- `submission/V{n}/SUBMISSION.md` - What the student claims
- `src/` - The actual code

### Mandatory Test Sequence
```bash
# 1. Compilation
make clean && make 2>&1

# 2. Run the main program
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test.csv 2>&1

# 3. Check output is non-empty
head -5 /tmp/test.csv
wc -l /tmp/test.csv

# 4. Check for errors in output
./main_labels ... 2>&1 | grep -i "error\|unique cards\|card pairs"
```

### Output: `grading/V{n}.md`
Must include:
- Actual test output (not placeholders)
- Pass/fail for each rubric criterion
- Specific blocking issues with exact fixes needed
- Acceptance tests for next iteration

### Rules
- MUST run the test commands
- MUST paste actual output
- FAIL if output shows errors or zeros
- Don't give benefit of the doubt
- Be specific about what's wrong and how to fix it

---

## Compaction Points

After each agent runs, context is COMPACTED:

| Agent | Compaction Output | Next Agent Reads |
|-------|-------------------|------------------|
| Researcher | `research/US-X_research.md` | Planner |
| Planner | `plans/US-X_plan.md` | Implementer |
| Implementer | `submission/V{n}/SUBMISSION.md` | Teacher |
| Teacher | `grading/V{n}.md` | Researcher (if retry) |

Each agent starts with FRESH context. No conversation history.

---

## Context Budget Guidelines

| Agent | Target Context Usage | Notes |
|-------|---------------------|-------|
| Researcher | 30-40% | Needs to read lots of code |
| Planner | 20-30% | Reads compressed research |
| Implementer | 20-30% | Reads plan, writes code |
| Teacher | 30-40% | Runs tests, reads output |

If any agent exceeds 50%, the task should be split into smaller stories.

---

## Anti-Patterns

### ❌ Don't Do This
- One long conversation that goes off track
- Vague plans: "improve the CSV parsing"
- Skipping research and jumping to implementation
- Not running the code during grading
- Sub-agents for "roles" (frontend agent, backend agent)

### ✅ Do This Instead
- Fresh context for each phase
- Specific plans: "change line 67 in src/labels.c from X to Y"
- Research first, understand the codebase
- Run actual tests, paste actual output
- Sub-agents for context control (fork to explore, return summary)
