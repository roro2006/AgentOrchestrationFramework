#!/usr/bin/env python3
"""
Tracer: Intelligent Agent Orchestration

Features:
- Prompt refinement through follow-up questions
- Spec and ticket management
- Deviation detection and correction
"""
from __future__ import annotations

import json
import re
import sys
import signal
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

    try:
        from .utils import (
            Colors, WORKSPACE, STATE_DIR,
            run_cli, extract_score, compact_text, load_project_context,
            LoopState, load_state, save_state,
            print_header, print_phase, print_progress,
        )
    except ImportError:
        from utils import (
            Colors, WORKSPACE, STATE_DIR,
            run_cli, extract_score, compact_text, load_project_context,
            LoopState, load_state, save_state,
            print_header, print_phase, print_progress,
        )

# ============================================================================
# CONFIGURATION
# ============================================================================

SPECS_DIR = WORKSPACE / "specs"
TICKETS_DIR = WORKSPACE / "tickets"
STATE_FILE = STATE_DIR / "tracer_state.json"


# ============================================================================
# ENUMS
# ============================================================================

class TicketStatus(Enum):
    DRAFT = "draft"
    REFINED = "refined"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Clarification:
    question: str
    answer: Optional[str] = None
    category: str = "general"


@dataclass
class Spec:
    id: str
    title: str
    description: str
    requirements: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    clarifications: list[Clarification] = field(default_factory=list)
    version: int = 1
    status: str = "draft"

    def to_markdown(self) -> str:
        md = f"# Spec: {self.title}\n\n**ID:** {self.id}\n**Status:** {self.status}\n\n"
        md += f"## Description\n\n{self.description}\n\n## Requirements\n\n"
        for i, r in enumerate(self.requirements, 1):
            md += f"{i}. {r}\n"
        md += "\n## Acceptance Criteria\n\n"
        for ac in self.acceptance_criteria:
            md += f"- [ ] {ac}\n"
        if self.constraints:
            md += "\n## Constraints\n\n"
            for c in self.constraints:
                md += f"- {c}\n"
        return md


@dataclass
class Ticket:
    id: str
    spec_id: str
    title: str
    description: str
    status: TicketStatus = TicketStatus.DRAFT
    tasks: list[dict] = field(default_factory=list)
    progress: int = 0
    deviations: list[dict] = field(default_factory=list)
    iterations: list[dict] = field(default_factory=list)


# ============================================================================
# TRAYCER
# ============================================================================

