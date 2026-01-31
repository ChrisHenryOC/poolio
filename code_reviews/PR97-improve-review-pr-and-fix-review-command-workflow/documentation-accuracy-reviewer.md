# Documentation Accuracy Review for PR #97

## Summary

This PR improves the review workflow by consolidating the diff file location from `/tmp/` to within the `code_reviews/` directory, providing better traceability. However, the documentation changes are incomplete: the gemini-reviewer agent and gemini-review command still reference the old `/tmp/pr*.diff` location, creating a critical inconsistency that will cause the Gemini integration to fail.

## Findings

### High

1. **Incomplete Documentation Update - Gemini Agent** - `/Users/chrishenry/source/poolio_rearchitect/.claude/agents/gemini-reviewer.md:18` and `:27`

   The gemini-reviewer agent still references the old diff location:
   - Line 18: `1. Read '/tmp/pr{NUMBER}.diff' using the Read tool`
   - Line 27: `cat /tmp/pr{NUMBER}.diff | gemini -p "..."`

   These should be updated to `code_reviews/PR{NUMBER}-{title}/pr.diff` to match the changes made in `_base-reviewer.md` and `review-pr.md`.

   **Recommendation**: Update both references to use the new `code_reviews/` path pattern.

2. **Incomplete Documentation Update - Gemini Command** - `/Users/chrishenry/source/poolio_rearchitect/.claude/commands/gemini-review.md:6`, `:16`, and `:25`

   The gemini-review command still references the old diff location in three places:
   - Line 6: `Get an independent code review from Gemini for PR diff at '/tmp/pr$ARGUMENTS.diff'.`
   - Line 16: `Read '/tmp/pr$ARGUMENTS.diff' to get the PR changes.`
   - Line 25: `cat /tmp/pr$ARGUMENTS.diff | gemini -p "..."`

   **Recommendation**: Update all three references to use `code_reviews/PR$ARGUMENTS-<title>/pr.diff`.

### Medium

3. **Pseudo-code in Setup Instructions** - `/Users/chrishenry/source/poolio_rearchitect/.claude/commands/fix-review.md:27`

   The setup section contains `<branch>` placeholder that requires manual substitution:
   ```bash
   git fetch origin <branch> && git checkout <branch>
   ```

   While the previous line shows how to get the branch name, the instruction relies on the user to mentally substitute the value. This is consistent with the existing pattern in `review-pr.md:116-117`, but a comment explaining this would improve clarity.

   **Recommendation**: Consider adding a brief comment like `# Use the branch name from the previous command` or document that `<branch>` is a placeholder.

4. **Inconsistent Placeholder Style** - `/Users/chrishenry/source/poolio_rearchitect/.claude/commands/review-pr.md:12-13`

   The PR uses `<sanitized-title>` as a placeholder, while other places use `<title>`. The diff shows:
   ```bash
   mkdir -p code_reviews/PR$ARGUMENTS-<sanitized-title>
   gh pr diff $ARGUMENTS > code_reviews/PR$ARGUMENTS-<sanitized-title>/pr.diff
   ```

   But later in the same file (line 29), it references `<title>`:
   ```
   Each agent reads `code_reviews/PR$ARGUMENTS-<title>/pr.diff`
   ```

   **Recommendation**: Standardize on one placeholder style, preferably `<title>` since that is used more consistently throughout the documentation.

### Low

5. **Removed Section Without Replacement Reference** - `/Users/chrishenry/source/poolio_rearchitect/.claude/commands/fix-review.md:39-46` (removed lines in diff)

   The "When Stuck on a Fix" section was removed from `fix-review.md`. While the content about Sequential Thinking for diagnostics is now covered in the "Troubleshooting" section at the end of the file (lines 153-159), the removal might cause users to miss this guidance since it was previously inline with the implementation flow.

   **Recommendation**: This is acceptable as the guidance remains in the file, but ensure the Troubleshooting section is discoverable.

6. **Improved Commit Behavior** - `/Users/chrishenry/source/poolio_rearchitect/.claude/commands/fix-review.md:53`

   Changed from `git add -A` to `git add -u` and added PR number to commit message. This is a positive change that prevents accidentally staging untracked files. The commit message now includes the PR number for better traceability.

   **Recommendation**: None - this is a documentation improvement.

## Documentation Consistency Matrix

| File | Uses New Path | Uses Old Path | Status |
|------|--------------|---------------|--------|
| `.claude/commands/review-pr.md` | Yes | No | OK |
| `.claude/commands/fix-review.md` | Yes | No | OK |
| `.claude/agents/_base-reviewer.md` | Yes | No | OK |
| `.claude/agents/gemini-reviewer.md` | No | Yes | INCONSISTENT |
| `.claude/commands/gemini-review.md` | No | Yes | INCONSISTENT |

## Files Changed

- `.claude/agents/_base-reviewer.md` - Path updated correctly
- `.claude/commands/fix-review.md` - Path documentation added, commit command improved
- `.claude/commands/review-pr.md` - Path updated correctly for diff storage
