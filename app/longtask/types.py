from dataclasses import dataclass, field

TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_PAUSED = "paused"
TASK_STATUS_BLOCKED = "blocked"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
TERMINAL_STATUSES = {TASK_STATUS_COMPLETED, TASK_STATUS_FAILED}

ACTION_REPO_RAG = "repo_rag"
MAX_STEP_ATTEMPTS = 3
MAX_OPEN_TASKS = 20
DEFAULT_LIST_LIMIT = 10


@dataclass(frozen=True)
class LongTaskStep:
    step_id: str
    title: str
    action_type: str
    query_hint: str
    status: str = TASK_STATUS_PENDING
    attempt_count: int = 0
    retry_round: int = 0
    expected_outcome: str = ""
    acceptance_hint: str = ""
    thought_summary: str = ""
    action_summary: str = ""
    observation_summary: str = ""
    trace_status: str = ""


@dataclass(frozen=True)
class LongTask:
    task_id: str
    user_id: str
    repo_key: str
    title: str
    goal: str
    task_type: str
    status: str
    plan_source: str
    current_step_index: int = 0
    retry_round: int = 0
    archived: bool = False
    steps: list[LongTaskStep] = field(default_factory=list)

    @property
    def current_step(self) -> LongTaskStep | None:
        if not self.steps:
            return None
        index = min(self.current_step_index, len(self.steps) - 1)
        return self.steps[index]


@dataclass(frozen=True)
class PlanResult:
    task_type: str
    plan_source: str
    steps: list[LongTaskStep]
    provider_status: str = ""


@dataclass(frozen=True)
class LongTaskCommand:
    action: str
    goal: str = ""
    task_id: str = ""
    note: str = ""


@dataclass(frozen=True)
class LongTaskCommandResult:
    handled: bool
    answer: str = ""
    task_id: str | None = None
    tool_action: str | None = None
    query_text: str = ""
    audit_summary: str = ""