class Tracer:
    def __init__(self, cli: str = "claude"):
        self.cli = cli
        self.state = load_state(STATE_FILE)
        self.state.mode = "tracer"
        self.specs: dict[str, Spec] = {}
        self.tickets: dict[str, Ticket] = {}

        SPECS_DIR.mkdir(parents=True, exist_ok=True)
        TICKETS_DIR.mkdir(parents=True, exist_ok=True)

        self._load_data()

    def _load_data(self):
        """Load specs and tickets from files."""
        for f in SPECS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                self.specs[data["id"]] = Spec(**{
                    k: v for k, v in data.items()
                    if k in Spec.__dataclass_fields__
                })
            except:
                pass

        for f in TICKETS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                data["status"] = TicketStatus(data.get("status", "draft"))
                self.tickets[data["id"]] = Ticket(**{
                    k: v for k, v in data.items()
                    if k in Ticket.__dataclass_fields__
                })
            except:
                pass

    def _save_spec(self, spec: Spec):
        """Save spec to file."""
        data = {
            "id": spec.id, "title": spec.title, "description": spec.description,
            "requirements": spec.requirements, "acceptance_criteria": spec.acceptance_criteria,
            "constraints": spec.constraints, "out_of_scope": spec.out_of_scope,
            "clarifications": [{"question": c.question, "answer": c.answer, "category": c.category}
                             for c in spec.clarifications],
            "version": spec.version, "status": spec.status,
        }
        (SPECS_DIR / f"{spec.id}.json").write_text(json.dumps(data, indent=2))
        (SPECS_DIR / f"{spec.id}.md").write_text(spec.to_markdown())
        self.specs[spec.id] = spec

    def _save_ticket(self, ticket: Ticket):
        """Save ticket to file."""
        data = {
            "id": ticket.id, "spec_id": ticket.spec_id, "title": ticket.title,
            "description": ticket.description, "status": ticket.status.value,
            "tasks": ticket.tasks, "progress": ticket.progress,
            "deviations": ticket.deviations, "iterations": ticket.iterations,
        }
        (TICKETS_DIR / f"{ticket.id}.json").write_text(json.dumps(data, indent=2))
        self.tickets[ticket.id] = ticket

    def _spec_context(self, spec: Spec, include: tuple[str, ...], max_chars: int) -> str:
        spec_file = SPECS_DIR / f"{spec.id}.md"
        if spec_file.exists():
            doc = load_project_context(spec_file, max_chars=max_chars, story_id=spec.id, story_name=spec.title)
            if doc:
                return doc

        parts = []
        if "title" in include:
            parts.append(f"TITLE: {spec.title}")
        if "description" in include:
            parts.append(f"DESCRIPTION: {spec.description}")
        if "requirements" in include:
            parts.append(f"REQUIREMENTS: {spec.requirements}")
        if "acceptance" in include:
            parts.append(f"ACCEPTANCE: {spec.acceptance_criteria}")
        if "constraints" in include:
            parts.append(f"CONSTRAINTS: {spec.constraints}")
        if "out_of_scope" in include:
            parts.append(f"OUT_OF_SCOPE: {spec.out_of_scope}")
        return compact_text("\n".join(parts), max_chars)

    # =========================================================================
    # CLARIFICATION PHASE
    # =========================================================================

    def clarify(self, request: str) -> Spec:
        """Refine request through clarifying questions."""
        print_phase("CLARIFY", "Refining your request")

        spec_id = f"SPEC-{hashlib.md5(request.encode()).hexdigest()[:8].upper()}"
        spec = Spec(id=spec_id, title="", description=request)

        self.state.spec_id = spec_id
        save_state(self.state, STATE_FILE)

        # Generate questions
        questions = self._generate_questions(request)
        spec.clarifications = questions

        if not questions:
            print(f"  {Colors.GREEN}✓ Request is clear{Colors.RESET}")
            spec.status = "refined"
            self._save_spec(spec)
            return spec

        print(f"\n  {Colors.CYAN}I have {len(questions)} questions:{Colors.RESET}\n")

        for i, q in enumerate(questions, 1):
            print(f"  {Colors.BOLD}{i}.{Colors.RESET} [{q.category.upper()}] {q.question}")
            answer = input(f"  {Colors.YELLOW}>{Colors.RESET} ").strip()
            q.answer = answer if answer else "[skipped]"
            spec.clarifications[i-1] = q

        # Refine spec
        spec = self._refine_spec(spec)
        spec.status = "refined"
        self._save_spec(spec)

        print(f"\n  {Colors.GREEN}✓ Spec created: {spec.id}{Colors.RESET}")
        print(f"    Title: {spec.title}")
        print(f"    Requirements: {len(spec.requirements)}")

        return spec

    def _generate_questions(self, request: str) -> list[Clarification]:
        """Generate clarifying questions."""
        request_text = compact_text(request, 2000)
        prompt = f'''
Given this request, generate 3-4 clarifying questions.

REQUEST: {request_text}

Categories: scope, approach, constraints, acceptance

Output JSON array:
[{{"question": "...", "category": "scope"}}]

Only output the JSON.
'''
        output, _ = run_cli(
            self.cli,
            prompt,
            timeout=120,
            show_output=False,
            usage_label="tracer:clarify:questions",
        )

        try:
            match = re.search(r'\[[\s\S]*\]', output)
            if match:
                data = json.loads(match.group())
                return [Clarification(q["question"], category=q.get("category", "general"))
                       for q in data]
        except:
            pass

        return [
            Clarification("What specific files should this affect?", category="scope"),
            Clarification("Any constraints I should know about?", category="constraints"),
            Clarification("How will you verify it works?", category="acceptance"),
        ]

    def _refine_spec(self, spec: Spec) -> Spec:
        """Refine spec from clarifications."""
        clarifications = "\n".join([
            f"Q: {c.question}\nA: {c.answer or '[skipped]'}"
            for c in spec.clarifications
        ])
        clarifications = compact_text(clarifications, 2000)
        request_text = compact_text(spec.description, 2000)

        prompt = f'''
Create a specification from this request and clarifications.

REQUEST: {request_text}

        CLARIFICATIONS:
        {clarifications}

Output JSON:
{{"title": "...", "description": "...", "requirements": [...], "acceptance_criteria": [...], "constraints": [...], "out_of_scope": [...]}}

Only output JSON.
'''
        output, _ = run_cli(
            self.cli,
            prompt,
            timeout=120,
            show_output=False,
            usage_label="tracer:clarify:spec",
        )

        try:
            match = re.search(r'\{[\s\S]*\}', output)
            if match:
                data = json.loads(match.group())
                spec.title = data.get("title", "Untitled")
                spec.description = data.get("description", spec.description)
                spec.requirements = data.get("requirements", [])
                spec.acceptance_criteria = data.get("acceptance_criteria", [])
                spec.constraints = data.get("constraints", [])
                spec.out_of_scope = data.get("out_of_scope", [])
        except:
            spec.title = "Untitled"

        return spec

    # =========================================================================
    # TICKET CREATION
    # =========================================================================

    def create_ticket(self, spec: Spec) -> Ticket:
        """Create ticket from spec."""
        print_phase("TICKET", "Creating work ticket")

        ticket = Ticket(
            id=f"TKT-{spec.id.split('-')[1]}",
            spec_id=spec.id,
            title=spec.title,
            description=spec.description,
            status=TicketStatus.REFINED,
        )

        # Generate tasks
        spec_context = self._spec_context(spec, ("title", "requirements"), 2000)
        prompt = f'''
Break this spec into tasks:

{spec_context}

Output JSON array:
[{{"name": "Task name", "type": "research|code|test"}}]
'''
        output, _ = run_cli(
            self.cli,
            prompt,
            timeout=120,
            show_output=False,
            usage_label="tracer:ticket:tasks",
        )

        try:
            match = re.search(r'\[[\s\S]*\]', output)
            if match:
                tasks = json.loads(match.group())
                ticket.tasks = [{"name": t["name"], "type": t.get("type", "code"), "done": False}
                               for t in tasks]
        except:
            ticket.tasks = [
                {"name": "Research", "type": "research", "done": False},
                {"name": "Implement", "type": "code", "done": False},
                {"name": "Test", "type": "test", "done": False},
            ]

        self.state.ticket_id = ticket.id
        save_state(self.state, STATE_FILE)
        self._save_ticket(ticket)

        print(f"\n  {Colors.GREEN}✓ Ticket created: {ticket.id}{Colors.RESET}")
        for t in ticket.tasks:
            print(f"    • {t['name']}")

        return ticket

    # =========================================================================
    # EXECUTION WITH DEVIATION DETECTION
    # =========================================================================

    def execute(self, ticket: Ticket) -> Ticket:
        """Execute ticket with deviation detection."""
        print_phase("EXECUTE", f"Working on {ticket.id}")

        spec = self.specs.get(ticket.spec_id)
        if not spec:
            print(f"  {Colors.RED}Spec not found{Colors.RESET}")
            return ticket

        ticket.status = TicketStatus.IN_PROGRESS
        self._save_ticket(ticket)

        max_iterations = 5
        for iteration in range(1, max_iterations + 1):
            self.state.iteration = iteration
            save_state(self.state, STATE_FILE)

            print(f"\n  {Colors.CYAN}━━━ Iteration {iteration} ━━━{Colors.RESET}")

            # Run implementation
            impl_output = self._run_implementation(spec, ticket)

            # Check for deviations
            deviations = self._detect_deviations(spec, impl_output)

            if deviations:
                self.state.deviations_detected += len(deviations)
                ticket.deviations.extend(deviations)
                self._save_ticket(ticket)

                print(f"\n  {Colors.YELLOW}⚠ {len(deviations)} deviation(s) detected{Colors.RESET}")

                # Try correction
                if self._correct_deviations(spec, deviations):
                    self.state.deviations_corrected += 1
                    print(f"  {Colors.GREEN}✓ Corrected{Colors.RESET}")
                else:
                    ticket.status = TicketStatus.BLOCKED
                    self._save_ticket(ticket)
                    break
            else:
                print(f"  {Colors.GREEN}✓ No deviations{Colors.RESET}")

                if self._verify_completion(spec):
                    ticket.status = TicketStatus.COMPLETED
                    ticket.progress = 100
                    for t in ticket.tasks:
                        t["done"] = True
                    self._save_ticket(ticket)
                    print(f"\n  {Colors.GREEN}✓ Complete!{Colors.RESET}")
                    break

            ticket.iterations.append({"num": iteration, "result": "deviation" if deviations else "ok"})
            done = sum(1 for t in ticket.tasks if t.get("done"))
            ticket.progress = int((done / len(ticket.tasks)) * 100) if ticket.tasks else 0
            self._save_ticket(ticket)

            print_progress(ticket.progress, 100)

        save_state(self.state, STATE_FILE)
        return ticket

    def _stream_updates(self, label: str):
        """Stream live updates during execution."""
        def _on_line(line: str):
            display = line.rstrip()
            if not display.strip():
                return
            if len(display) > 200:
                display = display[:200] + "..."
            print(f"  {Colors.GRAY}[{label}]{Colors.RESET} {display}")
        return _on_line

    def _run_implementation(self, spec: Spec, ticket: Ticket) -> str:
        """Run implementation."""
        pending = [t for t in ticket.tasks if not t.get("done")]
        if not pending:
            return ""

        task = pending[0]
        spec_context = self._spec_context(spec, ("title", "requirements", "acceptance"), 3000)
        prompt = f'''
Implement this task from the spec:

{spec_context}

TASK: {task["name"]}

        Follow the spec exactly. Do not add unrequested features.
        '''
        print(f"  {Colors.GRAY}Task: {task['name']}{Colors.RESET}")
        output, code = run_cli(
            self.cli,
            prompt,
            timeout=600,
            on_line=self._stream_updates("IMPLEMENT"),
            show_output=False,
            usage_label="tracer:execute:implement",
        )

        if code == 0:
            task["done"] = True
            self._save_ticket(ticket)

        return output

    def _detect_deviations(self, spec: Spec, output: str) -> list[dict]:
        """Detect deviations from spec."""
        if not output or len(output) < 100:
            return []

        spec_context = self._spec_context(spec, ("title", "requirements", "out_of_scope"), 3000)
        prompt = f'''
Check if this implementation follows the spec:

{spec_context}

OUTPUT (excerpt): {output[:2000]}

Look for: OFF_TOPIC, WRONG_APPROACH, INCOMPLETE, OVER_ENGINEERED, SPEC_VIOLATION

        Output JSON array of deviations (empty if none):
        [{{"type": "...", "description": "...", "correction": "..."}}]
        '''
        result, _ = run_cli(
            self.cli,
            prompt,
            timeout=120,
            on_line=self._stream_updates("REVIEW"),
            show_output=False,
            usage_label="tracer:execute:review",
        )

        try:
            match = re.search(r'\[[\s\S]*?\]', result)
            if match:
                deviations = json.loads(match.group())
                return [d for d in deviations if d.get("type") and d.get("description")]
        except:
            pass
        return []

    def _correct_deviations(self, spec: Spec, deviations: list[dict]) -> bool:
        """Attempt to correct deviations."""
        corrections = [d.get("correction", "") for d in deviations if d.get("correction")]
        if not corrections:
            return False

        spec_context = self._spec_context(spec, ("title", "requirements", "constraints"), 2000)
        prompt = f'''
Apply these corrections to fix deviations:

{spec_context}
CORRECTIONS: {corrections}

        Fix the issues and verify against the spec.
        '''
        _, code = run_cli(
            self.cli,
            prompt,
            timeout=600,
            on_line=self._stream_updates("CORRECT"),
            show_output=False,
            usage_label="tracer:execute:correct",
        )
        return code == 0

    def _verify_completion(self, spec: Spec) -> bool:
        """Verify acceptance criteria are met."""
        acceptance = compact_text("\n".join(spec.acceptance_criteria), 1500)
        prompt = f'''
Verify all acceptance criteria are met:

{acceptance}

        Run tests and check. Output JSON:
        {{"all_met": true/false}}
        '''
        output, _ = run_cli(
            self.cli,
            prompt,
            timeout=300,
            on_line=self._stream_updates("VERIFY"),
            show_output=False,
            usage_label="tracer:execute:verify",
        )

        try:
            match = re.search(r'\{[\s\S]*\}', output)
            if match:
                return json.loads(match.group()).get("all_met", False)
        except:
            pass
        return False

    # =========================================================================
    # MAIN WORKFLOW
    # =========================================================================

    def _run_flow(self, request: str, auto_confirm: bool):
        """Run full Tracer workflow."""
        print_header("TRAYCER", "Refine → Spec → Execute → Verify")

        self.state.started_at = datetime.now().isoformat()
        save_state(self.state, STATE_FILE)

        # Clarify
        spec = self.clarify(request)

        # Confirm
        if not auto_confirm:
            print(f"\n  {Colors.YELLOW}Create ticket and execute? [Y/n]{Colors.RESET}")
            if input("  > ").strip().lower() in ['n', 'no']:
                print(f"  {Colors.GRAY}Stopped. Spec saved.{Colors.RESET}")
                return

        # Create ticket
        ticket = self.create_ticket(spec)

        # Execute
        ticket = self.execute(ticket)

        # Summary
        color = Colors.GREEN if ticket.status == TicketStatus.COMPLETED else Colors.YELLOW
        print()
        print(f"{color}{'═' * 50}{Colors.RESET}")
        print(f"{color}  {'COMPLETED' if ticket.status == TicketStatus.COMPLETED else 'NEEDS ATTENTION'}{Colors.RESET}")
        print(f"  Spec: {spec.id}")
        print(f"  Ticket: {ticket.id}")
        print(f"  Status: {ticket.status.value}")
        print(f"  Progress: {ticket.progress}%")
        print(f"{color}{'═' * 50}{Colors.RESET}")

    def start(self, request: str):
        """Run full Tracer workflow with confirmation."""
        self._run_flow(request, auto_confirm=False)

    def run_all(self, request: str):
        """Run full Tracer workflow without confirmation."""
        self._run_flow(request, auto_confirm=True)

    def print_status(self):
        """Print status."""
        print()
        print(f"{Colors.CYAN}═══ Tracer Status ═══{Colors.RESET}")
        print()
        print(f"  Specs: {len(self.specs)}")
        print(f"  Tickets: {len(self.tickets)}")
        print(f"  Deviations: {self.state.deviations_detected} detected, {self.state.deviations_corrected} corrected")

        if self.state.ticket_id:
            ticket = self.tickets.get(self.state.ticket_id)
            if ticket:
                print(f"\n  Current: {ticket.id} - {ticket.title}")
                print(f"  Status: {ticket.status.value}")
                print(f"  Progress: {ticket.progress}%")

        if self.tickets:
            print(f"\n  {Colors.GRAY}Tickets:{Colors.RESET}")
            for tid, t in list(self.tickets.items())[-5:]:
                icon = "✅" if t.status == TicketStatus.COMPLETED else "🔄"
                print(f"    {icon} {tid}: {t.title[:40]}")
        print()


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Tracer")
    parser.add_argument("--cli", choices=["claude", "copilot"], default="claude")

    subparsers = parser.add_subparsers(dest="command")
    start_p = subparsers.add_parser("start")
    start_p.add_argument("request", nargs="?")
    run_p = subparsers.add_parser("run")
    run_p.add_argument("request", nargs="?")
    subparsers.add_parser("status")
    resume_p = subparsers.add_parser("resume")
    resume_p.add_argument("ticket_id")
    subparsers.add_parser("list")

    args = parser.parse_args()

    tracer = Tracer(cli=args.cli)

    signal.signal(signal.SIGINT, lambda s, f: (print(f"\n{Colors.YELLOW}Interrupted.{Colors.RESET}"), sys.exit(130)))

    if args.command == "start":
        if args.request:
            tracer.start(args.request)
        else:
            print(f"\n{Colors.CYAN}What would you like to accomplish?{Colors.RESET}")
            request = input(f"{Colors.YELLOW}> {Colors.RESET}")
            if request.strip():
                tracer.start(request)
    elif args.command == "run":
        if args.request:
            tracer.run_all(args.request)
        else:
            print(f"\n{Colors.CYAN}What would you like to accomplish?{Colors.RESET}")
            request = input(f"{Colors.YELLOW}> {Colors.RESET}")
            if request.strip():
                tracer.run_all(request)

    elif args.command == "status":
        tracer.print_status()

    elif args.command == "resume":
        ticket = tracer.tickets.get(args.ticket_id)
        if ticket:
            tracer.execute(ticket)
        else:
            print(f"{Colors.RED}Ticket not found{Colors.RESET}")

    elif args.command == "list":
        print(f"\n{Colors.CYAN}Specs:{Colors.RESET}")
        for s in tracer.specs.values():
            print(f"  • {s.id}: {s.title}")
        print(f"\n{Colors.CYAN}Tickets:{Colors.RESET}")
        for t in tracer.tickets.values():
            print(f"  • {t.id}: {t.title} [{t.status.value}]")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
