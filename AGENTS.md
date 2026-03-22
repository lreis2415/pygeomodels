# AGENTS.md

This file is for coding agents working in this repository.
It captures practical commands and project-specific coding rules.

## 1) Project Snapshot

- Project type: Python package (`pygeomodels`) + MCP HTTP service (`pygeomodels_service.py`).
- Packaging: `setup.py` + `setup.cfg` (legacy setuptools layout).
- Runtime service stack: FastMCP + Uvicorn + Starlette.
- Container support: `Dockerfile` and `docker-compose.yml`.
- Main modules:
  - `pygeomodels/`: core API/config/model classes.
  - `mcp_service/`: MCP tool registration for terrain + model management.
  - `pygeomodels_service.py`: service entry point.

## 2) Environment and Setup Commands

Use `python` and `pip` commands (not `python3`/`pip3`) in this repo.

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Install package in editable mode (recommended for development)

```bash
python -m pip install -e .
```

### Build wheel

```bash
python setup.py bdist_wheel
```

### Reinstall helper script (Unix)

```bash
bash reinstall.sh
```

## 3) Run Commands

### Run MCP service locally

```bash
python pygeomodels_service.py
```

Expected endpoint (default): `http://127.0.0.1:8050/mcp`

### Run with Docker Compose

```bash
docker compose up --build
```

### Run a sample script

```bash
python examples/ex01_submit_model_task.py
```

## 4) Test Commands

This repo currently has one main test-like module: `test_run_model.py`.
`setup.cfg` points pytest to `tests/`, but that folder may not exist.

### Run all discovered pytest tests

```bash
pytest
```

### Run a specific test file explicitly

```bash
pytest test_run_model.py
```

### Run a single test class

```bash
pytest test_run_model.py::TestRunModel
```

### Run a single test method (important)

```bash
pytest test_run_model.py::TestRunModel::test_run_model_success -q
```

### Alternative: execute the test script directly

```bash
python test_run_model.py
```

## 5) Lint and Format Commands

No mandatory linter/formatter config files were found (`ruff`, `black`, `flake8`, `mypy` not configured).

Use these safe checks unless the repo adds official tooling:

### Syntax check

```bash
python -m compileall pygeomodels mcp_service pygeomodels_service.py
```

### Optional style/type checks (only if tool is installed)

```bash
ruff check .
black --check .
mypy pygeomodels mcp_service
```

If these tools are missing, do not add them unless requested.

## 6) Code Style Guidelines (Repository-Specific)

Follow existing code conventions first, then improve incrementally.

### Imports

- Group imports in this order: standard library, third-party, local modules.
- Keep one import per line unless importing related names from the same module.
- Prefer absolute imports from `pygeomodels` and `mcp_service`.

### Formatting

- Use 4-space indentation.
- Keep lines reasonably short (target <= 100 chars where practical).
- Match surrounding quote style in edited files.
- Keep functions small and focused.

### Types and annotations

- Add type hints for new/modified public functions.
- Use `Optional[T]` or `T | None` consistently within a file.
- Prefer concrete return types over `Any` when known.

### Naming conventions

- Existing public classes include legacy names like `modelBank` and `modelTask`; keep API-compatible names.
- For new classes, prefer `CapWords` (PEP 8).
- For variables/functions, use `snake_case`.
- For constants, use `UPPER_SNAKE_CASE`.

### Error handling

- Validate external inputs at boundaries (tool functions, API wrappers, config parsing).
- Raise clear exceptions (`ValueError`, `AttributeError`, etc.) for invalid arguments.
- Preserve current behavior where functions return `None` on API failure unless changing behavior is requested.
- Avoid bare `except:` in new code; catch specific exceptions.

### Logging and prints

- Prefer `logging` for service/runtime paths.
- Avoid noisy `print` in library code.
- In tests/debug scripts, limited `print` is acceptable.

### Docstrings and comments

- Use English for new comments and docstrings.
- Keep docstrings concise and action-oriented.
- Add comments only for non-obvious logic.

### MCP service patterns

- Register tools inside `register_*_tools(mcp)` functions.
- Keep tool return values JSON-serializable.
- Perform lazy initialization (`initialize()`) before using global model/config objects.

### API client behavior

- Existing wrappers (`restapi_get`, `restapi_post`) return parsed JSON or `None`.
- New network calls should include timeout handling when feasible.
- Keep request/response handling explicit and predictable.

## 7) File and Change Hygiene

- Do not commit runtime artifacts (`__pycache__`, `*.pyc`, local virtual env files).
- Keep changes scoped; avoid unrelated refactors.
- Preserve backward compatibility of public APIs unless explicitly requested.
- Update docs/examples when changing command-line behavior or service endpoints.

## 8) Cursor/Copilot Rules Check

Checked paths:

- `.cursorrules`
- `.cursor/rules/`
- `.github/copilot-instructions.md`

Result: no Cursor or Copilot instruction files were found in this repository.

## 9) Agent Execution Checklist

Before coding:

1. Read target module and adjacent modules for local conventions.
2. Confirm whether change affects package code, MCP service code, or both.

During coding:

1. Keep imports and naming consistent with the touched file.
2. Add/adjust types for changed function signatures.
3. Keep behavior compatible unless task requires behavior changes.

After coding:

1. Run the smallest relevant test (prefer single test method first).
2. Run broader tests if available.
3. Run syntax check if no lint config exists.
4. Document any new run/test command in this file when needed.

## 10) Quick Command Reference

```bash
# setup
python -m pip install -r requirements.txt
python -m pip install -e .

# run service
python pygeomodels_service.py

# tests
pytest test_run_model.py::TestRunModel::test_run_model_success -q
pytest test_run_model.py

# syntax check
python -m compileall pygeomodels mcp_service pygeomodels_service.py

# container
docker compose up --build
```
