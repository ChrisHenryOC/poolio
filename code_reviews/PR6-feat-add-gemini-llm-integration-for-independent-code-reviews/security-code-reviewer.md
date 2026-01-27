# Security Review

## Summary

This PR adds Gemini LLM integration for independent code reviews via two new command files and modifications to the review-pr command. The changes introduce a potential command injection vulnerability through the heredoc pattern, and expose credential handling guidance that should be reviewed for secure practices.

## Findings

### Critical

None

### High

**Potential Command Injection via Heredoc** - `.claude/commands/gemini-review.md:82-124` - The command template uses a heredoc pattern (`<<'EOF'`) with instructions to insert diff content directly into the shell command. If the diff content contains shell metacharacters or malformed heredoc terminators (e.g., a line containing only `EOF`), this could cause unexpected shell behavior or command injection.

The instruction states:
```
Replace `[INSERT DIFF CONTENT]` with the actual diff content.
```

If an attacker can craft a PR diff containing `EOF` on its own line followed by malicious shell commands, those commands could execute. While the quoted heredoc (`<<'EOF'`) prevents variable expansion, it does not prevent premature heredoc termination.

**Recommendation**:
1. Use a more unique/random heredoc delimiter (e.g., `<<'GEMINI_REVIEW_END_MARKER_7a3b9c'`)
2. Alternatively, pipe the content via stdin or use a temporary file approach
3. Sanitize the diff content to escape or remove any occurrences of the heredoc terminator

**CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')**

### Medium

**API Key Exposure in Error Messages** - `.claude/commands/gemini-eval.md:53-56` and `.claude/commands/gemini-review.md:137` - The error handling guidance instructs users to set `GEMINI_API_KEY` as an environment variable, which is appropriate. However, there is no guidance about:
1. Avoiding logging or echoing the API key value
2. Ensuring the key is not exposed in shell history when set inline
3. Using secure credential storage mechanisms

**Recommendation**: Add guidance to use secure credential management:
- Use `.envrc` files with direnv (excluded from git)
- Reference 1Password CLI or similar secrets managers
- Warn against inline `export GEMINI_API_KEY="..."` in shell history

**CWE-522: Insufficiently Protected Credentials**

---

**Unrestricted Tool Permission Scope** - `.claude/commands/gemini-review.md:3` and `.claude/commands/gemini-eval.md:3` - The `allowed-tools` directive uses `Bash(gemini*)` which permits execution of any command starting with "gemini". While this is likely intended for the `gemini` CLI, it could potentially match other binaries or scripts if they exist on the system with that prefix.

**Recommendation**: Consider using the more specific pattern `Bash(gemini)` if only the exact `gemini` command is intended, or document the security assumption that no malicious `gemini*` binaries exist in PATH.

**CWE-284: Improper Access Control**

### Observations

1. **Defense in Depth**: The use of single-quoted heredoc (`<<'EOF'`) is a good practice as it prevents shell variable expansion within the heredoc body. This mitigates some injection risks but not the heredoc termination issue noted above.

2. **No Input Validation on PR Number**: The commands reference `$ARGUMENTS` which is expected to be a PR number. While this flows through the Claude command system (not directly to shell), validating that it is a numeric PR number before use would add defense in depth.

3. **External Service Dependency**: The integration relies on the external `gemini` CLI tool. The security posture of this integration depends on the security of that external tool, which is outside the scope of this codebase.

4. **Write Permission Scope**: The `gemini-review.md` command has `Write` permission, allowing it to save output files. This is appropriate for the use case but worth noting as it allows file system modifications.

5. **Kent Beck Alignment**: Following "simplicity over speculation," the core integration approach is straightforward. The security recommendations above focus on real attack vectors (heredoc injection from malicious diffs) rather than theoretical concerns.
