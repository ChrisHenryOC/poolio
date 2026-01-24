---
allowed-tools: Read,Write,Edit,Bash(gh issue create:*),Bash(gh label create:*),Bash(gh issue list:*),Bash(gh label list:*),Bash(gh issue edit:*),Bash(gh issue view:*)
description: Create GitHub issues from an implementation plan
---

# Create GitHub Issues from Implementation Plan

Create GitHub issues from: $ARGUMENTS

**Expected argument:** `<implementation-plan.md>` (defaults to `docs/implementation-plan.md`)

## 1. VALIDATE & PREPARE

1. **Validate the provided file**
   - Check if file exists
   - Look for `### Issue X.Y:` or `### Issue X.Ya:` headers to confirm it's an implementation plan (e.g., `### Issue 1.1:`, `### Issue 2.23a:`)
   - If no issues found, search for `**/implementation-plan.md` or `**/impl*.md` in the same directory tree
   - If still not found, ask user to provide the correct file path

2. **Parse the implementation plan**
   - Extract all issues from sections matching `### Issue X.Y:` or `### Issue X.Ya:` (supports letter suffixes like `2.23a`, `2.33a`)
   - **SKIP** issues matching any of these patterns:
     - `~~` strikethrough in the title (deferred placeholders)
     - `(DEFERRED` in the header line
     - `**Status**: **DEFERRED**` on a separate line within the issue
   - Identify phases (including sub-phases like 2a, 2b, 2c), types, and dependencies
   - Note the original plan issue IDs in X.Y or X.Ya format
   - **Plan ID gaps are expected** - deferred issues create gaps (e.g., 2.15 → 2.18 when 2.16-2.17 are deferred)

3. **Ensure required labels exist**

   First, extract all unique phases and types from the parsed issues. Then create labels in parallel:

   ```bash
   # Phase labels - create one for each unique phase found in the plan
   # Extract phase from "- **Phase**: X - Name" lines, create label like "phase:X"
   gh label create "phase:1" --description "Phase 1 - Foundation" --color "0052CC" --force
   gh label create "phase:2a" --description "Phase 2a - Pool Node" --color "1D76DB" --force
   # ... create for each unique phase found

   # Type labels - create one for each unique type found in the plan
   # Extract type from "- **Type**: TypeName" lines, lowercase it for label
   gh label create "type:setup" --description "Project setup" --color "D4C5F9" --force
   gh label create "type:core" --description "Core logic" --color "BFD4F2" --force
   gh label create "type:spike" --description "Exploratory spike" --color "FFDFBA" --force
   # ... create for each unique type found
   ```

   **Dynamic label creation**: Parse all `**Phase**:` and `**Type**:` fields from non-skipped issues, extract unique values, and create corresponding labels. Use consistent colors per category (blues for phases, purples/yellows for types). Only create labels for phases/types that have at least one issue being created.

4. **Validate against Summary table (if present)**
   - Look for a `## Summary` section with issue counts
   - Compare parsed issue count against stated totals (e.g., "Total Issues (MVP): 67")
   - Report any discrepancy as a warning

5. **Show pre-flight summary and confirm**
   Before creating issues, display:
   - Number of issues to create (and expected count if Summary table exists)
   - Phase breakdown (e.g., "Phase 1: 11 issues, Phase 2a: 11 issues")
   - Number of deferred issues skipped
   - Total dependencies count
   - Any validation warnings

   Ask user: "Proceed with creating X issues?"

## 2. VALIDATE PLAN WITH SEQUENTIAL THINKING

**Use `mcp__sequential-thinking__sequentialthinking`** to validate the plan before creating issues:

### Validation Analysis (estimate 4-6 thoughts)

1. **Check completeness** - Are all required fields present for each issue?
2. **Validate dependencies** - Do all referenced dependencies exist? Any circular dependencies?
3. **Verify phase ordering** - Do dependencies respect phase boundaries?
4. **Identify risks** - Are there issues that might fail to create (special characters, too long)?
5. **Plan error recovery** - What's the strategy if creation fails mid-way?

### Key Questions to Resolve

- Are there any issues referencing non-existent dependencies?
- Are there duplicate issue numbers in the plan?
- Do all issues have valid types that map to labels?
- Does the parsed count match any stated totals in a Summary section?
- Are there circular dependencies? (A depends on B, B depends on A)
- What are the root issues (no dependencies) and leaf issues (nothing depends on them)?

