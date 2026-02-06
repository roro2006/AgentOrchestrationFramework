#!/usr/bin/env python3
"""
Shared Utilities for Agent Orchestration

Consolidates common code used across all controllers:
- Colors for terminal output
- CLI execution
- Score extraction
- State management
"""
from __future__ import annotations

import os
import subprocess
import json
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


# ============================================================================
# PATHS
# ============================================================================

DEFAULT_WORKSPACE_MARKERS = (
    ".claude",
    "PROJECT_PROMPT.md",
    "PROJECT_STATUS.md",
    "rubric.md",
    "specs",
    "tickets",
)


def resolve_workspace() -> Path:
    env_workspace = os.getenv("TRACER_WORKSPACE") or os.getenv("ORCHESTRATOR_WORKSPACE")
    if env_workspace:
        resolved = Path(env_workspace).expanduser().resolve()
        cwd = Path.cwd().resolve()
        try:
            resolved.relative_to(cwd)
            return resolved
        except ValueError:
            return cwd

    return Path.cwd().resolve()


WORKSPACE = resolve_workspace()
STATE_DIR = WORKSPACE / "state"
CLAUDE_DIR = WORKSPACE / ".claude"
COMMANDS_DIR = CLAUDE_DIR / "commands"
AGENTS_DIR = CLAUDE_DIR / "agents"
USAGE_LOG = STATE_DIR / "usage.jsonl"
CACHE_DIR = STATE_DIR / "cache"


# ============================================================================
# COLORS
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"


# ============================================================================
# CLI CONFIGURATION
# ============================================================================

CLI_CONFIGS = {
    "claude": {
        "cmd": "claude",
        "args": ["--print", "--dangerously-skip-permissions"],
        "prompt_flag": "-p",
    },
    "copilot": {
        "cmd": "copilot",
        "args": ["--yolo"],
        "model_flag": "--model",
        "model": "gpt-5.2-codex",
        "cheap_model": "gpt-5.1-codex-mini",
        "prompt_flag": "--prompt",
    },
}

DEFAULT_CHEAP_LABELS = (
    "rpi:research",
    "rpi:plan",
    "tracer:clarify",
    "tracer:ticket",
    "tracer:execute:review",
    "orch:locator",
)


# ============================================================================
# CLI EXECUTION
# ============================================================================

def run_cli(
    cli: str,
    prompt: str,
    timeout: int = 600,
    workspace: Path = WORKSPACE,
    on_line: Optional[Callable[[str], None]] = None,
    show_output: bool = True,
    usage_label: Optional[str] = None,
    cache_key: Optional[str] = None,
) -> tuple[str, int]:
    """
    Execute CLI with streaming output.

    Args:
        cli: CLI name ("claude" or "copilot")
        prompt: Prompt to send
        timeout: Timeout in seconds
        workspace: Working directory
        on_line: Callback for each output line
        show_output: Whether to print output lines
        usage_label: Label for usage tracking output/logs
        cache_key: Optional cache key; if provided, caches output for reuse

    Returns:
        Tuple of (output_text, return_code)
    """
    config = CLI_CONFIGS.get(cli)
    if not config:
        return f"[ERROR] Unknown CLI: {cli}", -1

    usage_label = usage_label or "cli"
    model = _select_model(config, usage_label)
    cache_key = cache_key or _default_cache_key(prompt, model, usage_label)

    cached = _load_cache(cache_key)
    if cached is not None:
        _log_usage(f"{usage_label}:cache", cli, model, _estimate_tokens(prompt), _estimate_tokens(cached), 0.0)
        print_usage(f"{usage_label}:cache", model, _estimate_tokens(prompt), _estimate_tokens(cached))
        return cached, 0

    cmd = [config["cmd"]] + config["args"]
    if "model_flag" in config and model:
        cmd.extend([config["model_flag"], model])
    cmd.extend([config["prompt_flag"], prompt])

    output_lines = []
    start_time = time.time()

    try:
        prompt_tokens = _estimate_tokens(prompt)
        process = subprocess.Popen(
            cmd,
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                process.kill()
                _log_usage(usage_label, cli, model, prompt_tokens, 0, elapsed)
                return "[TIMEOUT]", -1

            line = process.stdout.readline()
            if line:
                output_lines.append(line)
                if on_line:
                    on_line(line.rstrip())
                elif show_output:
                    display = line.rstrip()[:100]
                    print(f"  {Colors.GRAY}│{Colors.RESET} {display}")
            elif process.poll() is not None:
                break

        remaining = process.stdout.read()
        if remaining:
            output_lines.append(remaining)
            if on_line:
                for line in remaining.split('\n'):
                    if line.strip():
                        on_line(line)

        output_text = ''.join(output_lines)
        output_tokens = _estimate_tokens(output_text)
        _save_cache(cache_key, output_text)
        _log_usage(usage_label, cli, model, prompt_tokens, output_tokens, time.time() - start_time)
        print_usage(usage_label, model, prompt_tokens, output_tokens)
        return output_text, process.returncode

    except FileNotFoundError:
        return f"[ERROR] CLI '{cli}' not found", -1
    except Exception as e:
        return f"[ERROR] {e}", -1


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def _default_cache_key(prompt: str, model: Optional[str], usage_label: str) -> str:
    return f"{usage_label}:{model}:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}"


def _cache_path(cache_key: str) -> Path:
    safe_key = re.sub(r'[^a-zA-Z0-9._-]', "_", cache_key)
    return CACHE_DIR / f"{safe_key}.json"


def _load_cache(cache_key: str) -> Optional[str]:
    if os.getenv("ORCHESTRATOR_CACHE") == "0":
        return None
    path = _cache_path(cache_key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data.get("output", "")
    except Exception:
        return None


def _save_cache(cache_key: str, output_text: str):
    if os.getenv("ORCHESTRATOR_CACHE") == "0":
        return
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {"ts": datetime.now().isoformat(), "output": output_text}
        _cache_path(cache_key).write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"  {Colors.YELLOW}[cache]{Colors.RESET} write failed: {e}")


def _select_model(config: dict, usage_label: str) -> Optional[str]:
    base_model = config.get("model")
    if "model_flag" not in config or not base_model:
        return base_model

    labels_raw = os.getenv("ORCHESTRATOR_CHEAP_LABELS")
    if labels_raw is None:
        labels = DEFAULT_CHEAP_LABELS
    else:
        labels = tuple(l.strip() for l in labels_raw.split(",") if l.strip())

    use_cheap = any(usage_label.startswith(label) for label in labels)
    if not use_cheap:
        return base_model

    return os.getenv("ORCHESTRATOR_CHEAP_MODEL") or config.get("cheap_model") or base_model


def _log_usage(label: str, cli: str, model: Optional[str], in_tokens: int, out_tokens: int, elapsed: float):
    usage = {
        "ts": datetime.now().isoformat(),
        "label": label,
        "cli": cli,
        "model": model,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "total_tokens": in_tokens + out_tokens,
        "elapsed_sec": round(elapsed, 3),
    }
    try:
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(usage) + "\n")
    except Exception as e:
        print(f"  {Colors.YELLOW}[usage]{Colors.RESET} log write failed: {e}")


