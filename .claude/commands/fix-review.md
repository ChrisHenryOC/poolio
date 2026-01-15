---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*),Bash(poetry run:*)
description: Fix high and medium severity issues from code review for PR $ARGUMENTS.
---

Fix high and medium severity issues from code review for PR $ARGUMENTS.

## SETUP

```bash
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
ls -d code_reviews/PR$ARGUMENTS-* 2>/dev/null | head -1
```

Check for @claude comments:
```bash
gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --jq '.[] | select(.body | contains("@claude")) | {id, path, body: .body[:80]}'
```

## GATHER FINDINGS

Read `CONSOLIDATED-REVIEW.md` from the review directory. It contains the Issue Matrix with severity, scope, and actionability already determined.

Also add any @claude PR comments as High severity issues (record comment ID for later reply).

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
poetry run pytest tests/unit/ -x -q && poetry run mypy src/ && poetry run ruff check src/ tests/
git add -A && git commit -m "fix: Address review findings" && git push
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

**Reminders:**
- Keep fixes minimal and focused
- Don't improve code beyond what's flagged
- Reply to all @claude comments
