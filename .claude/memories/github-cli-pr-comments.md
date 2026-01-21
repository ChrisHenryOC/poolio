# GitHub CLI PR Comments Syntax

## Inline Comments on PR Diffs (Recommended)

Use `line` and `side` (the modern approach, replaces deprecated `position`):

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --method POST \
  -f body="Comment text" \
  -f path="src/file.py" \
  -F line=42 \
  -f side="RIGHT" \
  -f commit_id="$(gh pr view {pr} --json headRefOid -q '.headRefOid')"
```

**Parameters:**
- `line` - The actual line number in the file
- `side` - `RIGHT` for additions/unchanged lines, `LEFT` for deletions
- Use `-F` (not `-f`) for integer values like `line`

## Multi-line Comments

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --method POST \
  -f body="Comment spanning multiple lines" \
  -f path="src/file.py" \
  -F start_line=10 \
  -f start_side="RIGHT" \
  -F line=15 \
  -f side="RIGHT" \
  -f commit_id="$(gh pr view {pr} --json headRefOid -q '.headRefOid')"
```

## File-level Comment (not on specific line)

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --method POST \
  -f body="Comment on the entire file" \
  -f path="src/file.py" \
  -f subject_type="file" \
  -f commit_id="$(gh pr view {pr} --json headRefOid -q '.headRefOid')"
```

## Reply to Existing Comment

**Note:** Can only reply to top-level comments, not to replies.

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  --method POST \
  -f body="Reply text"
```

## Get Comments on a PR

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | {id, path, line, body: .body[:80]}'
```

## Post General PR Comment (not inline)

```bash
gh pr comment {pr} --body "Comment text"
```

## Deprecated: position parameter

The `position` parameter (diff offset from `@@` header) still works but is being phased out. Prefer `line` and `side` for new code.
