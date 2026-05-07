from uuid import uuid4


def generate_trace_id() -> str:
    return f"trace_{uuid4().hex}"
