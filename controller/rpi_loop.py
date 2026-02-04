#!/usr/bin/env python3
"""
RPI Loop: Research-Plan-Implement-Grade

Streamlined implementation using shared utilities.
"""
from __future__ import annotations

import sys
import signal
from pathlib import Path
from datetime import datetime

try:
    from .utils import (
        Colors, WORKSPACE, STATE_DIR,
        run_cli, extract_score, load_command_prompt,
        LoopState, load_state, save_state,
        get_current_story, print_header, print_phase, print_score,
    )
except ImportError:
    from utils import (
        Colors, WORKSPACE, STATE_DIR,
        run_cli, extract_score, load_command_prompt,
        LoopState, load_state, save_state,
        get_current_story, print_header, print_phase, print_score,
    )

# ============================================================================
# CONFIGURATION
# ============================================================================

RESEARCH_DIR = WORKSPACE / "research"
PLANS_DIR = WORKSPACE / "plans"
SUBMISSION_DIR = WORKSPACE / "submission"
GRADING_DIR = WORKSPACE / "grading"
STATE_FILE = STATE_DIR / "rpi_state.json"

PROJECT_PROMPT_FILE = WORKSPACE / "PROJECT_PROMPT.md"
PROJECT_STATUS_FILE = WORKSPACE / "PROJECT_STATUS.md"
RUBRIC_FILE = WORKSPACE / "rubric.md"

MAX_ITERATIONS = 10
DEFAULT_TIMEOUT = 600


# ============================================================================
# PROMPT GENERATION
# ============================================================================

def get_researcher_prompt(story: dict, prev_grading: str = "") -> str:
    """Generate researcher prompt."""
    cmd_template = load_command_prompt("research")
    project_prompt = PROJECT_PROMPT_FILE.read_text() if PROJECT_PROMPT_FILE.exists() else ""
    rubric = RUBRIC_FILE.read_text() if RUBRIC_FILE.exists() else ""

    feedback = ""
    if prev_grading:
        feedback = f"""
## PREVIOUS ATTEMPT FAILED - THIS IS A RETRY

Research WHY it failed:

```
{prev_grading[:4000]}
```

DO NOT repeat the same approach.
"""

    return f'''
RESEARCHER PHASE - {story.get("id", "?")}

{cmd_template}

## Current Story: {story.get("id", "?")} - {story.get("name", "")}

{feedback}

## Project Context
{project_prompt[:5000]}

## Rubric
{rubric[:1500]}

## Output
Save to: research/{story.get("id", "?")}_research.md

BEGIN RESEARCH.
'''


def get_planner_prompt(story: dict) -> str:
    """Generate planner prompt."""
    cmd_template = load_command_prompt("plan")

    research_file = RESEARCH_DIR / f"{story.get('id', 'US-1')}_research.md"
    research = research_file.read_text() if research_file.exists() else "No research found."
    rubric = RUBRIC_FILE.read_text() if RUBRIC_FILE.exists() else ""

    return f'''
PLANNER PHASE - {story.get("id", "?")}

{cmd_template}

## Research Findings
{research}

## Rubric
{rubric[:2000]}

## Output
Save to: plans/{story.get("id", "?")}_plan.md

CREATE THE PLAN.
'''


def get_implementer_prompt(story: dict, version: int) -> str:
    """Generate implementer prompt."""
    cmd_template = load_command_prompt("implement")

    plan_file = PLANS_DIR / f"{story.get('id', 'US-1')}_plan.md"
    plan = plan_file.read_text() if plan_file.exists() else "No plan found."

    return f'''
IMPLEMENTER PHASE - {story.get("id", "?")} V{version}

{cmd_template}

## The Plan
{plan}

## Output
Create: submission/V{version}/SUBMISSION.md

IMPLEMENT NOW.
'''


def get_grader_prompt(story: dict, version: int) -> str:
    """Generate grader prompt."""
    cmd_template = load_command_prompt("grade")

    plan_file = PLANS_DIR / f"{story.get('id', 'US-1')}_plan.md"
    plan = plan_file.read_text() if plan_file.exists() else ""
    rubric = RUBRIC_FILE.read_text() if RUBRIC_FILE.exists() else ""

    return f'''
GRADER PHASE - {story.get("id", "?")} V{version}

{cmd_template}

## Plan
{plan[:4000]}

## Rubric
{rubric}

## MANDATORY TESTS

Run these and paste ACTUAL output:

```bash
make clean && make 2>&1
./main_labels data/tmp/powered_premier_games.csv data/raw/cards.csv /tmp/test_labels.csv 2>&1
head -5 /tmp/test_labels.csv
wc -l /tmp/test_labels.csv
```

## Output
Save to: grading/V{version}.md

GRADE NOW.
'''


# ============================================================================
# PHASE EXECUTION
# ============================================================================

def run_phase(cli: str, phase: str, prompt: str, output_file: Path,
              timeout: int = DEFAULT_TIMEOUT) -> tuple[str, bool]:
    """Run a single phase."""
    print_phase(phase)

    output, code = run_cli(cli, prompt, timeout=timeout)

    if output_file.exists():
        print(f"  {Colors.GREEN}✓ {output_file.name} created{Colors.RESET}")
        return output_file.read_text(), True
    else:
        print(f"  {Colors.YELLOW}⚠ Output file not created, saving raw output{Colors.RESET}")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output)
        return output, code == 0


