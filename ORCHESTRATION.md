# Agent Orchestration Layer

Multi-agent coordination system for complex software engineering tasks.

## Two Orchestration Modes

### 1. Basic Orchestrator
Direct agent execution with task queues and parallel processing.

### 2. Tracer (Intelligent Orchestration)
Interactive workflow with prompt refinement, spec management, and deviation correction.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│  │   Agent     │   │    Task     │   │  Workflow   │                   │
│  │  Registry   │   │    Queue    │   │   Engine    │                   │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                   │
│         │                 │                 │                           │
│         └────────────┬────┴─────────────────┘                           │
│                      │                                                  │
│              ┌───────▼───────┐                                          │
│              │   Executor    │                                          │
│              │ (CLI Runner)  │                                          │
│              └───────┬───────┘                                          │
│                      │                                                  │
│         ┌────────────┼────────────┐                                     │
│         ▼            ▼            ▼                                     │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐                               │
│    │ Claude  │  │ Copilot │  │  Other  │                               │
│    │   CLI   │  │   CLI   │  │  CLIs   │                               │
│    └─────────┘  └─────────┘  └─────────┘                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install as a package (from repo root)
pip install -e .

# Show status
tracer-orch status

# List available agents
tracer-orch agents -v

# Run a single agent
tracer-orch run researcher "Analyze the CSV parsing in src/csv.c"

# Run RPI loop
tracer-orch rpi start

# Run agents in parallel
tracer-orch parallel "locator,researcher" "Find card tracking code"

# Run a workflow
tracer-orch workflow rpi

# Tracer workflow
tracer-orch tracer start "Fix the CSV parsing bug"
```

## Local (no install)

```bash
cd controller

# Show status
./run.py status

# List available agents
./run.py agents -v

# Run a single agent
./run.py run researcher "Analyze the CSV parsing in src/csv.c"

# Run RPI loop
./run.py rpi start

# Run agents in parallel
./run.py parallel "locator,researcher" "Find card tracking code"

# Run a workflow
./run.py workflow rpi
```

## Available Agents

| Agent | Purpose | Model |
|-------|---------|-------|
| `researcher` | Deep research, codebase analysis, compressed research docs | sonnet |
| `locator` | Fast code finder - files, functions, patterns | haiku |
| `clarifier` | Refine vague requests into specs with acceptance criteria | sonnet |
| `reviewer` | Review implementations, detect deviations, guard quality | sonnet |

## Execution Modes

### Sequential
Run tasks one after another, passing context:
```python
orch.run_task(task1)
orch.run_task(task2)  # Can use output from task1
```

### Parallel
Run independent tasks simultaneously:
```python
tasks = [task1, task2, task3]
results = orch.run_parallel(tasks, max_workers=3)
```

### Workflow
Define multi-step flows with conditions:
```python
workflow = (
    WorkflowBuilder("My Workflow", "Description")
    .step("research", "researcher", "Find relevant code")
    .output_as("research_output")
    .step("analyze", "researcher", "Analyze: {{research_output}}")
    .build()
)
orch.run_workflow(workflow)
```

## Directory Structure

```
controller/
├── run.py           # Unified entry point
├── orchestrator.py  # Orchestration engine
└── rpi_loop.py      # RPI loop implementation

.claude/
├── agents/          # Agent definitions
│   ├── researcher.md
│   ├── locator.md
│   ├── clarifier.md
│   └── reviewer.md
├── commands/        # Command prompts
│   ├── research.md
│   ├── plan.md
│   ├── implement.md
│   └── grade.md
└── workflows/       # Workflow definitions
    └── rpi_loop.yaml
```

## Adding Custom Agents

Create a markdown file in `.claude/agents/`:

```markdown
---
name: my-agent
description: What this agent does
tools: Read, Grep, Glob, Bash
model: sonnet
color: blue
---

You are a specialist at [task].

## Core Responsibilities
...

## Output Format
...
```

## Adding Custom Workflows

Create a YAML file in `.claude/workflows/`:

```yaml
name: my_workflow
description: What this workflow does

context:
  key: value

steps:
  - name: step1
    agent: agent-name
    prompt_file: command.md
    output_key: step1_output

  - name: step2
    agent: other-agent
    prompt_file: another.md
    requires:
      - step1
