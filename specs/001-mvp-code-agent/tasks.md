# Tasks: V1 MVP Code Agent

## Implementation

- [x] Create the project directory structure.
- [x] Write V1 spec, plan, and task documents.
- [x] Write lightweight harness rules.
- [ ] Implement FastAPI app creation.
- [ ] Add package marker `__init__.py` files under `app/`.
- [ ] Implement `/chat` router.
- [ ] Implement chat request and response schemas.
- [ ] Implement trace ID generation.
- [ ] Implement mock code agent with an answer that mentions V1 does not read `repo_path`.
- [ ] Implement chat service orchestration.
- [ ] Add pytest coverage for `/chat`, including unique `trace_id` values across consecutive requests.
- [ ] Write README with setup, usage, current scope, and roadmap.
- [ ] Add `ruff` as a quality gate in `pyproject.toml`.

## Verification

- [ ] Run `pytest`.
- [ ] Run `ruff check .`.
- [ ] Confirm `uvicorn app.main:app --reload` is the documented startup command.

## Deferred

- [ ] Add repository file tools.
- [ ] Add basic agent loop.
- [ ] Add Skill Loader.
- [ ] Add trace persistence.
- [ ] Add mini eval.
- [ ] Add Reflection.
