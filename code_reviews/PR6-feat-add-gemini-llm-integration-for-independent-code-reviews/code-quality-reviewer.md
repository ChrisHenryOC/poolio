# Code Quality Review for PR #6

## Summary

This PR adds Gemini LLM integration for independent code reviews through a new agent definition, slash command, and documentation. The implementation follows existing patterns well and adheres to Kent Beck's principle of simplicity. The main concerns are duplicated prompt content between the agent and command files, inconsistent error handling patterns, and a shell injection risk via heredoc that should use piped input instead.

## Findings

### Critical

None

### High

**Shell injection risk via heredoc pattern** - `.claude/agents/gemini-reviewer.md:33-73` and `.claude/commands/gemini-review.md:117-158`

Both files instruct embedding diff content directly into a heredoc with `<<'EOF'` delimiter. If a malicious PR diff contains a line with only `EOF`, it terminates the heredoc early and subsequent lines execute as shell commands.

The agent file (line 33) shows:
```bash
cat /tmp/pr{NUMBER}.diff | gemini -p "..."
```

This piped approach is safe. However, the command file's "Alternative approach" section (lines 117-158) suggests a heredoc pattern that is vulnerable.

**Recommendation**: Remove the heredoc alternative entirely and standardize on the piped `cat | gemini -p` approach shown in the agent file, which is both safer and simpler. This aligns with Beck's "Fewest elements" rule.

### Medium

**Duplicated prompt content violates DRY** - `.claude/agents/gemini-reviewer.md:33-73` vs `.claude/commands/gemini-review.md:117-158`

The Gemini prompt (review focus, project context, output format) is duplicated between the agent definition and the slash command. Any future changes to the review criteria or output format require updates in two places.

**Recommendation**: Extract the prompt to a shared location (e.g., `.claude/references/gemini-prompt.md`) and reference it from both files, or document that one is the source of truth. Alternatively, since the command file references `docs/gemini-setup.md`, the prompt could live there.

---

**Inconsistent error handling between agent and command** - `.claude/agents/gemini-reviewer.md:82-87` vs `.claude/commands/gemini-review.md:169-175`

The agent defines error handling as:
- Auth error: Note GEMINI_API_KEY needs configuration
- Timeout: Save partial output, note timeout
- Empty response: Note that Gemini returned no output

The command defines it differently:
- Auth error: Tell user to see `docs/gemini-setup.md`
- Timeout: Report partial output, suggest retry with smaller diff
- Empty response: Report that Gemini returned no output, suggest retry

These inconsistencies could lead to different user experiences depending on which entry point is used.

**Recommendation**: Align error handling between both files. The command's guidance (referencing setup docs, suggesting retry) is more actionable.

---

**review-pr.md has ambiguous parallel execution instruction** - `.claude/commands/review-pr.md:195-202`

The instruction says "Launch in parallel (all 6 agents in a single message with multiple Task tool calls)" but lists gemini-reviewer with "(optional - skip if GEMINI_API_KEY not set)". It is unclear how the caller determines if GEMINI_API_KEY is set before launching agents.

**Recommendation**: Either move the GEMINI_API_KEY check to the gemini-reviewer agent itself (so it can gracefully exit), or provide explicit guidance on how to check the key before launching. The agent file already handles this: "If Gemini is unavailable, write a brief note to the output file explaining this and exit gracefully" (line 20).

### Observations

**Good: Piped input pattern is safe** - `.claude/agents/gemini-reviewer.md:33`

The `cat /tmp/pr{NUMBER}.diff | gemini -p "..."` pattern avoids shell injection because the diff content never enters the shell command parsing. This is the correct approach.

**Good: Clear exit guidance** - `.claude/agents/gemini-reviewer.md:18-20`

"If Gemini is unavailable, write a brief note to the output file explaining this and exit gracefully." This follows the principle of handling failure modes explicitly.

**Good: Minimal tool permissions** - `.claude/agents/gemini-reviewer.md:4` and `.claude/commands/gemini-review.md:95`

The agent uses `tools: Bash, Read, Write` and the command uses `allowed-tools: Bash(gemini),Read,Write`. The command's more restrictive `Bash(gemini)` pattern limits shell access appropriately.

**Good: Documentation included** - `docs/gemini-setup.md`

The setup documentation covers installation, API key configuration (with multiple secure options), security notes, and troubleshooting. This addresses a common gap in CLI tool integrations.

**Naming follows existing conventions** - Both new files use kebab-case consistent with existing commands (`review-pr.md`, `merge-pr.md`).

**Beck's Four Rules Assessment**:

| Rule | Assessment |
|------|------------|
| Passes the tests | N/A - Configuration files, no executable code |
| Reveals intention | Good - Purpose clear from descriptions and step-by-step instructions |
| No duplication | Issue - Prompt duplicated between agent and command |
| Fewest elements | Good - Simple integration, no over-engineering |