```

## Context Engineering Principles

1. **Fresh Context**: Each agent starts with clean context
2. **Compression**: Outputs are compressed artifacts, not conversation
3. **Smart Zone**: Keep context usage < 40%
4. **File:Line References**: All claims must be traceable
5. **Verification**: Grade phase must RUN code, not just read it

## CLI Options

```
--cli {claude,copilot}  # Which CLI to use
--timeout SECONDS       # Timeout per task/phase
```

## Environment Variables

```bash
MAX_THINKING_TOKENS=32000  # Set in .claude/settings.json
TRACER_WORKSPACE=/path/to/project  # Override workspace detection
ORCHESTRATOR_WORKSPACE=/path/to/project  # Alias for TRACER_WORKSPACE
```

---

# Tracer: Intelligent Orchestration

Tracer provides a more intelligent workflow with prompt refinement, spec tracking, and deviation correction.

## Tracer Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TRAYCER WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User Request                                                           │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────┐                                                        │
│  │  CLARIFY    │ ◄─── Ask follow-up questions                          │
│  │             │      Refine requirements                              │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │    SPEC     │ ◄─── Generate formal specification                    │
│  │             │      Define acceptance criteria                       │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │   TICKET    │ ◄─── Break into tasks                                 │
│  │             │      Track progress                                   │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐     ┌─────────────┐                                   │
│  │  EXECUTE    │────▶│   REVIEW    │ ◄─── Detect deviations            │
│  │             │     │             │      Verify spec compliance        │
│  └──────┬──────┘     └──────┬──────┘                                   │
│         │                   │                                           │
│         │    ┌──────────────┘                                           │
│         │    │ Deviation?                                               │
│         │    ▼                                                          │
│         │  ┌─────────────┐                                              │
│         │  │   CORRECT   │ ◄─── Fix issues                             │
│         │  │             │      Re-verify                              │
│         │  └──────┬──────┘                                              │
│         │         │                                                     │
│         ▼         ▼                                                     │
│  ┌─────────────────────┐                                                │
│  │     COMPLETE        │                                                │
│  └─────────────────────┘                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tracer Commands

```bash
# Start new work with interactive refinement
./run.py tracer start "Fix the CSV parsing bug"

# Start interactively (prompts for input)
./run.py tracer start

# Check Tracer status
./run.py tracer status

# Resume work on a ticket
./run.py tracer resume TKT-ABC123

# List all specs and tickets
./run.py tracer list
```

## Key Features

### 1. Prompt Refinement
Tracer asks 3-5 clarifying questions before starting work:
- **Scope**: What exactly should be included/excluded?
- **Approach**: Any preferred implementation methods?
- **Constraints**: Performance, compatibility limits?
- **Acceptance**: How do we verify success?

### 2. Spec Management
Creates and tracks formal specifications:
- Requirements with specific, measurable criteria
- Acceptance criteria that can be tested
- Constraints and out-of-scope items
- Version history

Specs are saved to `specs/SPEC-XXXXX.md`

### 3. Ticket Tracking
Breaks specs into trackable work tickets:
- Task breakdown with types (research/code/test)
- Progress percentage
- Blocker tracking
- Iteration history

Tickets are saved to `tickets/TKT-XXXXX.md`

### 4. Deviation Detection
Automatically detects when implementation deviates from spec:

| Type | Description |
|------|-------------|
| `OFF_TOPIC` | Added things not in spec |
| `WRONG_APPROACH` | Violated constraints |
| `INCOMPLETE` | Missing requirements |
| `OVER_ENGINEERED` | Unnecessary complexity |
| `SPEC_VIOLATION` | Contradicts spec |

### 5. Automatic Correction
When deviations are detected:
1. Analyzes the deviation type
2. Generates correction instructions
3. Applies corrections
4. Re-verifies against spec
5. Records in iteration history

## Tracer Agents

| Agent | Role |
|-------|------|
| `clarifier` | Asks clarifying questions AND creates formal specifications |
| `reviewer` | Detects deviations from spec, guards quality |
| `researcher` | Deep codebase analysis for understanding context |
| `locator` | Fast code finding for implementation |

## Directory Structure

```
specs/
├── SPEC-ABC123.json    # Spec data
└── SPEC-ABC123.md      # Human-readable spec

tickets/
├── TKT-ABC123.json     # Ticket data
└── TKT-ABC123.md       # Human-readable ticket

progress/
└── ...                 # Progress tracking

state/
└── tracer_state.json  # Tracer state
```

## Example Session

```
$ ./run.py tracer start "Fix CSV parsing"

╔══════════════════════════════════════════════════════════════════════════╗
║  TRAYCER - Intelligent Agent Orchestration                               ║
║  Refine → Spec → Execute → Verify                                        ║
╚══════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════╗
║  CLARIFY       Refining your request through questions                   ║
╚══════════════════════════════════════════════════════════════════════════╝

  I have 4 questions to clarify your request:

  1. [SCOPE]
     Which CSV files should the parser handle - game data, cards, or both?

  Your answer: Both game data and cards CSV files

  2. [APPROACH]
     Should we follow RFC 4180 for quoted field handling?

  Your answer: Yes, RFC 4180 compliant

  3. [CONSTRAINTS]
     Are there memory or performance constraints?

  Your answer: Should handle files up to 1GB

  4. [ACCEPTANCE]
     How will you verify it's working?

  Your answer: Unique cards tracked should be > 0

  ╔════════════════════════════════════════════════════════════════╗
  ║  ✓ Spec Created: SPEC-A1B2C3D4                                 ║
  ╚════════════════════════════════════════════════════════════════╝

  Title: RFC 4180 Compliant CSV Parser
  Requirements: 4
  Acceptance Criteria: 3
  Saved to: specs/SPEC-A1B2C3D4.md

  Ready to create ticket and execute?
  [Y/n]: Y

  [Continues with ticket creation and execution...]
```

## Comparison: RPI vs Tracer

| Feature | RPI Loop | Tracer |
|---------|----------|---------|
| Prompt Refinement | No | Yes (interactive) |
| Spec Management | No | Yes (formal specs) |
| Ticket Tracking | Basic | Detailed |
| Deviation Detection | Via grading | Automatic |
| Correction | Manual retry | Automatic |
| Best For | Known tasks | Vague requests |