### Dependency Graph Analysis

Build a dependency graph and identify:
- **Root issues**: No dependencies (can start immediately)
- **Leaf issues**: Nothing depends on them (end of chains)
- **Circular dependencies**: A→B→C→A patterns (must be resolved)
- **Maximum chain depth**: Longest dependency path

### When to Branch Thinking

Use `branchFromThought` when:

- Circular dependency detected - explore how to resolve
- Missing required fields - decide whether to skip or ask user
- Ambiguous issue structure - determine correct parsing approach

## 3. PARSE IMPLEMENTATION PLAN

Extract from each issue section:

```markdown
### Issue X.Y: [Title]
- **Phase**: N - [Phase Name]
- **Type**: [Type]
- **Description**: [Description text]
- **Acceptance Criteria**:
  - [ ] Criterion 1
  - [ ] Criterion 2
- **Files**: [Expected files]
- **Dependencies**: X.Y, X.Z (or None)
- **Tests**: [Test requirements]
```

Build a data structure:

```text
issues = [
  {
    plan_id: "1.1",       # supports X.Y or X.Ya format (e.g., "2.23a")
    title: "...",
    phase: "1",           # string, may include letters (e.g., "2a", "2b", "4+")
    type: "setup",        # lowercase for label matching
    description: "...",
    acceptance_criteria: [...],
    files: "...",
    dependencies: ["1.3", "1.5"],  # plan IDs only - filter out prose
    tests: "..."
  },
  ...
]
```

**Dependency parsing**: The Dependencies field may contain various formats:
- Simple list: `1.4, 1.5, 1.6`
- With prose: `1.4, production experience showing need`
- Expanded ranges: `2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9`
- Prose references: `All issues 2.24 through 2.33a`

Extract only valid issue ID patterns (X.Y or X.Ya format) and ignore non-matching text. For prose references like "All issues X through Y", expand to the individual IDs if possible, or log a warning and skip.

## 4. CREATE ISSUES (Two-Pass Approach)

### Pass 1: Create all issues and build explicit mapping

Create issues sequentially and **build an explicit mapping** as each issue is created.

**IMPORTANT**: Do NOT assume sequential GitHub issue numbers. Always parse the actual issue number from the response URL.

```bash
# Create issue and capture the returned issue number
gh issue create \
  --title "[Type] Title" \
  --body "$(cat <<'EOF'
## Description

[Description from plan]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Files

[Expected files to create/modify]

## Dependencies

_Dependencies will be added after all issues are created._

## Tests

[Test requirements]

---
*Generated from implementation plan issue X.Y*
EOF
)" \
  --label "phase:N" \
  --label "type:typename"
```

**Build the mapping** by parsing each response URL:

```text
mapping = {}  # plan_id (X.Y format) -> github_issue_number

# After "gh issue create" returns:
# https://github.com/owner/repo/issues/42
# Extract 42 from the URL, store: mapping["1.1"] = 42

# Continue for each issue:
# mapping["1.2"] = 43  (or whatever GitHub assigns)
# mapping["2.1"] = 45  (might skip if concurrent creation happened!)
# ... etc
```

**Why explicit mapping (not offset calculation):**

- Issue creation could fail mid-way, causing gaps
- Concurrent issue creation from other sources could cause skips
- GitHub might skip numbers for internal reasons
- Explicit mapping is resilient to any numbering irregularities

### Pass 2: Update issues with correct dependency references

For each issue that has dependencies, use the mapping to translate plan numbers to GitHub numbers:

```bash
# First, get the current body (needed to preserve it)
gh issue view GITHUB_NUMBER --json body -q .body

# Then edit with the translated dependencies
gh issue edit GITHUB_NUMBER --body "$(cat <<'EOF'
[Original body content with Dependencies section updated]

## Dependencies

Blocked by: #${mapping[dep1]}, #${mapping[dep2]}

EOF
)"
```

## 5. UPDATE IMPLEMENTATION PLAN DOCUMENT

**Recommended approach**: Use the Write tool to rewrite the entire file rather than making many small Edit changes. This is faster and less error-prone.

