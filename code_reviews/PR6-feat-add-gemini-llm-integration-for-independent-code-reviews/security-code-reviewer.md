# Security Review for PR #6

## Summary

This PR adds Gemini LLM integration for independent code reviews through new agent and command definitions. The implementation uses a piped input pattern (`cat file | gemini -p`) which is safer than heredoc approaches for handling untrusted diff content. The main security considerations are API key management guidance and the tool permission glob pattern.

## Findings

### Critical

None

### High

None - The earlier security review in the PR identified a "heredoc injection" risk, but examining the actual code shows the implementation uses piped input (`cat /tmp/pr$ARGUMENTS.diff | gemini -p "..."`) rather than heredocs. This design explicitly "avoids heredoc injection risks" as noted in `.claude/commands/gemini-review.md:114`.

### Medium

**Tool Permission Glob May Match Unintended Commands** - `.claude/commands/gemini-review.md:95` and `.claude/agents/gemini-reviewer.md:4`

The `allowed-tools` directive uses patterns like `Bash(gemini)` which is appropriately specific in the command file. However, in `.claude/commands/review-pr.md:186`, the tool permission was updated to include `Bash(gemini)` which is correct.

*CWE-284: Improper Access Control* - The permission scope is reasonable for the intended use case. No action required.

---

**API Key Handling Guidance Could Be Stronger** - `docs/gemini-setup.md:46-51`

The setup documentation includes good security guidance:
- "Never commit API keys to version control"
- "Avoid setting keys inline in commands (exposes in shell history)"
- "Use environment variables or secrets managers"
- "Rotate keys periodically"

However, the error handling in `.claude/commands/gemini-review.md:169-174` only tells users to "see `docs/gemini-setup.md`" without immediate security context. A user troubleshooting in a hurry might skip to the quickest solution.

*CWE-522: Insufficiently Protected Credentials* - Low risk, documentation is present but could be more prominent.

**Recommendation**: Consider adding inline security reminders in the error handling sections, e.g., "Note: Never paste API keys directly in terminal commands."

### Observations

1. **Safe Input Handling Pattern**: The implementation correctly uses piped input (`cat file | gemini -p "prompt"`) rather than heredocs or command substitution. This prevents:
   - Heredoc terminator injection (no `EOF` or delimiter to escape)
   - Shell metacharacter expansion in the diff content
   - Command injection via backticks or `$()` in diffs

2. **PR Number Validation**: The `$ARGUMENTS` variable is expected to be a PR number. While the Claude command system provides some isolation, the value flows into file paths (`/tmp/pr$ARGUMENTS.diff`). A malformed argument like `../../etc/passwd` would fail to find the file rather than exposing sensitive data, since the path is read-only. This is acceptable defense-in-depth.

3. **External Tool Trust**: The security of this integration depends on the Gemini CLI tool itself. The prompt includes `IMPORTANT: DO NOT attempt to apply changes, modify files, or execute commands` (`.claude/agents/gemini-reviewer.md:35-36`), which is a reasonable attempt to constrain the LLM's behavior, though it relies on the external model's compliance.

4. **Write Permission Scope**: The `gemini-reviewer` agent has `Write` tool access (`.claude/agents/gemini-reviewer.md:4`) limited to saving review output. This is appropriate and minimal.

5. **Fallback Path Security**: When the primary output directory is unavailable, the command falls back to `/tmp/` (`.claude/commands/gemini-review.md:166-167`). The `/tmp/` directory is world-writable, so review files saved there could be read by other users on shared systems. This is low risk for typical single-user development machines but worth noting for shared environments.

6. **Kent Beck Alignment**: Following "simplicity over speculation," this review focuses on real attack vectors. The piped input pattern is simple and secure. No unnecessary security abstractions are recommended.

## Beck's Four Rules Check

| Rule | Assessment |
|------|------------|
| Passes the tests | N/A - Configuration files, no executable tests |
| Reveals intention | Yes - Security measures (piped input) are documented inline |
| No duplication | Yes - Security setup consolidated in `docs/gemini-setup.md` |
| Fewest elements | Yes - Minimal permissions requested, no over-engineered auth flows |
