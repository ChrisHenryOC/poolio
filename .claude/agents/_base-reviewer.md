# Base Reviewer Template

This file contains shared context for all reviewer agents. Individual agents extend this with their specialty focus.

## Guiding Philosophy (Kent Beck)

All reviews should consider:

- **"Make it work, make it right, make it fast"** - in that order
- **Four Rules of Simple Design**: Tests pass → Reveals intention → No duplication → Fewest elements
- **Simplicity over speculation** - Don't flag missing features; flag unnecessary complexity
- **Feedback over perfection** - Ship working code; iterate based on feedback

## Project Context

- **Project**: [PROJECT_NAME] (Python)
- **Performance target**: [PERFORMANCE_TARGET]
- **Memory target**: [MEMORY_TARGET]
- **Standards**: Type hints required, ruff linting, pytest for testing

## Review Process

1. Read `/tmp/pr{NUMBER}.diff` using the Read tool
2. Focus on changed lines (+ lines in diff)
3. Flag issues only in new/modified code unless critical
4. Write findings to `code_reviews/PR{NUMBER}-{title}/{agent-name}.md`

## Output Format

```markdown
# {Agent Name} Review for PR #{NUMBER}

## Summary
[2-3 sentences]

## Findings

### Critical
[Security vulnerabilities, data loss, breaking changes]

### High
[Performance >10% impact, missing critical tests, over-engineering]

### Medium
[Code quality affecting maintainability]

### Low
[Minor suggestions - usually skip]
```

Each finding: **Issue** - `file.py:line` - Recommendation

## Severity Definitions

- **Critical**: Security vulnerabilities, data loss, breaking changes
- **High**: Performance bottlenecks >10%, missing critical tests, significant over-engineering
- **Medium**: Code quality issues affecting maintainability
- **Low**: Minor suggestions (typically skip)

## Over-Engineering Red Flags

Flag these as High severity when found:

- Abstractions used only once
- "Factory" or "Manager" classes for simple operations
- Configuration for things that never change
- Error handling for impossible states
- Interfaces with single implementations
- Comments explaining "why this might be needed later"
- Premature optimization without profiling evidence
