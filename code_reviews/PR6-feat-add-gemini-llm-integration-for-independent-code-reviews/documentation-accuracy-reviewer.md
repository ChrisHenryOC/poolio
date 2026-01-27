# Documentation Accuracy Review for PR #6

## Summary

This PR adds Gemini LLM integration for independent code reviews, introducing a command (`gemini-review.md`), an agent (`gemini-reviewer.md`), setup documentation (`docs/gemini-setup.md`), and modifications to the `review-pr.md` workflow. The documentation contains several inconsistencies: references to a non-existent `gemini-eval` command, conflicting output filename instructions between the agent and command, and unverifiable installation instructions for the Gemini CLI.

## Findings

### Critical

None

### High

**H1: Documentation references non-existent `gemini-eval` command** - `docs/gemini-setup.md:3`

The setup documentation states:
```markdown
This document describes how to set up the Gemini CLI for use with the `/gemini-eval` and `/gemini-review` commands.
```

However, there is no `gemini-eval.md` file in `.claude/commands/`. Only `gemini-review.md` exists. The consolidated review files in this PR also reference `gemini-eval.md` extensively (lines 264, 266, 269, etc.), suggesting either:
1. A command was removed but references were not updated, or
2. The reviews were written against a different version of the code

**Recommendation**: Either remove references to `gemini-eval` from `docs/gemini-setup.md`, or add the missing `gemini-eval.md` command if it was intended to be part of this PR.

---

**H2: Unverifiable Gemini CLI installation instructions** - `docs/gemini-setup.md:8-17`

The setup document provides two installation methods:

```bash
npm install -g @google/generative-ai-cli
```

and

```bash
brew install gemini
```

These package names should be verified against actual package registries. As of my knowledge cutoff, Google's official Gemini CLI is distributed differently (the official CLI is `@anthropic-ai/claude` for Claude, but Gemini's official CLI tooling has varied). The npm package `@google/generative-ai-cli` may not exist, and `brew install gemini` may install something unrelated to Google's Gemini.

**Recommendation**: Verify the actual package names and installation methods. Link to Google's official documentation for the Gemini CLI rather than providing potentially outdated commands.

### Medium

**M1: Inconsistent output filename between agent and command** - `.claude/agents/gemini-reviewer.md:20` vs `.claude/commands/gemini-review.md:70`

The agent specifies:
```markdown
3. Save output to `code_reviews/PR{NUMBER}-{title}/gemini-reviewer.md`
```

The command specifies:
```markdown
Save Gemini's response to `code_reviews/PR$ARGUMENTS-<title>/gemini-review.md`.
```

One uses `gemini-reviewer.md`, the other uses `gemini-review.md`. This could cause confusion about where to find or expect the output file.

**Recommendation**: Standardize on one filename. The agent filename (`gemini-reviewer.md`) follows the pattern of other agents in the directory.

---

**M2: review-pr.md incorrectly states Bash(gemini) permission applies to GEMINI_API_KEY checking** - `.claude/commands/review-pr.md:27`

The command states:
```markdown
- gemini-reviewer (optional - skip if GEMINI_API_KEY not set)
```

However, `review-pr.md` has `allowed-tools: ... Bash(gemini)` in its frontmatter (line 2), which only permits running the `gemini` command. There is no mechanism documented for how the orchestrating command would check if `GEMINI_API_KEY` is set before deciding to skip the agent. The Task tool launching agents does not have access to environment variable checking.

**Recommendation**: Clarify how the skip-if-unavailable logic should work in practice. Either document that the agent itself handles the unavailability gracefully (which the agent does - line 14 of `gemini-reviewer.md`), or remove the suggestion that the parent command can skip based on API key presence.

---

**M3: Consolidated review references line numbers that do not exist in current files** - `code_reviews/PR6-.../CONSOLIDATED-REVIEW.md:263-270`

The issue matrix references specific line numbers like:
- `.claude/commands/gemini-review.md:83` (heredoc delimiter)
- `.claude/commands/gemini-review.md:100` (placeholder)
- `.claude/commands/gemini-review.md:133` (fallback path)

However, the actual `gemini-review.md` file is only 87 lines. These line numbers appear to reference a version of the file that no longer exists or was written against the heredoc version shown in the diff rather than the current piped version.

**Recommendation**: Update line number references to match the current file content, or note that line numbers reference a specific commit/version.

### Observations

**O1: Good documentation structure** - The new `docs/gemini-setup.md` follows a logical flow (Installation -> API Key Configuration -> Security Notes -> Verification -> Troubleshooting) that makes it easy for users to get started.

**O2: Appropriate cross-references** - Both `gemini-review.md:84-86` and `gemini-reviewer.md:12` correctly point to `docs/gemini-setup.md` for setup instructions. This follows the DRY principle by keeping setup instructions in one place.

**O3: Self-documenting command structure** - The command and agent files use clear step-by-step instructions that reveal their intention without requiring additional comments, aligning with Kent Beck's "reveals intention" principle.

**O4: Piped input approach addresses security concern** - The current `gemini-review.md` uses `cat /tmp/pr$ARGUMENTS.diff | gemini -p "..."` rather than a heredoc, which addresses the heredoc injection risk mentioned in the security review. The comment on line 22 ("avoids heredoc injection risks") documents why this pattern was chosen.

**O5: Duplicated prompt content is necessary** - The Gemini prompt in both `gemini-review.md` and `gemini-reviewer.md` duplicates the output format specification from `_base-reviewer.md`. This duplication is intentional and necessary because the prompt must be self-contained when sent to Gemini. A comment noting this design decision would help future maintainers understand why DRY is not applied here.
