# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

[PROJECT_NAME] - [Brief description of the project]

## Development Philosophy

This project follows **Kent Beck's principles** for software development:

1. **Make it work, make it right, make it fast** - in that order
2. **Four Rules of Simple Design**: Tests pass → Reveals intention → No duplication → Fewest elements
3. **TDD (Test-Driven Development)**: Red → Green → Refactor

See `.claude/references/kent-beck-principles.md` for detailed guidance.

## Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest
poetry run pytest tests/unit/  # unit tests only
poetry run pytest -k "test_name"  # single test

# Type checking
poetry run mypy src/

# Linting and formatting
poetry run ruff check src/ tests/
poetry run ruff format src/ tests/
```

## Architecture

```
├── docs/               # Documentation
└── src/[project_name]/
    ├── core/           # Core domain logic
    ├── api/            # API layer (if applicable)
    ├── services/       # Business logic services
    ├── models/         # Data models
    └── utils/          # Utilities
```

## Development Workflow

### TDD Cycle

For every new feature or bug fix:

1. **Red**: Write a failing test first
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Clean up while tests stay green

### Slash Commands

Use the provided slash commands:
- `/review-pr [number]` - Review a pull request
- `/fix-review [number]` - Fix issues from code review
- `/implement-issue [number]` - Work on a GitHub issue
- `/merge-pr [number]` - Merge and clean up
- `/create-architecture` - Create architecture document
- `/create-git-issues` - Create GitHub issues from plan
- `/create-implementation-plan` - Create implementation plan

## Code Standards

- **Type hints**: Required on all function signatures
- **Testing**: All new code must have tests
- **Simplicity**: Avoid over-engineering; build only what's needed
- **Clarity**: Code should reveal its intention without excessive comments

## Anti-Patterns to Avoid

- Abstractions for single use cases
- Premature optimization
- "Just in case" code
- Configuration for things that never change
- Error handling for impossible states

## Performance Targets

- [Define specific performance targets if applicable]
- Only optimize after profiling shows a bottleneck
