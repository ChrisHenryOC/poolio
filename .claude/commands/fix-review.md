---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*),Bash(uv run:*)
description: Fix high and medium severity issues from code review for PR $ARGUMENTS.
---

Fix high and medium severity issues from code review for PR $ARGUMENTS.

## SETUP

```bash
# Get review directory and verify diff exists
ls -d code_reviews/PR$ARGUMENTS-* 2>/dev/null | head -1
# Verify the diff file exists (run /review-pr first if not)
test -f code_reviews/PR$ARGUMENTS-*/pr.diff || echo "ERROR: Diff not found. Run /review-pr $ARGUMENTS first."
# Verify we're on the correct branch
gh pr view $ARGUMENTS --json headRefName -q '.headRefName'
git fetch origin <branch> && git checkout <branch>
```

The diff is already saved at `code_reviews/PR$ARGUMENTS-<title>/pr.diff` from `/review-pr`. If the diff file doesn't exist, run `/review-pr $ARGUMENTS` first.

Check for @claude comments:

```bash
gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --jq '.[] | select(.body | contains("@claude")) | {id, path, body: .body[:80]}'
```

## GATHER FINDINGS

Read `CONSOLIDATED-REVIEW.md` from the review directory. It contains the Issue Matrix with severity, scope, and actionability already determined.

Also add any @claude PR comments as High severity issues (record comment ID for later reply).

## ANALYZE WITH SEQUENTIAL THINKING

**Use `mcp__sequential-thinking__sequentialthinking`** to understand and plan fixes:

### Issue Analysis (estimate 5-8 thoughts)

1. **Understand each issue** - What exactly is wrong and why?
2. **Identify dependencies** - Do any fixes depend on others?
3. **Plan fix order** - What sequence minimizes rework?
4. **Anticipate side effects** - Could a fix break something else?
5. **Verify simplicity** - Is the planned fix the simplest solution?
6. **Revise as needed** - Use `isRevision: true` if understanding changes

### Key Questions to Resolve

- Are any issues symptoms of the same root cause?
- Can multiple issues be fixed together safely?
- What's the minimal change that addresses each issue?

### When to Branch Thinking

Use `branchFromThought` when:

- Multiple valid fix approaches exist
- Unclear which of several related issues is the root cause
- Fix might require touching code outside the PR

## SIMPLICITY CHECK

Before implementing each fix, ask:

- Is this the simplest solution that could work?
- Am I adding more than what's needed to fix this specific issue?
- Does the fix reveal intention clearly?

**Avoid:** Adding abstractions, "improving" nearby code, future-proofing.

## CREATE TODO LIST

Use TodoWrite to track actionable issues:

- One todo per issue with severity prefix (e.g., "[High] Fix docstring")
- Mark deferred items separately

## IMPLEMENT (Following "Make It Work, Make It Right, Make It Fast")

For each issue (Critical > High > Medium):

1. **Make it work:**
   - Mark todo in_progress
   - Read the file before editing
   - Implement the simplest fix that addresses the issue

2. **Make it right:**
   - Ensure the fix reveals intention
   - Check for any duplication introduced
   - Mark todo completed

3. Reply to @claude comments if applicable:

   ```bash
   gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments/{ID}/replies --method POST -f body="Fixed. [description]"
   ```

**Do NOT "make it fast"** - performance optimization is out of scope for fix-review.

## VALIDATE AND COMMIT

```bash
uv run ruff format --check src/ tests/ && uv run ruff check src/ tests/ && uv run mypy src/ tests/ && uv run pytest tests/unit/ -x -q
git add -u && git commit -m "fix: Address review findings for PR #$ARGUMENTS" && git push
```

## HANDLE DEFERRED ITEMS

Skip if no deferred items or all are Low severity (auto-skip Low items).

For High/Medium deferred items, use AskUserQuestion with options:

- Fix now
- Add to existing issue (if related issue found)
- Create new issue
- Skip

## FINAL SUMMARY

Post to PR with:

- Issues Fixed table
- Deferred Items table (with decisions/outcomes)
- Validation results

```bash
gh pr comment $ARGUMENTS --body "$(cat <<'EOF'
## Code Review Fixes Applied
[summary tables]
EOF
)"
```

---

## Reminders

- Keep fixes minimal and focused
- Don't improve code beyond what's flagged
- Reply to all @claude comments

---

## Sequential Thinking Integration Points

| Fix Phase               | When to Use Sequential Thinking                  |
| ----------------------- | ------------------------------------------------ |
| Understanding issues    | Complex or interrelated findings                 |
| Planning fix order      | Dependencies between issues                      |
| Implementing fix        | Non-obvious solution or multiple approaches      |
| Debugging failed fix    | Fix didn't work as expected                      |
| Handling deferred items | Deciding between fix now, create issue, or skip  |

## Troubleshooting

If fixes cause test failures or new issues:

1. **Use Sequential Thinking** to diagnose:
   - Start with what changed and what broke
   - Set `isRevision: true` when reconsidering the fix approach
   - Use `branchFromThought` to explore rollback vs. forward-fix
   - Continue until root cause is clear

2. Update TodoWrite with revised plan
3. Re-implement with corrected approach