def run_rpi_iteration(cli: str, story: dict, version: int,
                      timeout: int, prev_grading: str = "") -> int:
    """Run one full RPI iteration."""
    print_header(
        f"RPI ITERATION - {story.get('id', '?')} V{version}",
        "Research → Plan → Implement → Grade"
    )

    # Ensure directories exist
    for d in [RESEARCH_DIR, PLANS_DIR, SUBMISSION_DIR / f"V{version}", GRADING_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Phase 1: Research
    run_phase(
        cli, "RESEARCH",
        get_researcher_prompt(story, prev_grading),
        RESEARCH_DIR / f"{story.get('id', 'US-1')}_research.md",
        timeout
    )

    # Phase 2: Plan
    run_phase(
        cli, "PLAN",
        get_planner_prompt(story),
        PLANS_DIR / f"{story.get('id', 'US-1')}_plan.md",
        timeout
    )

    # Phase 3: Implement
    run_phase(
        cli, "IMPLEMENT",
        get_implementer_prompt(story, version),
        SUBMISSION_DIR / f"V{version}" / "SUBMISSION.md",
        timeout
    )

    # Phase 4: Grade
    grading_output, _ = run_phase(
        cli, "GRADE",
        get_grader_prompt(story, version),
        GRADING_DIR / f"V{version}.md",
        timeout
    )

    score = extract_score(grading_output)
    print_score(score)

    return score


# ============================================================================
# MAIN LOOP
# ============================================================================

def run_loop(cli: str, max_iter: int = MAX_ITERATIONS, timeout: int = DEFAULT_TIMEOUT):
    """Run the full RPI loop."""
    print_header(
        "RPI LOOP",
        "Research → Plan → Implement → Grade"
    )

    if not PROJECT_PROMPT_FILE.exists():
        print(f"{Colors.RED}Error: PROJECT_PROMPT.md not found{Colors.RESET}")
        sys.exit(1)

    story = get_current_story(PROJECT_STATUS_FILE, PROJECT_PROMPT_FILE)
    state = load_state(STATE_FILE)
    state.mode = "rpi"
    state.current_story = story.get("id", "US-1")
    state.started_at = state.started_at or datetime.now().isoformat()

    print()
    print(f"  {Colors.CYAN}Story:{Colors.RESET} {story.get('id')} - {story.get('name', '')}")
    print(f"  {Colors.CYAN}CLI:{Colors.RESET} {cli}")
    print(f"  {Colors.CYAN}Timeout:{Colors.RESET} {timeout}s per phase")

    version = state.version + 1
    prev_grading = ""

    for iteration in range(version, max_iter + 1):
        state.version = iteration
        state.iteration = iteration
        save_state(state, STATE_FILE)

        score = run_rpi_iteration(cli, story, iteration, timeout, prev_grading)

        state.score = score
        state.history.append({
            "version": iteration,
            "score": score,
            "time": datetime.now().isoformat()
        })
        save_state(state, STATE_FILE)

        if score >= 100:
            print()
            print(f"{Colors.GREEN}{'═' * 70}{Colors.RESET}")
            print(f"{Colors.GREEN}  SUCCESS! {story.get('id')} complete with {score}/100{Colors.RESET}")
            print(f"{Colors.GREEN}{'═' * 70}{Colors.RESET}")
            return True

        # Get grading for next iteration
        grading_file = GRADING_DIR / f"V{iteration}.md"
        if grading_file.exists():
            prev_grading = grading_file.read_text()

        print(f"\n  {Colors.YELLOW}Score {score}/100 - Retrying...{Colors.RESET}")

    print(f"\n{Colors.YELLOW}Max iterations reached.{Colors.RESET}")
    return False


def show_status():
    """Show RPI loop status."""
    state = load_state(STATE_FILE)
    story = get_current_story(PROJECT_STATUS_FILE, PROJECT_PROMPT_FILE)

    print()
    print(f"{Colors.CYAN}═══ RPI Loop Status ═══{Colors.RESET}")
    print()
    print(f"  Story:   {story.get('id')} - {story.get('name', '')}")
    print(f"  Version: V{state.version}")
    print(f"  Score:   {state.score}/100")
    print()

    # Show artifacts
    research_file = RESEARCH_DIR / f"{story.get('id', 'US-1')}_research.md"
    plan_file = PLANS_DIR / f"{story.get('id', 'US-1')}_plan.md"

    print(f"  {'✓' if research_file.exists() else '○'} research/{story.get('id')}_research.md")
    print(f"  {'✓' if plan_file.exists() else '○'} plans/{story.get('id')}_plan.md")

    for v in range(1, state.version + 2):
        sub_dir = SUBMISSION_DIR / f"V{v}"
        grade_file = GRADING_DIR / f"V{v}.md"
        if sub_dir.exists() or grade_file.exists():
            print(f"  {'✓' if sub_dir.exists() else '○'} submission/V{v}/")
            print(f"  {'✓' if grade_file.exists() else '○'} grading/V{v}.md")

    if state.history:
        print()
        print(f"  {Colors.GRAY}History:{Colors.RESET}")
        for h in state.history[-5:]:
            print(f"    V{h.get('version')}: {h.get('score')}/100")
    print()


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="RPI Loop")
    subparsers = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--cli", choices=["claude", "copilot"], default="claude")
    common.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    common.add_argument("--max-iter", type=int, default=MAX_ITERATIONS)

    subparsers.add_parser("start", parents=[common])
    subparsers.add_parser("resume", parents=[common])
    subparsers.add_parser("status")
    subparsers.add_parser("reset")

    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda s, f: (print(f"\n{Colors.YELLOW}Interrupted.{Colors.RESET}"), sys.exit(130)))

    if args.command == "start":
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        run_loop(args.cli, args.max_iter, args.timeout)

    elif args.command == "resume":
        run_loop(args.cli, args.max_iter, args.timeout)

    elif args.command == "status":
        show_status()

    elif args.command == "reset":
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        print(f"{Colors.GREEN}Reset complete.{Colors.RESET}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
