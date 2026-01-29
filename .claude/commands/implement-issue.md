---
allowed-tools: Bash(gh issue view:*),Bash(gh issue list:*),Bash(git checkout:*),Bash(git branch:*),Bash(git push:*),Bash(uv run:*)
description: Analyze and fix a GitHub issue
---

Analyze and fix GitHub issue: $ARGUMENTS

## 1. IDENTIFY & APPROVE

**REQUIRED before ANY work:**
1. Find issue:
   - "next": Check project backlog + `gh issue list --state open`
   - Number: `gh issue view $ARGUMENTS`
2. **Use AskUserQuestion** for approval (GitHub #, title, description)
3. Only proceed after explicit "Yes"

## 2. PLAN

**REQUIRED - Complete ALL steps before implementing:**

1. `gh issue view` for full details

2. **Use Sequential Thinking** for problem analysis:
   - Use `mcp__sequential-thinking__sequentialthinking` to break down the problem
   - Start with understanding the problem scope (estimate 5-8 thoughts)
   - Allow revision of earlier thoughts as understanding deepens
   - Generate a hypothesis for the implementation approach
   - Verify the hypothesis against codebase patterns

   Key questions to explore:
   - What is the root cause/core requirement?
   - What existing code patterns apply?
   - What are the edge cases?
   - What could go wrong?

3. For complex issues, launch **Explore agent** (quick):
   - Search for similar patterns in source code
   - Check for related prior work

4. **REQUIRED: Create scratchpad file** - DO THIS IMMEDIATELY:
   - Path: `scratchpads/issue-{number}-{short-name}.md`
   - Use the template below
   - This file tracks your work and decisions - DO NOT SKIP

5. Break into tasks with **TodoWrite**

### Scratchpad Template (REQUIRED)

```markdown
# Issue #{number}: {title}

## Problem Statement
{Copy from issue description}

## Acceptance Criteria
{Copy checklist from issue}

## Research Notes
{What you learned from exploring the codebase}

## Sequential Thinking Log
{Document key insights from sequential thinking sessions}
- Problem analysis: [thoughts 1-N: key insights, any revisions made]
- Approach decision: [hypothesis generated and verification result]

## Implementation Approach
{Your plan - files to create/modify, key decisions}

## Progress Log
- [ ] Task 1
- [ ] Task 2
...

## Open Questions / Blockers
{Any unresolved issues}
```

**CHECKPOINT: Do NOT proceed to implementation until the scratchpad file exists.**

## 3. IMPLEMENT (TDD - Red/Green/Refactor)

Follow Kent Beck's TDD approach:

### Create Branch

```bash
git checkout -b feature/issue-{number}-{desc}  # or fix/issue-{number}-{desc}
```

### For Each Task

**If the solution approach is unclear**, use Sequential Thinking first:

- Analyze what the test should verify
- Consider edge cases and failure modes
- Revise approach if initial hypothesis doesn't hold
- Use `branchFromThought` if multiple valid approaches exist

1. **Red**: Write a failing test that defines the expected behavior

   ```bash
   uv run pytest tests/unit/test_<module>.py -x  # Should fail
   ```

2. **Green**: Write the minimum code to make the test pass

   ```bash
   uv run pytest tests/unit/test_<module>.py -x  # Should pass
   ```

3. **Refactor**: Clean up while keeping tests green
   - Remove duplication
   - Improve naming
   - Simplify logic

   ```bash
   uv run pytest tests/ -x  # Still passes
   ```

4. **Commit** after each green/refactor cycle

### Simplicity Check (After Each Cycle)

- Is this the simplest solution that works?
- Does the code reveal its intention?
- Am I building only what's needed for this issue?

## 4. VALIDATE

**REQUIRED - All must pass before PR:**

```bash
# All tests pass
uv run pytest

# Type checking
uv run mypy src/ tests/

# Linting and formatting (ORDER MATTERS)
# 1. Fix lint issues first (may remove unused imports, etc.)
uv run ruff check src/ tests/ --fix
# 2. Format after lint fixes (to clean up any formatting issues from fixes)
uv run ruff format src/ tests/
# 3. Final verification - this MUST pass before committing
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
```

**IMPORTANT:** Always run `ruff format --check` as the final step before committing.
The `--fix` flags modify files, so you must verify formatting after all fixes are applied.

All functions need type annotations.

## 5. PUSH & PR

1. Push: `git push -u origin {branch}`
2. Create PR:

   ```bash
   gh pr create --title "{feat|fix}: Description" --body "Closes #{github_issue_number}"
   ```

Note: Code review happens via `/review-pr` after PR creation.

---

## Troubleshooting (When Stuck)

If tests fail unexpectedly or implementation hits blockers:

1. **Use Sequential Thinking** to diagnose:
   - Start with what you expected vs. what happened
   - Set `isRevision: true` when reconsidering assumptions
   - Use `branchFromThought` to explore alternative explanations
   - Continue until root cause identified

2. Update scratchpad with findings
3. Revise TodoWrite tasks if needed

---

## Sequential Thinking Integration Points

| Workflow Step        | When to Use Sequential Thinking                |
| -------------------- | ---------------------------------------------- |
| Understanding issue  | Complex requirements, unclear scope            |
| Planning approach    | Multiple valid solutions, architectural decisions |
| Writing tests        | Non-obvious edge cases, complex behavior       |
| Debugging failures   | Test failures, unexpected behavior             |
| Refactoring decisions | Trade-offs between simplicity and flexibility |

---

## TDD Quick Reference

| Phase    | What to do                     | Test status    |
| -------- | ------------------------------ | -------------- |
| Red      | Write test for desired behavior | Failing        |
| Green    | Write minimal code to pass     | Passing        |
| Refactor | Clean up, remove duplication   | Still passing  |

**Remember:** "Make it work, make it right, make it fast" - in that order. Don't optimize until you have working, clean code.
