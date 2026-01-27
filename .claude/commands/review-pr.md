---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(mkdir:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*),Bash(gh pr list:*),Bash(gemini)
description: Review a pull request
---

Review PR $ARGUMENTS (auto-detect from current branch if empty).

## Step 1: Setup

```bash
gh pr view $ARGUMENTS --json title,number -q '.number + " " + .title'
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
mkdir -p code_reviews/PR$ARGUMENTS-<sanitized-title>
```

Directory name: PR number + lowercase title with non-alphanumeric replaced by hyphens.

## Step 2: Launch Agents

Launch in parallel (all 6 agents in a single message with multiple Task tool calls):

- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer
- gemini-reviewer (optional - skip if GEMINI_API_KEY not set)

Each agent reads `/tmp/pr$ARGUMENTS.diff` and saves findings to `code_reviews/PR$ARGUMENTS-<title>/{agent}.md`.

## Step 3: Consolidate with Sequential Thinking

After agents complete, **use `mcp__sequential-thinking__sequentialthinking`** to analyze and consolidate findings:

### Analysis Process (estimate 6-10 thoughts)

1. **Categorize findings** - Group by severity and type across all agent reports
2. **Identify patterns** - Are multiple agents flagging related issues?
3. **Evaluate against Beck's Four Rules** - Does the PR satisfy each rule?
4. **Determine scope** - Which issues are in PR scope vs. pre-existing?
5. **Assess actionability** - Can each issue be fixed in this PR?
6. **Prioritize** - What's the critical path for fixes?
7. **Revise as needed** - Use `isRevision: true` if earlier categorization was wrong

### Key Questions to Resolve

- Are there conflicting recommendations between agents (including Gemini)?
- Did Gemini catch anything the Claude agents missed (or vice versa)?
- Which findings are symptoms vs. root causes?
- What's the minimum set of changes needed?

### When to Branch Thinking

Use `branchFromThought` when:

- An issue could be categorized multiple ways (security vs. code quality)
- Unclear if something is in PR scope
- Multiple valid fix approaches exist

Create `PR$ARGUMENTS-CONSOLIDATED-REVIEW.md`:

```markdown
# Consolidated Review for PR #$ARGUMENTS

## Summary

[2-3 sentences]

## Sequential Thinking Summary

- **Key patterns identified**: [What emerged from analyzing agent reports]
- **Conflicts resolved**: [Any disagreements between agents and how resolved]
- **Gemini unique findings**: [Issues Gemini caught that Claude agents missed, if any]
- **Prioritization rationale**: [Why issues were ordered this way]

## Beck's Four Rules Check

- [ ] Passes the tests - Are there adequate tests for new code?
- [ ] Reveals intention - Is the code self-explanatory?
- [ ] No duplication - Is DRY maintained?
- [ ] Fewest elements - Is there any over-engineering?

## Issue Matrix

(Use format from `.claude/memories/review-issue-matrix.md` if available)

## Actionable Issues

[Issues where In PR Scope AND Actionable are Yes]

## Deferred Issues

[Issues where either is No, with reason]
```

## Step 4: Post Comment

```bash
gh pr comment $ARGUMENTS --body "[summary by severity]"
```

## Step 5: Commit Review Files

```bash
gh pr view $ARGUMENTS --json headRefName -q '.headRefName'
git fetch origin <branch> && git checkout <branch>
git add code_reviews/PR$ARGUMENTS-*/
git commit -m "docs: Add code review for PR #$ARGUMENTS"
git push origin <branch>
```

---

## Agent Instructions

Each agent:

1. Read `/tmp/pr$ARGUMENTS.diff` first
2. Apply Kent Beck's principles from `.claude/references/kent-beck-principles.md`
3. Save findings to `code_reviews/PR$ARGUMENTS-<title>/{agent-name}.md` with:
   - Summary (2-3 sentences)
   - Findings by severity
   - File:line references

---

## Sequential Thinking Integration Points

| Review Phase            | When to Use Sequential Thinking                          |
| ----------------------- | -------------------------------------------------------- |
| Consolidating reports   | Multiple agents with overlapping or conflicting findings |
| Beck's Rules evaluation | Unclear if PR satisfies a rule                           |
| Scope determination     | Changes touch pre-existing code                          |
| Severity assignment     | Issue could be High or Medium depending on context       |
| Writing summary         | Complex PR with many interrelated changes                |
