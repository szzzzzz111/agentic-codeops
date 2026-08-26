"""Canonical repository verification entry."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROBE_TIMEOUT_SECONDS = 10


def _environment() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def _module_available(module: str, *, cwd: Path, env: dict[str, str]) -> bool:
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                (
                    "import importlib.util,sys; "
                    "raise SystemExit(0 if importlib.util.find_spec(sys.argv[1]) "
                    "is not None else 1)"
                ),
                module,
            ],
            cwd=cwd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical repository verification")
    parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    env = _environment()
    for module in ("pytest", "ruff"):
        if not _module_available(module, cwd=root, env=env):
            print(f"verification_tool_unavailable:{module}", file=sys.stderr)
            return 2
    commands = (
        ("pytest", [sys.executable, "-I", "-m", "pytest"]),
        ("ruff", [sys.executable, "-I", "-m", "ruff", "check", "."]),
        ("stage-doc", [sys.executable, "-I", "scripts/check_stage_docs.py"]),
        ("skill-eval", [sys.executable, "-I", "scripts/check_skill_evals.py"]),
    )
    for label, argv in commands:
        print(f"== {label} ==", flush=True)
        completed = subprocess.run(argv, cwd=root, env=env, check=False)
        if completed.returncode != 0:
            return completed.returncode
    print("== RepoPilot verification complete ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
