# Contributing to FaultBox

We welcome contributions to FaultBox. This project uses Python 3.12, `ruff` for code formatting and linting, and `pytest` for automated testing.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/alexandrmotologa/faultbox.git
   cd faultbox
   ```

2. Create a virtual environment using `uv`:
   ```bash
   uv venv --python 3.12
   uv pip install -e ".[dev]"
   ```

3. Run the test suite:
   ```bash
   uv run pytest
   ```

4. Format and lint your changes:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

## Adding a New Toxic Plugin

To add a new toxic to the engine:

1. Create a new module under `src/faultbox/toxics/<name>.py`.
2. Inherit from `BaseToxic` and implement the `transform(self, chunk: bytes, context: StreamContext) -> bytes | list[bytes] | None` method.
3. Register the class in `src/faultbox/toxics/factory.py` within `TOXIC_REGISTRY`.
4. Export the class in `src/faultbox/toxics/__init__.py`.
5. Add unit tests under `tests/unit/test_toxics.py`.
6. Document the configuration attributes in `docs/TOXICS.md`.

## Submitting Pull Requests

- Keep commits atomic with descriptive commit messages following the Conventional Commits specification.
- Ensure all automated tests pass before opening a pull request.
- Keep documentation up to date with new features or configuration flags.
