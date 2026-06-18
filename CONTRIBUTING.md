# Contributing to Azure Connectors Python SDK

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Getting Started

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/) (tested on 3.10, 3.11, 3.12, 3.13)
- [Git](https://git-scm.com/downloads)
- [pip](https://pip.pypa.io/en/stable/) (comes with Python)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Azure/Connectors-Python-SDK.git
cd Connectors-Python-SDK

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the package in editable mode with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=azure.connectors --cov-report=html

# Run specific test file
pytest tests/test_office365.py

# Run tests in verbose mode
pytest -v
```

### Code Quality Checks

```bash
# Check code style (flake8)
flake8 src/ tests/

# Check for common issues
flake8 src/ --statistics

# Format code (optional, if using black)
black src/ tests/

# Type checking (optional, if using mypy)
mypy src/
```

## How to Contribute

1. Fork the repository
2. Create a topic branch from `main` (`git checkout -b feature/my-change`)
3. Make your changes
4. Run tests to ensure nothing is broken (`pytest`)
5. Run linting to ensure code quality (`flake8 src/ tests/`)
6. Commit your changes (`git commit -m "Add my change"`)
7. Push to your fork (`git push origin feature/my-change`)
8. Open a pull request against `main`

### Pull Request Guidelines

- Keep PRs focused on a single change
- Include tests for new functionality
- Update documentation if behavior changes
- Follow the existing code style (see [.github/copilot-instructions.md](.github/copilot-instructions.md) for Python conventions)
- Ensure all tests pass and linting succeeds before submitting
- Add an entry to [CHANGELOG.md](CHANGELOG.md) for user-facing changes

### Reporting Issues

- Use [GitHub Issues](https://github.com/Azure/Connectors-Python-SDK/issues) to report bugs or request features
- Search existing issues before creating a new one
- Use the provided issue templates when available
- Include Python version, SDK version, and steps to reproduce for bug reports

## Code Style

This project follows Python best practices documented in [.github/copilot-instructions.md](.github/copilot-instructions.md). Key points:

- **PEP 8** — Standard Python style guide (79 character line limit)
- **Type hints** — All public API signatures must have type hints (PEP 484)
- **Async/await** — Use async patterns for all I/O operations
- **Naming conventions:**
  - `snake_case` for functions, methods, variables
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants
  - `_snake_case` for private methods/attributes
- **Docstrings** — Google-style docstrings for all public APIs
- **Context managers** — Use `async with` for client lifecycle management

### Automated Enforcement

Coding standards are enforced automatically in CI — PRs that violate them will not pass:

- **`flake8`** (lint job) — enforces PEP 8 style rules (line length, imports, spacing)
- **`pytest`** (build-and-test jobs) — all tests must pass across Python 3.10-3.13
- **Test coverage** — minimum 70% coverage required
- **Markdown linting** — `markdownlint-cli2` checks all `.md` files

Run `flake8 src/ tests/` locally before pushing to catch style issues early.

## Generated Code

Connector client files in `src/azure/connectors/*.py` (except `sdk/` subpackage) are produced by an internal Microsoft code generator that is not publicly accessible at this time. **Do not submit pull requests that directly modify generated files** — changes will be overwritten the next time the code is regenerated.

If you find a bug or want to suggest an improvement in the generated code:

1. Open a [GitHub Issue](https://github.com/Azure/Connectors-Python-SDK/issues) describing the problem in detail
2. Include the affected file(s) and the current (incorrect) generated output
3. You are welcome to include a code suggestion showing the desired output — this helps the team understand the fix
4. A Microsoft contributor will work your suggestion back into the internal code generator so the fix applies to all generated connectors

**Files safe to modify:**

- `src/azure/connectors/sdk/*.py` — Core SDK infrastructure (not generated)
- `tests/*.py` — All test files
- `samples/*.py` — Sample code
- Documentation files (`.md` files)
- Configuration files (`.yml`, `.toml`, etc.)

## Testing Guidelines

### Test Structure

Tests use `pytest` with the following conventions:

- Test files: `tests/test_<module>.py`
- Test classes: `class Test<ClassName>:`
- Test methods: `def test_<method>_<scenario>_<expected_result>:`
- Async tests: Use `@pytest.mark.asyncio` decorator

### Test Categories

1. **Unit tests** — Test individual methods in isolation with mocks
2. **Integration tests** — Test against real Azure connectors (marked with `@pytest.mark.integration`)
3. **Edge case tests** — Test error handling, boundary conditions, special characters

### Fixtures

Common test fixtures are defined in `tests/conftest.py`:

- `mock_token_provider` — Mock authentication provider
- `mock_response_success` — Mock successful HTTP response
- `mock_response_error` — Mock error HTTP response

### Coverage Requirements

- Minimum 70% code coverage overall
- New code should have ≥ 80% coverage
- Critical paths (error handling, authentication) must have 100% coverage

Run coverage report:

```bash
pytest --cov=azure.connectors --cov-report=html
# Open htmlcov/index.html in browser
```

## Documentation

### Updating Documentation

- **README.md** — Project overview, quick start, installation
- **CHANGELOG.md** — Version history (add entry for every user-facing change)
- **ROADMAP.md** — Feature roadmap and connector priorities
- **docs/*.md** — Guides and tutorials
- **Docstrings** — Inline API documentation (Google-style format)

### Building Documentation

If Sphinx documentation is added in the future:

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build docs
cd docs
make html

# View docs
open _build/html/index.html
```

## Release Process

Releases use the Azure DevOps `eng/ci/library-release.yml` pipeline. Only
maintainers can start the release.

1. Update `CHANGELOG.md` with release notes.
2. Run the official release pipeline with the intended version (for example
  `1.2.3`, `1.2.3b1`, or `1.2.3.post1`).
3. The pipeline creates `release/{version}`, updates
  `src/azure/connectors/__init__.py`, builds the artifacts, creates a GitHub
  draft release, and uploads artifacts to Azure SDK partner drops.
4. Trigger the partner-release pipeline for PyPI using the BlobPath printed by
  the official release pipeline, then approve the final confirmation gate.

Do not delete or recreate published release tags as a normal retry path. If a
release fails after the tag is pushed, use a new version such as
`1.2.3.post1`; retagging is break-glass admin work only.

See [ROADMAP.md](ROADMAP.md) for release planning.

## Adding a New Connector

See the detailed guide in [.github/copilot-instructions.md](.github/copilot-instructions.md#adding-a-new-connector).

Quick checklist:

1. Generate connector code using LogicAppsCompiler with `--python` flag
2. Copy generated `.py` file to `src/azure/connectors/`
3. Update `__init__.py` exports
4. Add comprehensive unit tests
5. Add sample code to `samples/`
6. Update `README.md` and `ROADMAP.md`
7. Create PR with tests passing

## Questions and Support

- **General questions:** [GitHub Discussions](https://github.com/Azure/LogicApps/discussions)
- **Bug reports:** [GitHub Issues](https://github.com/Azure/Connectors-Python-SDK/issues)
- **Documentation:** See [docs/](docs/) folder and [README.md](README.md)
- **Stack Overflow:** Tag with `azure-connectors` or `azure-logic-apps`

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
