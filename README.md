# Claude Code Python Template

A Python project template configured for use with Claude Code, following Kent Beck's principles for software development.

## Features

- Poetry for dependency management
- pytest for testing
- mypy for type checking
- ruff for linting and formatting
- TDD workflow support
- Claude Code slash commands for PR reviews, issue management, and more

## Getting Started

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)

### Installation

```bash
poetry install
```

## Development

### Commands

```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy src/

# Linting and formatting
poetry run ruff check src/ tests/
poetry run ruff format src/ tests/
```

### TDD Workflow

This project follows Test-Driven Development:

1. **Red** - Write a failing test
2. **Green** - Write minimal code to pass
3. **Refactor** - Clean up while tests stay green

## Project Structure

```
├── docs/               # Documentation
└── src/[project_name]/
    ├── core/           # Core domain logic
    ├── api/            # API layer
    ├── services/       # Business logic services
    ├── models/         # Data models
    └── utils/          # Utilities
```

## License

[Add your license here]
