from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time


MAX_STREAM_EXCERPT_CHARS = 4000
MAX_ANSWER_OUTPUT_CHARS = 6000
DEFAULT_TIMEOUT_SECONDS = 120
ALLOWED_COMMANDS: dict[str, list[str]] = {
    "pytest": ["pytest"],
    "ruff": ["ruff", "check", "."],
    "verify": [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "scripts/verify.ps1",
    ],
}
_VERIFY_ALIASES = {
    "运行验证": "verify",
    "执行验证": "verify",
    "跑验证": "verify",
    "run verify": "verify",
    "run verification": "verify",
    "运行 pytest": "pytest",
    "执行 pytest": "pytest",
    "跑 pytest": "pytest",
    "run pytest": "pytest",
    "运行 ruff": "ruff",
    "执行 ruff": "ruff",
    "跑 ruff": "ruff",
    "run ruff": "ruff",
}
_SHELL_SYNTAX_RE = re.compile(r"[|&;<>()`$]|(?:^|\s)(?:[A-Za-z_][A-Za-z0-9_]*=)")
_WINDOWS_ABSOLUTE_PATH_RE = re.compile(
    r"\b[A-Za-z]:[\\/][^\s，。；;'\"\)\]]+(?:[\\/][^\s，。；;'\"\)\]]+)*"
)
_POSIX_LOCAL_ABSOLUTE_PATH_RE = re.compile(
    r"(?<![\w.])/(?:Users|home|root|tmp|var|etc|opt|mnt|srv)/[^\s，。；;'\"\)\]]+"
)
_REPOPILOT_PATH_RE = re.compile(r"\.repopilot[\\/][^\s，。；;'\"\)\]]+")
_SECRET_RE = re.compile(
    r"\b[A-Za-z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s，。；;]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class VerificationRequest:
    handled: bool
    command_label: str = ""
    rejected: bool = False
    reason: str = ""


@dataclass(frozen=True)
class VerificationRunResult:
    command_label: str
    status: str
    exit_code: int | None
    duration_ms: int
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    timed_out: bool = False
    truncated: bool = False

    def audit_summary(self) -> dict[str, str | int]:
        return {
            "command_label": self.command_label,
            "status": self.status,
            "exit_code": "" if self.exit_code is None else self.exit_code,
            "duration_ms": self.duration_ms,
            "timed_out": str(self.timed_out).lower(),
            "truncated": str(self.truncated).lower(),
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
        }


def parse_verification_request(message: str) -> VerificationRequest:
    normalized = " ".join(message.strip().split())
    lower = normalized.lower()
    if not _looks_like_verification_request(normalized, lower):
        return VerificationRequest(handled=False)
    if _SHELL_SYNTAX_RE.search(normalized):
        return VerificationRequest(handled=True, rejected=True, reason="unsafe_syntax")
    label = _VERIFY_ALIASES.get(lower)
    if label is None:
        return VerificationRequest(handled=True, rejected=True, reason="not_whitelisted")
    return VerificationRequest(handled=True, command_label=label)


def parse_verification_label(value: str) -> VerificationRequest:
    normalized = " ".join(value.strip().split())
    lower = normalized.lower()
    if not normalized:
        return VerificationRequest(
            handled=True,
            rejected=True,
            reason="missing_verification_label",
        )
    if _SHELL_SYNTAX_RE.search(normalized):
        return VerificationRequest(handled=True, rejected=True, reason="unsafe_syntax")
    label = {
        "验证": "verify",
        "verify": "verify",
        "verification": "verify",
        "pytest": "pytest",
        "ruff": "ruff",
    }.get(lower)
    if label is None:
        return VerificationRequest(handled=True, rejected=True, reason="not_whitelisted")
    return VerificationRequest(handled=True, command_label=label)


def command_argv(command_label: str) -> list[str] | None:
    command = ALLOWED_COMMANDS.get(command_label)
    if command is None:
        return None
    return list(command)


def run_whitelisted_verification(
    repo_path: str | Path,
    command_label: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> VerificationRunResult:
    argv = command_argv(command_label)
    if argv is None:
        return VerificationRunResult(
            command_label=command_label,
            status="rejected",
            exit_code=None,
            duration_ms=0,
            stderr_excerpt="unsupported_command",
        )
    return run_verification_command(
        repo_path=repo_path,
        command_label=command_label,
        argv=argv,
        timeout_seconds=timeout_seconds,
    )


def run_verification_command(
    *,
    repo_path: str | Path,
    command_label: str,
    argv: list[str],
    timeout_seconds: int,
) -> VerificationRunResult:
    started = time.monotonic()
    try:
        cwd = Path(repo_path).resolve(strict=True)
        if not cwd.is_dir():
            raise NotADirectoryError
    except (OSError, RuntimeError):
        return VerificationRunResult(
            command_label=command_label,
            status="unavailable",
            exit_code=None,
            duration_ms=_elapsed_ms(started),
            stderr_excerpt="repo_unavailable",
        )

    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        return VerificationRunResult(
            command_label=command_label,
            status="unavailable",
            exit_code=None,
            duration_ms=_elapsed_ms(started),
            stderr_excerpt="command_unavailable",
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _excerpt(exc.stdout or "", repo_path=cwd)
        stderr, stderr_truncated = _excerpt(exc.stderr or "", repo_path=cwd)
        return VerificationRunResult(
            command_label=command_label,
            status="timed_out",
            exit_code=None,
            duration_ms=_elapsed_ms(started),
            stdout_excerpt=stdout,
            stderr_excerpt=stderr,
            timed_out=True,
            truncated=stdout_truncated or stderr_truncated,
        )
    except OSError:
        return VerificationRunResult(
            command_label=command_label,
            status="failed",
            exit_code=None,
            duration_ms=_elapsed_ms(started),
            stderr_excerpt="runner_error",
        )

    stdout, stdout_truncated = _excerpt(completed.stdout, repo_path=cwd)
    stderr, stderr_truncated = _excerpt(completed.stderr, repo_path=cwd)
    status = "success" if completed.returncode == 0 else "failed"
    return VerificationRunResult(
        command_label=command_label,
        status=status,
        exit_code=completed.returncode,
        duration_ms=_elapsed_ms(started),
        stdout_excerpt=stdout,
        stderr_excerpt=stderr,
        timed_out=False,
        truncated=stdout_truncated or stderr_truncated,
    )


def redact_verification_output(value: str, *, repo_path: str | Path) -> str:
    text = str(value)
    try:
        resolved_repo = Path(repo_path).resolve()
        text = text.replace(str(resolved_repo), "<repo>")
        text = text.replace(resolved_repo.as_posix(), "<repo>")
    except (OSError, RuntimeError):
        pass
    text = _SECRET_RE.sub("<redacted-secret>", text)
    text = _REPOPILOT_PATH_RE.sub(".repopilot/<redacted>", text)
    text = _WINDOWS_ABSOLUTE_PATH_RE.sub("<local-path>", text)
    return _POSIX_LOCAL_ABSOLUTE_PATH_RE.sub("<local-path>", text)


def format_verification_answer(result: VerificationRunResult) -> str:
    status_text = {
        "success": "验证完成",
        "failed": "验证失败",
        "timed_out": "验证超时",
        "unavailable": "验证不可用",
        "rejected": "验证已拒绝",
    }.get(result.status, "验证结束")
    excerpts = []
    if result.stdout_excerpt:
        excerpts.append(f"stdout: {result.stdout_excerpt}")
    if result.stderr_excerpt:
        excerpts.append(f"stderr: {result.stderr_excerpt}")
    output = "\n".join(excerpts)
    answer_truncated = result.truncated or len(output) > MAX_ANSWER_OUTPUT_CHARS
    if len(output) > MAX_ANSWER_OUTPUT_CHARS:
        output = output[:MAX_ANSWER_OUTPUT_CHARS]
    suffix = f"\n{output}" if output else ""
    return (
        f"{status_text}：command={result.command_label}，"
        f"exit_code={'' if result.exit_code is None else result.exit_code}，"
        f"duration_ms={result.duration_ms}，"
        f"timed_out={str(result.timed_out).lower()}，"
        f"truncated={str(answer_truncated).lower()}。"
        f"{suffix}"
    )


def unsupported_verification_answer() -> str:
    return "只支持固定验证命令：pytest、ruff、verify；不支持附加参数或 shell 语法。"


def _looks_like_verification_request(message: str, lower: str) -> bool:
    has_verification_term = any(
        term in lower or term in message
        for term in ("verify", "verification", "pytest", "ruff", "验证")
    )
    has_command_phrase = any(
        phrase in lower
        for phrase in (
            "run verify",
            "run verification",
            "run pytest",
            "run ruff",
        )
    )
    return has_verification_term and (
        has_command_phrase
        or lower.startswith("run ")
        or message.startswith("运行")
        or message.startswith("执行")
        or message.startswith("跑")
    )


def _excerpt(value: str, *, repo_path: Path) -> tuple[str, bool]:
    redacted = redact_verification_output(value, repo_path=repo_path)
    if len(redacted) <= MAX_STREAM_EXCERPT_CHARS:
        return redacted, False
    return redacted[:MAX_STREAM_EXCERPT_CHARS], True


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
