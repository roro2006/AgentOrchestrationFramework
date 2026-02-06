#!/usr/bin/env python3
"""
Agent Orchestrator

Core orchestration framework with:
- Agent registry
- Task queue
- Parallel execution
- Workflow definitions
"""
from __future__ import annotations

import json
import sys
import signal
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .utils import (
        Colors, WORKSPACE, AGENTS_DIR, COMMANDS_DIR,
        run_cli, load_agent_prompt, print_header,
    )
except ImportError:
    from utils import (
        Colors, WORKSPACE, AGENTS_DIR, COMMANDS_DIR,
        run_cli, load_agent_prompt, print_header,
    )

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    model: str = "sonnet"
    color: str = "blue"


@dataclass
class Task:
    """A task to execute."""
    id: str
    name: str
    agent: str
    prompt: str
    status: str = "pending"
    output: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# AGENT REGISTRY
# ============================================================================

class AgentRegistry:
    """Registry of available agents."""

    BUILTIN = {
        "researcher": AgentConfig("researcher", "Explore codebase, create research docs",
                                  ["Read", "Grep", "Glob", "Bash"], "sonnet", "blue"),
        "planner": AgentConfig("planner", "Create implementation plans",
                               ["Read", "Grep", "Glob"], "sonnet", "cyan"),
        "implementer": AgentConfig("implementer", "Execute plans step by step",
                                   ["Read", "Edit", "Write", "Bash"], "sonnet", "green"),
        "reviewer": AgentConfig("reviewer", "Review work, detect deviations",
                                ["Read", "Bash", "Grep"], "sonnet", "magenta"),
        "locator": AgentConfig("locator", "Find files and patterns",
                               ["Grep", "Glob", "Bash"], "haiku", "gray"),
        "clarifier": AgentConfig("clarifier", "Ask clarifying questions, write specs",
                                 ["Read", "Grep", "Glob"], "sonnet", "cyan"),
    }

    def __init__(self):
        self.agents: dict[str, AgentConfig] = dict(self.BUILTIN)
        self._load_custom()

    def _load_custom(self):
        """Load custom agents from .claude/agents/"""
        if not AGENTS_DIR.exists():
            return

        for f in AGENTS_DIR.glob("*.md"):
            try:
                content = f.read_text()
                if not content.startswith("---"):
                    continue
                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue

                config = {"name": f.stem, "description": "", "tools": [], "model": "sonnet", "color": "blue"}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key, val = key.strip(), val.strip()
                        if key == "name":
                            config["name"] = val
                        elif key == "description":
                            config["description"] = val
                        elif key == "tools":
                            config["tools"] = [t.strip() for t in val.split(",")]
                        elif key == "model":
                            config["model"] = val
                        elif key == "color":
                            config["color"] = val

                self.agents[config["name"]] = AgentConfig(**config)
            except:
                pass

    def get(self, name: str) -> Optional[AgentConfig]:
        return self.agents.get(name)

    def list(self) -> list[str]:
        return list(self.agents.keys())


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class Orchestrator:
    """Main orchestration engine."""

    def __init__(self, cli: str = "claude"):
        self.cli = cli
        self.registry = AgentRegistry()

    def run_task(self, task: Task, timeout: int = 600) -> Task:
        """Run a single task."""
        agent = self.registry.get(task.agent)
        if not agent:
            task.status = "failed"
            task.error = f"Agent '{task.agent}' not found"
            return task

        task.status = "running"
        self._print_task_start(task, agent)

        output, code = run_cli(
            self.cli,
            task.prompt,
            timeout=timeout,
            usage_label=f"orch:{task.agent}",
        )

        task.output = output
        if code == 0:
            task.status = "completed"
            print(f"  {Colors.GREEN}✓ Completed{Colors.RESET}")
        else:
            task.status = "failed"
            task.error = f"Exit code: {code}"
            print(f"  {Colors.RED}✗ Failed{Colors.RESET}")

        return task

    def run_parallel(self, tasks: list[Task], max_workers: int = 3, timeout: int = 600) -> list[Task]:
        """Run tasks in parallel."""
        print(f"\n  {Colors.CYAN}Running {len(tasks)} tasks in parallel...{Colors.RESET}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.run_task, t, timeout): t for t in tasks}
            results = []
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    task = futures[future]
                    task.status = "failed"
                    task.error = str(e)
                    results.append(task)

        return results

    def _print_task_start(self, task: Task, agent: AgentConfig):
        """Print task start."""
        color_map = {
            "blue": Colors.BLUE, "cyan": Colors.CYAN, "green": Colors.GREEN,
            "magenta": Colors.MAGENTA, "red": Colors.RED, "yellow": Colors.YELLOW,
            "gray": Colors.GRAY,
        }
        color = color_map.get(agent.color, Colors.WHITE)
        print()
        print(f"{color}━━━ {agent.name.upper()}: {task.name} ━━━{Colors.RESET}")

    def print_status(self):
        """Print orchestrator status."""
        print()
        print(f"{Colors.CYAN}═══ Orchestrator ═══{Colors.RESET}")
        print()
        print(f"  {Colors.GRAY}Agents: {len(self.registry.list())}{Colors.RESET}")
        for name in sorted(self.registry.list()):
            agent = self.registry.get(name)
            print(f"    • {name}: {agent.description[:50]}...")
        print()


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agent Orchestrator")
    parser.add_argument("--cli", choices=["claude", "copilot"], default="claude")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status")
    subparsers.add_parser("agents")

    run_p = subparsers.add_parser("run")
    run_p.add_argument("agent")
    run_p.add_argument("prompt")
    run_p.add_argument("--timeout", type=int, default=600)

    args = parser.parse_args()

    orch = Orchestrator(cli=args.cli)

    signal.signal(signal.SIGINT, lambda s, f: (print(f"\n{Colors.YELLOW}Interrupted.{Colors.RESET}"), sys.exit(130)))

    if args.command == "status":
        orch.print_status()

    elif args.command == "agents":
        print()
        print(f"{Colors.CYAN}═══ Available Agents ═══{Colors.RESET}")
        for name in sorted(orch.registry.list()):
            agent = orch.registry.get(name)
            print(f"\n  {Colors.BOLD}{name}{Colors.RESET}")
            print(f"  {Colors.GRAY}{agent.description}{Colors.RESET}")
            print(f"  {Colors.GRAY}Tools: {', '.join(agent.tools)}{Colors.RESET}")

    elif args.command == "run":
        task = Task(id="manual", name=f"Run {args.agent}", agent=args.agent, prompt=args.prompt)
        orch.run_task(task, timeout=args.timeout)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
