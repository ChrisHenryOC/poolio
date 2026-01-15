---
allowed-tools: Bash(gh issue view:*),Bash(gh issue list:*),Bash(git checkout:*),Bash(git branch:*),Bash(git push:*),Bash(poetry run:*)
description: Analyze and fix a GitHub issue
---

Analyze and fix GitHub issue: $ARGUMENTS

## 1. IDENTIFY & APPROVE

**Required before ANY work:**
1. Find issue:
   - "next": Check project backlog + `gh issue list --state open`
   - Number: `gh issue view $ARGUMENTS`
2. **Use AskUserQuestion** for approval (GitHub #, title, description)
3. Only proceed after explicit "Yes"

## 2. PLAN

1. `gh issue view` for full details
2. For complex issues, launch **Explore agent** (quick):
   - Search for similar patterns in source code
   - Check for related prior work
3. Break into tasks with **TodoWrite**
4. Create scratchpad if needed: `/scratchpads/issue-{number}-{short-name}.md`

## 3. IMPLEMENT (TDD - Red/Green/Refactor)

Follow Kent Beck's TDD approach:

### Create Branch
```bash
git checkout -b feature/issue-{number}-{desc}  # or fix/issue-{number}-{desc}
```

### For Each Task:

1. **Red**: Write a failing test that defines the expected behavior
   ```bash
   poetry run pytest tests/unit/test_<module>.py -x  # Should fail
   ```

2. **Green**: Write the minimum code to make the test pass
   ```bash
   poetry run pytest tests/unit/test_<module>.py -x  # Should pass
   ```

3. **Refactor**: Clean up while keeping tests green
   - Remove duplication
   - Improve naming
   - Simplify logic
   ```bash
   poetry run pytest tests/unit/ -x  # Still passes
   ```

4. **Commit** after each green/refactor cycle

### Simplicity Check (After Each Cycle)
- Is this the simplest solution that works?
- Does the code reveal its intention?
- Am I building only what's needed for this issue?

## 4. VALIDATE

```bash
# All tests pass
poetry run pytest

# Type checking
poetry run mypy src/

# Linting and formatting
poetry run ruff format src/ tests/
poetry run ruff check src/ tests/ --fix
```

All functions need type annotations.

## 5. PUSH & PR

1. Push: `git push -u origin {branch}`
2. Create PR:
   ```bash
   gh pr create --title "{feat|fix}: Description" --body "Closes #{github_issue_number}"
   ```

Note: Code review happens via `/review-pr` after PR creation.

---

## TDD Quick Reference

| Phase | What to do | Test status |
|-------|-----------|-------------|
| Red | Write test for desired behavior | Failing |
| Green | Write minimal code to pass | Passing |
| Refactor | Clean up, remove duplication | Still passing |

**Remember:** "Make it work, make it right, make it fast" - in that order. Don't optimize until you have working, clean code.
