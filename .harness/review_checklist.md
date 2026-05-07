# Review Checklist

- [ ] Only V1 allowed files were modified.
- [ ] `main.py` only creates the app and registers routers.
- [ ] `/chat` accepts `user_id`, `session_id`, `message`, and `repo_path`.
- [ ] Response includes `trace_id`, `answer`, `related_files`, and `tool_calls`.
- [ ] `trace_id` is generated for every request.
- [ ] Two consecutive requests return different `trace_id` values.
- [ ] Mock answer explains that V1 does not read `repo_path` yet.
- [ ] V1 does not read `repo_path`.
- [ ] V1 does not call a real LLM.
- [ ] V1 does not implement repository tools, Skill Loader, Reflection, or eval.
- [ ] Pytest covers the `/chat` endpoint.
- [ ] Ruff is configured and can be run as a quality gate.
- [ ] README documents startup, tests, current capability, and roadmap.
