# Documentation Accuracy Review for PR #6

## Summary

This PR adds Gemini LLM integration for independent code reviews, introducing two new commands (`gemini-eval.md`, `gemini-review.md`) and modifying the existing `review-pr.md` workflow. The documentation is generally well-structured and follows existing conventions, but has several gaps: missing setup instructions for the Gemini CLI tool, inconsistent error handling documentation, and a placeholder pattern that requires manual replacement during execution.

## Findings

### Critical

None

### High

**Missing Gemini CLI setup documentation** - `.claude/commands/gemini-eval.md:36` and `.claude/commands/gemini-review.md:83` - Both commands assume a `gemini` CLI tool exists and is available in PATH, but there is no documentation on how to install or configure this tool. The commands reference setting `GEMINI_API_KEY`, but users need to know:

1. Where to obtain the Gemini CLI (is it `npm install -g @google/gemini-cli`? A pip package? A standalone binary?)
2. How to obtain an API key
3. Any required configuration beyond the environment variable

**Recommendation**: Add a setup section to `gemini-eval.md` or create a separate `.claude/references/gemini-setup.md` document explaining prerequisites. Alternatively, add a link to official Gemini CLI documentation.

### Medium

**Inconsistent error handling documentation** - `.claude/commands/gemini-review.md:135-139` - The error handling section lists three error conditions but the guidance is incomplete:

- "Auth error" says to tell user to set `GEMINI_API_KEY` but does not specify what the actual error message looks like
- "Timeout" suggests reporting "partial output if any" but does not explain how to detect or handle timeouts in a heredoc-style command
- "Empty response" says "Log and report failure" but does not specify where to log or what format

**Recommendation**: Either remove the specific error handling guidance (let implementers handle errors naturally) or make it actionable with specific detection patterns.

**Placeholder instruction in bash example** - `.claude/commands/gemini-review.md:99-100` and `:127` - The template shows `[INSERT DIFF CONTENT]` as a placeholder with a separate instruction "Replace `[INSERT DIFF CONTENT]` with the actual diff content." This is less clear than other command patterns in the codebase.

**Recommendation**: Follow the pattern used in `gemini-eval.md` which uses variables and clearer templating, or show the actual variable substitution expected: `${DIFF_CONTENT}` or similar.

**Missing command cross-reference** - `.claude/commands/gemini-eval.md` - The eval command does not mention `gemini-review.md` and vice versa. Users discovering one may not know about the other.

**Recommendation**: Add a brief "See Also" section linking related commands.

### Observations

**Consistent formatting with existing commands** - The new commands follow the established YAML frontmatter pattern (`description`, `allowed-tools`) and step-based structure used by other commands in the repository.

**Good integration with existing workflow** - The changes to `review-pr.md` appropriately mark the Gemini review as "(Optional)" and include clear skip conditions ("Skip if Gemini is unavailable or GEMINI_API_KEY is not set").

**Output format alignment** - The Gemini review output format in `gemini-review.md:104-123` matches the format used by other reviewers in the codebase (Summary, Findings by severity, file:line references), which will facilitate consolidation.

**Appropriate scope** - The PR correctly updates the consolidation instructions in `review-pr.md` to account for Gemini findings, adding "Gemini unique findings" to the template and modifying questions to consider conflicts with Gemini.

**Allowed-tools consistency** - The `Bash(gemini*)` pattern in allowed-tools is appropriately permissive for gemini commands while following the glob pattern convention used elsewhere.

**No README or CLAUDE.md updates** - The new capability is not documented in the project's main documentation files. For an internal developer workflow tool, this may be acceptable. However, if this feature is intended to be used by other contributors, consider adding a brief mention to `CLAUDE.md` under a "Code Review Workflow" or "Available Commands" section.
