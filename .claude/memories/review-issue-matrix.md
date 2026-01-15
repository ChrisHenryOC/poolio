# Code Review Issue Matrix Format

## Standard Matrix

| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|

## Severity Levels

- **Critical**: Security vulnerabilities, data loss risks
- **High**: >10% performance impact, missing tests for new code, significant over-engineering
- **Medium**: Maintainability, code quality issues
- **Low**: Minor style issues (auto-skip)

## Actionability Criteria

**Actionable = Yes** when ALL true:
- No new dependencies needed
- Changes stay within PR's modified files
- No major refactoring required

**Actionable = No** examples:
- Requires changes to files not in PR
- Would need new library/dependency
- Architectural changes beyond scope

## Over-Engineering Flags

Per Kent Beck's "Fewest Elements" rule, flag as High severity:
- Abstractions used only once
- Configuration for things that never change
- Error handling for impossible states
- "Just in case" code paths