1. Read the current implementation plan content
2. Use the explicit mapping built during issue creation
3. Replace all issue references using the mapping:
   - `### Issue 1.1:` → `### Issue #${mapping["1.1"]}:`
   - `Dependencies: 1.1, 1.3` → `Dependencies: #${mapping["1.1"]}, #${mapping["1.3"]}`
   - `Issues | 1.1-1.7` → `Issues | #${mapping["1.1"]}-#${mapping["1.7"]}`
   - Critical path references (e.g., `1.1 -> 1.2 -> 2.1` → `#42 -> #43 -> #45`)
   - Any other `X.Y` plan ID patterns in the document
4. Write the updated content back to the file

**Why Write over Edit:**

- Dozens of Edit calls are slow and can fail on non-unique strings
- Single Write operation is atomic and faster
- Easier to verify the complete result
- No risk of partial updates if interrupted

**IMPORTANT**: This is a destructive update. The original plan numbers will be replaced with GitHub issue numbers. This ensures the plan and GitHub stay in sync.

## 6. VERIFY & REPORT

1. **Generate summary report**

   ```text
   ## Issue Creation Summary

   Total issues created: 67
   Deferred issues skipped: 4

   ### By Phase
   | Phase | Issues Created |
   |-------|----------------|
   | 1 - Foundation | #1-#11 (11 issues) |
   | 2a - Pool Node | #12-#22 (11 issues) |
   | 2b - Valve Node | #23-#28 (6 issues) |
   | ... |

   ### By Type
   | Type | Count |
   |------|-------|
   | setup | 7 |
   | core | 31 |
   | integration | 15 |
   | test | 11 |
   | ... |

   ## Number Mapping

   | Plan ID | GitHub Issue # | Title |
   |---------|----------------|-------|
   | 1.1 | #1 | Project Setup and Structure |
   | 1.2 | #2 | Message Type Classes |
   | 2.1 | #12 | Pool Node Project Setup |
   | ... |
   ```

2. **Confirm implementation plan was updated**
   - Show the user that the implementation plan now uses GitHub issue numbers
   - Note the file path that was modified

---

## Guidelines

- **Sequential creation** - Create issues one at a time to maintain order
- **Explicit mapping** - Always track actual GitHub numbers, never assume sequential
- **Two-pass for dependencies** - First create all issues, then add dependency links with correct numbers
- **Write over Edit** - Use Write tool for plan update, not multiple Edit calls
- **Plan update is mandatory** - Always update the implementation plan with actual GitHub numbers
- **Preserve plan structure** - Only change issue numbers, not content or organization

## Error Handling

- If issue creation fails, note the failure and continue with remaining issues
- The mapping will have gaps for failed issues - track these explicitly
- Report all failures at the end with the plan number that failed
- For failed issues, provide commands to manually create them
- If too many failures occur, warn user and consider aborting

### Error Recovery with Sequential Thinking

If errors occur during issue creation, **use Sequential Thinking** to diagnose and recover:

1. **Analyze the failure** - What went wrong? (API error, validation, rate limit?)
2. **Assess impact** - Which issues are affected? Are dependencies broken?
3. **Plan recovery** - Retry? Skip? Manual intervention needed?
4. **Revise approach** - Use `isRevision: true` if initial strategy needs adjustment

## Example Usage

```text
/create-git-issues docs/implementation-plan.md
```

Or with default path:

```text
/create-git-issues
```

## Workflow Summary

```text
1. Validate file (check for ### Issue X.Y: pattern)
   ↓
2. Parse implementation plan (extract X.Y plan IDs)
   ↓
3. Validate with Sequential Thinking (dependencies, completeness)
   ↓
4. Create labels (in parallel)
   ↓
5. Show pre-flight summary, get confirmation
   ↓
6. Create issues (build explicit mapping: plan_id → GitHub #)
   ↓
7. Update issues with mapped dependencies
   ↓
8. Rewrite implementation plan (replace X.Y with GitHub #N)
   ↓
9. Report results with full mapping table (Plan ID → GitHub #)
```

---

## Sequential Thinking Integration Points

| Phase                    | When to Use Sequential Thinking                      |
| ------------------------ | ---------------------------------------------------- |
| Plan validation          | Checking dependencies, completeness, circular refs   |
| Parsing ambiguity        | Unclear issue structure or missing fields            |
| Error during creation    | API failures, rate limits, validation errors         |
| Dependency mapping       | Complex dependency chains or cross-phase references  |
| Recovery planning        | Multiple failures requiring strategy adjustment      |
