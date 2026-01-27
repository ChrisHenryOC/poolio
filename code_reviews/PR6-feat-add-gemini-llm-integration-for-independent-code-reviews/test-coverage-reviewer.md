# Test Coverage Review for PR #6

## Summary

This PR adds Gemini LLM integration for independent code reviews through markdown command definitions (`.claude/agents/gemini-reviewer.md`, `.claude/commands/gemini-review.md`) and documentation (`docs/gemini-setup.md`). Since these are declarative configuration files rather than executable code, traditional unit testing does not apply directly. However, the PR introduces untested behavior specifications and edge cases that warrant validation strategies, and the heredoc-based approach has an injection vulnerability that testing would have caught.

## Findings

### Critical

None

### High

**Heredoc injection vulnerability untested** - `.claude/commands/gemini-review.md:33-73` and `.claude/agents/gemini-reviewer.md:33-73` - The command uses `<<'EOF'` heredoc to pass diff content to Gemini. If a PR diff contains the literal string `EOF` on its own line, it will prematurely terminate the heredoc, potentially executing subsequent diff content as shell commands. A simple test with a crafted diff containing `EOF` would immediately reveal this vulnerability.

```
# Untested scenario that would fail:
# Diff containing:
#   EOF
#   rm -rf /
# Would escape the heredoc and execute malicious commands
```

**Recommendation**: Change to piped input pattern which is already shown in the agent file:
```bash
cat /tmp/pr{NUMBER}.diff | gemini -p "..."
```
This avoids heredoc termination issues entirely. Add a test fixture with `EOF` in the diff to verify.

---

**No integration test for Gemini output format handling** - `.claude/commands/review-pr.md:43-55` - The consolidation step must parse Gemini's output and reconcile it with Claude agent outputs. There are no test fixtures or validation that Gemini's actual output matches the expected format specified in the prompt. Different LLM models can interpret format instructions differently.

**Recommendation**: Create test fixtures with sample Gemini outputs (both well-formed and edge cases like partial responses) to validate the consolidation logic handles real-world variance.

### Medium

**Graceful degradation path untested** - `.claude/commands/review-pr.md:33` states "skip if GEMINI_API_KEY not set" but there is no specification of what "skip" means:
- Does the review continue without Gemini findings?
- Is a placeholder written to the output directory?
- Is the user notified?

**Recommendation**: Document expected behavior and consider adding a smoke test that runs the review workflow with GEMINI_API_KEY unset to verify graceful degradation.

---

**Edge cases for input detection undocumented** - `.claude/agents/gemini-reviewer.md:23-26` - The instruction to "Read `/tmp/pr{NUMBER}.diff`" assumes the file exists. Edge cases not covered:
- File does not exist (previous step failed)
- File is empty (PR has no diff)
- File is extremely large (could hit API limits)

**Recommendation**: Add explicit handling instructions for these cases. For executable code, these would be test cases.

---

**Error scenario coverage inconsistent** - `.claude/agents/gemini-reviewer.md:82-86` lists three error types (auth, timeout, empty response) while `.claude/commands/gemini-review.md:169-175` handles four (adding "Tool not found"). This inconsistency suggests error handling was added ad-hoc rather than systematically designed.

**Recommendation**: Align error handling between agent and command definitions. In TDD terms, define the error contract first, then implement consistently.

### Observations

**TDD Assessment: Not Applicable / Negative Indicators**

These are configuration files, so TDD does not directly apply. However, several anti-patterns suggest specification-after-implementation thinking:

| Indicator | Evidence |
|-----------|----------|
| Implementation before behavior spec | Error handling differs between files - suggests fixes added as problems arose |
| Missing edge case coverage | No guidance for empty diff, missing file, rate limiting |
| Happy path focus | Documentation describes success flow in detail but error handling is sparse |
| No testable contract | Output format is specified but no way to verify Gemini conforms |

**Kent Beck's Four Rules Analysis:**

| Rule | Assessment |
|------|------------|
| Passes the tests | N/A - No tests exist; command behavior is untested |
| Reveals intention | Partial - Commands are readable but error behavior is unclear |
| No duplication | Concern - Prompt text duplicated between agent/command files |
| Fewest elements | Good - Implementation is minimal |

**Testing Strategy Recommendations:**

1. **Smoke test script** (`scripts/test-gemini-commands.sh`):
   - Verify `gemini` CLI is available
   - Test with mock diff containing `EOF` (security)
   - Test with missing API key (graceful degradation)
   - Test with empty diff (edge case)

2. **Test fixtures** (`tests/fixtures/gemini/`):
   - `sample-gemini-output.md` - Expected format
   - `malformed-gemini-output.md` - Missing sections
   - `diff-with-eof.patch` - Security test case

3. **CI validation**:
   - Lint markdown files (already in place per CLAUDE.md)
   - Validate YAML frontmatter in command files
   - Check for consistent allowed-tools patterns

**Missing Test Scenarios Table:**

| Scenario | File | Status |
|----------|------|--------|
| Diff contains `EOF` string | `gemini-review.md:33-73` | Not handled (security risk) |
| GEMINI_API_KEY not set | `review-pr.md:33` | Behavior unspecified |
| Gemini returns empty response | `gemini-reviewer.md:86` | Documented, untested |
| Gemini times out | `gemini-reviewer.md:85` | Documented, untested |
| Diff file does not exist | `gemini-reviewer.md:24` | Not addressed |
| Very large diff (>100KB) | N/A | Not addressed |
| Gemini rate limited | `docs/gemini-setup.md:77-79` | Mentioned in docs only |
| Output directory does not exist | `gemini-review.md:162-168` | Fallback documented |