def print_usage(label: str, model: Optional[str], in_tokens: int, out_tokens: int):
    total = in_tokens + out_tokens
    model_note = f" model={model}" if model else ""
    print(f"  {Colors.GRAY}[usage]{Colors.RESET} {label}:{model_note} in≈{in_tokens} out≈{out_tokens} total≈{total}")


# ============================================================================
# SCORE EXTRACTION
# ============================================================================

def extract_score(text: str) -> int:
    """
    Extract score from grading output.

    Looks for patterns like:
    - "Score: 85/100"
    - "**Score:** 85"
    - "Score: 85"
    """
    patterns = [
        r'\*\*Score:\s*(\d+)/100\*\*',
        r'[Ss]core:\s*(\d+)/100',
        r'\*\*[Ss]core:\*\*\s*(\d+)',
        r'[Ss]core:\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return 0


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

@dataclass
class LoopState:
    """Unified state for all loop types."""
    mode: str = "rpi"  # "rpi" | "tracer" | "custom"
    current_story: str = "US-1"
    current_phase: str = "none"
    iteration: int = 0
    version: int = 0
    score: int = 0
    history: list = field(default_factory=list)
    # Tracer-specific
    spec_id: Optional[str] = None
    ticket_id: Optional[str] = None
    deviations_detected: int = 0
    deviations_corrected: int = 0
    # Timestamps
    started_at: str = ""
    last_activity: str = ""

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "current_story": self.current_story,
            "current_phase": self.current_phase,
            "iteration": self.iteration,
            "version": self.version,
            "score": self.score,
            "history": self.history,
            "spec_id": self.spec_id,
            "ticket_id": self.ticket_id,
            "deviations_detected": self.deviations_detected,
            "deviations_corrected": self.deviations_corrected,
            "started_at": self.started_at,
            "last_activity": self.last_activity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoopState":
        return cls(
            mode=data.get("mode", "rpi"),
            current_story=data.get("current_story", "US-1"),
            current_phase=data.get("current_phase", "none"),
            iteration=data.get("iteration", 0),
            version=data.get("version", 0),
            score=data.get("score", 0),
            history=data.get("history", []),
            spec_id=data.get("spec_id"),
            ticket_id=data.get("ticket_id"),
            deviations_detected=data.get("deviations_detected", 0),
            deviations_corrected=data.get("deviations_corrected", 0),
            started_at=data.get("started_at", ""),
            last_activity=data.get("last_activity", ""),
        )


def load_state(state_file: Path) -> LoopState:
    """Load state from file."""
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            return LoopState.from_dict(data)
        except Exception:
            pass
    return LoopState()


def save_state(state: LoopState, state_file: Path):
    """Save state to file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state.last_activity = datetime.now().isoformat()
    state_file.write_text(json.dumps(state.to_dict(), indent=2))


# ============================================================================
# PROMPT LOADING
# ============================================================================

def load_command_prompt(command_name: str) -> str:
    """Load a command prompt from .claude/commands/"""
    cmd_file = COMMANDS_DIR / f"{command_name}.md"
    if cmd_file.exists():
        content = cmd_file.read_text()
        # Strip YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content
    return ""


def load_agent_prompt(agent_name: str) -> str:
    """Load an agent definition from .claude/agents/"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    if agent_file.exists():
        content = agent_file.read_text()
        # Strip YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content
    return ""


# ============================================================================
# CONTEXT COMPACTION
# ============================================================================

def compact_text(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head_size = max_chars // 2
    tail_size = max_chars - head_size
    head = text[:head_size].rstrip()
    tail = text[-tail_size:].lstrip()
    return f"{head}\n...\n{tail}"


def _extract_heading_section(text: str, token: str) -> str:
    if not text or not token:
        return ""
    lines = text.splitlines()
    header_re = re.compile(r'^(#{1,6})\s*(.+)\s*$')
    token_re = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)

    start = None
    level = None
    for i, line in enumerate(lines):
        match = header_re.match(line)
        if match and token_re.search(match.group(2)):
            start = i
            level = len(match.group(1))
            break

    if start is None:
        return ""

    end = len(lines)
    for j in range(start + 1, len(lines)):
        match = header_re.match(lines[j])
        if match and len(match.group(1)) <= level:
            end = j
            break

    return "\n".join(lines[start:end]).strip()


def load_project_context(path: Path, max_chars: int,
                         story_id: Optional[str] = None,
                         story_name: Optional[str] = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text()
    for token in [story_id, story_name]:
        section = _extract_heading_section(text, token) if token else ""
        if section:
            return compact_text(section, max_chars)
    return compact_text(text, max_chars)


# ============================================================================
# PROJECT PARSING
# ============================================================================

def get_current_story(project_status_file: Path, project_prompt_file: Path) -> dict:
    """Parse PROJECT_STATUS.md to find current story."""
    if not project_status_file.exists():
        return {"id": "US-1", "name": "Unknown", "status": "waiting"}

    content = project_status_file.read_text()
    current_id = "US-1"

    match = re.search(r'\*\*Current Story\*\*\s*\|\s*(US-\d+)', content)
    if match:
        current_id = match.group(1)

    story_info = {"id": current_id, "name": "", "status": "in_progress"}

    # Try to find story name from PROJECT_PROMPT.md
    if project_prompt_file.exists():
        prompt_content = project_prompt_file.read_text()
        pattern = rf'###\s*{current_id}[:\s]+([^\n]+)'
        match = re.search(pattern, prompt_content)
        if match:
            story_info["name"] = match.group(1).strip()

    return story_info


# ============================================================================
# OUTPUT HELPERS
# ============================================================================

def print_header(title: str, subtitle: str = "", color: str = None):
    """Print a formatted header."""
    c = color or Colors.BLUE
    print()
    print(f"{c}{'═' * 70}{Colors.RESET}")
    print(f"{c}  {title}{Colors.RESET}")
    if subtitle:
        print(f"{c}  {Colors.GRAY}{subtitle}{Colors.RESET}")
    print(f"{c}{'═' * 70}{Colors.RESET}")


def print_phase(phase: str, description: str = ""):
    """Print a phase banner."""
    icons = {
        "RESEARCH": "🔍",
        "PLAN": "📋",
        "IMPLEMENT": "🔧",
        "GRADE": "📊",
        "CLARIFY": "❓",
        "REVIEW": "👀",
    }
    icon = icons.get(phase.upper(), "▶")
    print()
    print(f"{Colors.CYAN}{'━' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}  {icon}  {phase.upper()}{Colors.RESET}")
    if description:
        print(f"{Colors.GRAY}     {description}{Colors.RESET}")
    print(f"{Colors.CYAN}{'━' * 70}{Colors.RESET}")


def print_score(score: int):
    """Print a formatted score."""
    if score >= 100:
        color = Colors.GREEN
        msg = "PERFECT!"
    elif score >= 80:
        color = Colors.YELLOW
        msg = "CLOSE"
    else:
        color = Colors.RED
        msg = "NEEDS WORK"

    print()
    print(f"  {color}╔{'═' * 30}╗{Colors.RESET}")
    print(f"  {color}║  SCORE: {score:3d}/100  {msg:<10} ║{Colors.RESET}")
    print(f"  {color}╚{'═' * 30}╝{Colors.RESET}")


def print_progress(current: int, total: int, label: str = "Progress"):
    """Print a progress bar."""
    if total == 0:
        pct = 0
    else:
        pct = int((current / total) * 100)

    filled = pct // 5
    empty = 20 - filled
    bar = f"{'█' * filled}{'░' * empty}"

    color = Colors.GREEN if pct >= 80 else Colors.YELLOW if pct >= 40 else Colors.RED
    print(f"  {Colors.GRAY}{label}:{Colors.RESET} [{color}{bar}{Colors.RESET}] {pct}%")
