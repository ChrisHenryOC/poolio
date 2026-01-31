---
description: Get independent code review from Gemini LLM
allowed-tools: Bash(gemini),Read,Write
---

Get an independent code review from Gemini for PR diff at `code_reviews/PR$ARGUMENTS-<title>/pr.diff`.

This provides a second opinion from a different LLM to catch issues Claude might miss.

## Prerequisites

Requires the Gemini CLI. See `docs/gemini-setup.md` for installation and API key configuration.

## Step 1: Read the Diff

Read `code_reviews/PR$ARGUMENTS-<title>/pr.diff` to get the PR changes.

If the file doesn't exist, inform the user to run `/review-pr` first or provide a PR number.

## Step 2: Execute Gemini Review

Use piped input with the `-p` flag (avoids heredoc injection risks):

```bash
cat code_reviews/PR$ARGUMENTS-<title>/pr.diff | gemini -p "You are an expert code reviewer. Analyze this pull request diff and provide a thorough review.

IMPORTANT: DO NOT attempt to apply changes, modify files, or execute commands. Your ONLY task is to review the code and provide written feedback.

## Review Focus
- Code quality and maintainability
- Potential bugs or edge cases
- Security concerns
- Performance implications
- Over-engineering or unnecessary complexity

## Project Context
IoT pool automation system (CircuitPython/C++ for ESP32). Principles:
- Reliability is critical (controls physical hardware like valves)
- Simple solutions over clever ones
- Kent Beck's Four Rules: Tests pass, Reveals intention, No duplication, Fewest elements

## Output Format

# Gemini Independent Review

## Summary
[2-3 sentence assessment]

## Findings

### Critical
[Security vulnerabilities, data loss, breaking changes - or None]

### High
[Bugs, performance issues, significant over-engineering - or None]

### Medium
[Code quality, maintainability concerns - or None]

### Observations
[Questions, suggestions, or patterns noticed]

For each finding: **Issue** - file:line - Recommendation

Remember: ONLY provide review text. Do not attempt any file operations."
```

## Step 3: Save Output

Save Gemini's response to `code_reviews/PR$ARGUMENTS-<title>/gemini-reviewer.md`.

If the directory doesn't exist:

1. Create it if possible, OR
2. Save to `/tmp/gemini-reviewer-$ARGUMENTS.md` and notify user: "Note: Review saved to /tmp/ because code_reviews directory not found."

## Error Handling

- **Auth error**: Tell user to see `docs/gemini-setup.md` for API key configuration
- **Timeout**: Report partial output if any, suggest retry with smaller diff
- **Empty response**: Report that Gemini returned no output, suggest retry
- **"Tool not found" in output**: Ignore - Gemini sometimes tries to use unavailable tools

## See Also

- `docs/gemini-setup.md` - Installation and configuration
