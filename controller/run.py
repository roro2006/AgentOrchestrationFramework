#!/usr/bin/env python3
"""
Unified Entry Point for Agent Orchestration

Simple interface to run agents, workflows, and the RPI loop.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add controller to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from .orchestrator import Orchestrator
    from .utils import Colors
    from .rpi_loop import run_loop, show_status, load_state, get_current_story
    from .tracer import Tracer
except ImportError:
    from orchestrator import Orchestrator
    from utils import Colors
    from rpi_loop import run_loop, show_status, load_state, get_current_story
    from tracer import Tracer


def cmd_status(args):
    """Show project and orchestrator status."""
    print()
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}  Project Status{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    show_status()

    print()
    orch = Orchestrator()
    orch.print_status()


def cmd_agents(args):
    """List available agents."""
    orch = Orchestrator()

    color_map = {
        "blue": Colors.BLUE, "cyan": Colors.CYAN, "green": Colors.GREEN,
        "magenta": Colors.MAGENTA, "red": Colors.RED, "yellow": Colors.YELLOW,
        "gray": Colors.GRAY,
    }

    print()
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}  Available Agents{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print()

    for name in sorted(orch.registry.list()):
        agent = orch.registry.get(name)
        color = color_map.get(agent.color, Colors.WHITE)
        print(f"  {color}●{Colors.RESET} {name}")
        print(f"    {Colors.GRAY}{agent.description[:60]}...{Colors.RESET}")
        if args.verbose:
            print(f"    {Colors.GRAY}Tools: {', '.join(agent.tools)}{Colors.RESET}")
            print(f"    {Colors.GRAY}Model: {agent.model}{Colors.RESET}")
        print()


def cmd_run(args):
    """Run a single agent with a prompt."""
    orch = Orchestrator(cli=args.cli)

    if not orch.registry.get(args.agent):
        print(f"{Colors.RED}Error: Unknown agent '{args.agent}'{Colors.RESET}")
        print(f"Available agents: {', '.join(orch.registry.list())}")
        sys.exit(1)

    task = orch.create_task(
        name=f"Manual: {args.agent}",
        agent=args.agent,
        prompt=args.prompt,
    )

    result = orch.run_task(task, timeout=args.timeout)

    if result.status.value == "completed":
        print(f"\n{Colors.GREEN}✓ Task completed{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}✗ Task failed: {result.error}{Colors.RESET}")
        sys.exit(1)


def cmd_rpi(args):
    """Run the RPI loop."""
    if args.subcommand == "start":
        from rpi_loop import STATE_FILE
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        run_loop(args.cli, args.max_iter, args.timeout)

    elif args.subcommand == "resume":
        run_loop(args.cli, args.max_iter, args.timeout)

    elif args.subcommand == "status":
        show_status()

    elif args.subcommand == "reset":
        from rpi_loop import STATE_FILE
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            print(f"{Colors.GREEN}✓ State reset{Colors.RESET}")
        else:
            print(f"{Colors.GRAY}No state to reset{Colors.RESET}")


def cmd_parallel(args):
    """Run multiple agents in parallel."""
    orch = Orchestrator(cli=args.cli)

    agents = args.agents.split(",")
    tasks = []

    for agent_name in agents:
        agent_name = agent_name.strip()
        if not orch.registry.get(agent_name):
            print(f"{Colors.YELLOW}Warning: Unknown agent '{agent_name}', skipping{Colors.RESET}")
            continue

        task = orch.create_task(
            name=f"Parallel: {agent_name}",
            agent=agent_name,
            prompt=args.prompt,
        )
        tasks.append(task)

    if not tasks:
        print(f"{Colors.RED}No valid agents specified{Colors.RESET}")
        sys.exit(1)

    print(f"\n{Colors.CYAN}Running {len(tasks)} agents in parallel...{Colors.RESET}")
    results = orch.run_parallel(tasks, max_workers=args.workers, timeout=args.timeout)

    print(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}  Parallel Execution Results{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")

    for result in results:
        status_icon = "✓" if result.status.value == "completed" else "✗"
        status_color = Colors.GREEN if result.status.value == "completed" else Colors.RED
        print(f"  {status_color}{status_icon}{Colors.RESET} {result.agent}: {result.status.value}")


def cmd_tracer(args):
    """Run Tracer workflow."""
    tracer = Tracer(cli=args.cli)

    if args.subcommand == "start":
        if args.request:
            tracer.start(args.request)
        else:
            print(f"\n{Colors.CYAN}What would you like to accomplish?{Colors.RESET}")
            request = input(f"{Colors.YELLOW}> {Colors.RESET}")
            if request.strip():
                tracer.start(request)

    elif args.subcommand == "status":
        tracer.print_status()

    elif args.subcommand == "resume":
        ticket = tracer.tickets.get(args.ticket_id)
        if ticket:
            spec = tracer.specs.get(ticket.spec_id)
            if spec:
                tracer.execute(ticket)
        else:
            print(f"{Colors.RED}Ticket not found: {args.ticket_id}{Colors.RESET}")

    elif args.subcommand == "list":
        print(f"\n{Colors.CYAN}Specs:{Colors.RESET}")
        for sid, spec in tracer.specs.items():
            print(f"  • {sid}: {spec.title}")

        print(f"\n{Colors.CYAN}Tickets:{Colors.RESET}")
        for tid, ticket in tracer.tickets.items():
            status = ticket.status.value
            print(f"  • {tid}: {ticket.title} [{status}]")
        print()


def cmd_workflow(args):
    """Run a predefined workflow."""
    # NOTE: Workflow feature is not yet implemented
    # Use 'rpi start' for the RPI loop instead
    print(f"{Colors.YELLOW}Workflow feature not yet implemented.{Colors.RESET}")
    print(f"Use './run.py rpi start' for the RPI loop.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="run",
        description="Unified Agent Orchestration Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./run.py status                           # Show status
  ./run.py agents                           # List agents
  ./run.py run researcher "Research CSV parsing"
  ./run.py rpi start                        # Start RPI loop
  ./run.py parallel "locator,researcher" "Find CSV code"
  ./run.py workflow rpi                     # Run RPI workflow
  ./run.py tracer start "Fix the CSV bug"   # Start Tracer workflow
  ./run.py tracer status                    # Show Tracer status
        """
    )

    # Global options
    parser.add_argument("--cli", choices=["claude", "copilot"], default="claude",
                       help="CLI to use (default: claude)")
    parser.add_argument("--timeout", type=int, default=600,
                       help="Timeout in seconds (default: 600)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Status command
    subparsers.add_parser("status", help="Show project and orchestrator status")

    # Agents command
    agents_p = subparsers.add_parser("agents", help="List available agents")
    agents_p.add_argument("-v", "--verbose", action="store_true")

    # Run command
    run_p = subparsers.add_parser("run", help="Run a single agent")
    run_p.add_argument("agent", help="Agent name")
    run_p.add_argument("prompt", help="Prompt for the agent")

    # RPI command
    rpi_p = subparsers.add_parser("rpi", help="RPI loop operations")
    rpi_sub = rpi_p.add_subparsers(dest="subcommand", required=True)
    rpi_start = rpi_sub.add_parser("start", help="Start fresh")
    rpi_start.add_argument("--max-iter", type=int, default=10)
    rpi_resume = rpi_sub.add_parser("resume", help="Resume from state")
    rpi_resume.add_argument("--max-iter", type=int, default=10)
    rpi_sub.add_parser("status", help="Show RPI status")
    rpi_sub.add_parser("reset", help="Reset RPI state")

    # Parallel command
    parallel_p = subparsers.add_parser("parallel", help="Run agents in parallel")
    parallel_p.add_argument("agents", help="Comma-separated agent names")
    parallel_p.add_argument("prompt", help="Shared prompt")
    parallel_p.add_argument("--workers", type=int, default=3)

    # Workflow command
    wf_p = subparsers.add_parser("workflow", help="Run a workflow")
    wf_p.add_argument("workflow", choices=["rpi", "research"], help="Workflow name")
    wf_p.add_argument("--query", help="Query for research workflow")

    # Tracer command
    tracer_p = subparsers.add_parser("tracer", help="Tracer intelligent orchestration")
    tracer_sub = tracer_p.add_subparsers(dest="subcommand", required=True)
    tracer_start = tracer_sub.add_parser("start", help="Start new work")
    tracer_start.add_argument("request", nargs="?", help="What to accomplish")
    tracer_sub.add_parser("status", help="Show Tracer status")
    tracer_resume = tracer_sub.add_parser("resume", help="Resume a ticket")
    tracer_resume.add_argument("ticket_id", help="Ticket ID")
    tracer_sub.add_parser("list", help="List specs and tickets")

    args = parser.parse_args()

    # Route to command handler
    handlers = {
        "status": cmd_status,
        "agents": cmd_agents,
        "run": cmd_run,
        "rpi": cmd_rpi,
        "parallel": cmd_parallel,
        "workflow": cmd_workflow,
        "tracer": cmd_tracer,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
