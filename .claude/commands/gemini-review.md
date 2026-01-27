---
description: Get independent code review from Gemini LLM
allowed-tools: Bash(gemini*),Read,Write
---

Get an independent code review from Gemini for PR diff at `/tmp/pr$ARGUMENTS.diff`.

This provides a second opinion from a different LLM to catch issues Claude might miss.

## Step 1: Read the Diff

Read `/tmp/pr$ARGUMENTS.diff` to get the PR changes.

If the file doesn't exist, inform the user to run `/review-pr` first or provide a PR number.

## Step 2: Build and Execute Gemini Prompt

Construct the prompt with the diff content and run:

```bash
gemini <<'EOF'
You are an expert code reviewer. Analyze this pull request diff and provide a thorough review.

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

## Diff
[INSERT DIFF CONTENT]

## Output Format

# Gemini Independent Review

## Summary
[2-3 sentence assessment]

## Findings

### Critical
[Security vulnerabilities, data loss, breaking changes - or "None"]

### High
[Bugs, performance issues, significant over-engineering - or "None"]

### Medium
[Code quality, maintainability concerns - or "None"]

### Observations
[Questions, suggestions, or patterns noticed]

For each finding: **Issue** - `file:line` - Recommendation
EOF
```

Replace `[INSERT DIFF CONTENT]` with the actual diff content.

## Step 3: Save Output

Save Gemini's response to `code_reviews/PR$ARGUMENTS-<title>/gemini-review.md`.

If the directory doesn't exist, create it or save to `/tmp/gemini-review-$ARGUMENTS.md`.

## Error Handling

- **Auth error**: Tell user to set `GEMINI_API_KEY` environment variable
- **Timeout**: Report partial output if any, suggest retry
- **Empty response**: Log and report failure
