# GitHub CLI PR Comments Syntax

## Inline Comments on PR Diffs

Use `position` (diff line offset from `@@` header), not `line`:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --method POST \
  -f body="Comment text" \
  -f path="src/file.py" \
  -F position=5 \
  -f commit_id="$(gh pr view {pr} --json headRefOid -q '.headRefOid')"
```

**Important:** Use `-F` (not `-f`) for integer values like `position`.

## Reply to Existing Comment

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  --method POST \
  -f body="Reply text"
```

## Get Comments on a PR

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | {id, path, body: .body[:80]}'
```

## Post General PR Comment (not inline)

```bash
gh pr comment {pr} --body "Comment text"
```
