# Two-Role Iterative Loop System

A structured workflow for iterative spec→submit→grade→revise cycles with strict quality gates.

## Quick Start

### Option 1: Use the Controller Prompt Directly

Copy the contents of `controller/CONTROLLER_PROMPT.md` into your system prompt, then interact naturally:

```
User: Assignment: Create a function that sorts a list of numbers

Claude (TEACHER): [Sets assignment with rubric and DoD]

User: Submit V1

Claude (STUDENT): [Creates submission with evidence]

User: Grade it

Claude (TEACHER): [Grades against rubric, returns score and revisions]

... loop until score = 100 ...
```

### Option 2: Use the Python Controller

```bash
# Check status
python3 controller/run.py status

# Start new assignment
python3 controller/run.py rpi start

# Reset
python3 controller/run.py rpi reset
```

### Option 3: Install as a Package

```bash
pip install -e .

# Run from your project folder to keep outputs local
cd /path/to/your/project

# Usage tracking
# Per-step usage is printed and logged to state/usage.jsonl
# Simple tasks auto-route to a cheaper model; see ORCHESTRATION.md for overrides

# Show status
tracer-orch status

# Run RPI loop
tracer-orch rpi start

# Run Tracer loop
tracer-orch tracer start "Fix the CSV parsing bug"
```

## Directory Structure

```
.
├── README.md                    # This file
├── rubric.md                    # Master rubric (versioned)
├── controller/
│   ├── CONTROLLER_PROMPT.md     # Copy-paste system prompt
│   ├── orchestrator.md          # Workflow documentation
│   ├── run.py                   # Python controller script
│   ├── student_template.md      # Student submission template
│   └── teacher_template.md      # Teacher feedback template
├── submission/
│   └── V{n}/                    # Student deliverables per version
├── grading/
│   └── V{n}.md                  # Teacher feedback per version
└── example/                     # Complete example iteration
    ├── assignment.md
    ├── submission/V1/
    └── grading/V1.md
```

## Core Concepts

### Roles

| Role | Responsibilities | Constraints |
|------|------------------|-------------|
| **STUDENT** | Produce deliverables, provide evidence, self-assess | Cannot modify rubric |
| **TEACHER** | Grade against rubric, provide revision plan | Cannot produce work product |

### Rubric Criteria

| ID | Criterion | Weight | Blocking |
|----|-----------|--------|----------|
| R1 | Requirements Coverage | 20 | Yes |
| R2 | Correctness | 25 | Yes |
| R3 | Reliability | 15 | Yes |
| R4 | Performance | 10 | Yes |
| R5 | Code Quality | 10 | No |
| R6 | Documentation | 10 | No |
| R7 | Reproducibility | 5 | No |
| R8 | Safety/Compliance | 5 | No |

**Blocking = score capped at ≤79 if FAIL**

### Stop Conditions

1. **Success**: Score = 100/100 with Teacher sign-off
2. **Max iterations**: 10 per milestone (then split scope)
3. **Infeasible**: Teacher marks assignment as impossible

## Guardrails

- Teacher must cite rubric ID for all feedback
- Student must include diff summary on revisions (V2+)
- At least one NEW evidence item per iteration
- No rubber-stamping: evidence must be verified

## Example Workflow

See `example/` directory for a complete iteration showing:
- Teacher assignment (`example/assignment.md`)
- Student V1 submission (`example/submission/V1/`)
- Teacher grading (`example/grading/V1.md`)

## Templates

### Student Submission (Required Fields)

```markdown
# Submission: {Title}
**Version:** V{n}

## Goal Statement
## Deliverables List
## Claims List (mapped to R1-R8)
## Evidence Section
## Known Limitations
## How to Reproduce
## Changes Since V{n-1} (V2+ only)
```

### Teacher Feedback (Required Fields)

```markdown
# Grading: V{n}
**Score:** X/100

## Rubric Evaluation Table
## Blocking Issues
## Non-Blocking Improvements
## Acceptance Tests for V{n+1}
## Pass/Fail Checklist
```

## Customization

### Adjusting Rubric Weights

Edit `rubric.md` to change weights or add criteria. Document changes in the changelog.

### Adding Domain-Specific Criteria

Add new rows to the rubric table. Ensure each criterion is:
- Binary or near-binary (PASS/FAIL)
- Has clear evidence requirements
- Specifies whether it's blocking

### Changing Max Iterations

Edit `MAX_ITERATIONS` in `controller/run_loop.py` (default: 10)
