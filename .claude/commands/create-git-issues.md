---
allowed-tools: Read,Write,Edit,Bash(gh issue create:*),Bash(gh label create:*),Bash(gh issue list:*),Bash(gh label list:*),Bash(gh issue edit:*)
description: Create GitHub issues from an implementation plan
---

# Create GitHub Issues from Implementation Plan

Create GitHub issues from: $ARGUMENTS

**Expected argument:** `<implementation-plan.md>` (defaults to `docs/implementation-plan.md`)

## 1. VALIDATE & PREPARE

1. **Read the implementation plan**
   - Parse the file to extract all issues
   - Identify phases, types, and dependencies
   - Note the original plan issue numbers

2. **Ensure required labels exist**
   Create labels if they don't exist:
   ```bash
   # Phase labels
   gh label create "phase:1" --description "Phase 1 - Foundation" --color "0052CC" --force
   gh label create "phase:2" --description "Phase 2 - Core" --color "1D76DB" --force
   # ... create for each phase found in the plan

   # Type labels
   gh label create "type:setup" --description "Project setup" --color "D4C5F9" --force
   gh label create "type:model" --description "Data models" --color "C5DEF5" --force
   gh label create "type:core" --description "Core logic" --color "BFD4F2" --force
   gh label create "type:service" --description "Service layer" --color "D4E5F7" --force
   gh label create "type:api" --description "API/interface" --color "E6F0FA" --force
   gh label create "type:integration" --description "Integration" --color "C2E0C6" --force
   gh label create "type:test" --description "Testing" --color "FBCA04" --force
   gh label create "type:docs" --description "Documentation" --color "0075CA" --force
   ```

3. **Ask for user confirmation**
   - Show total issue count to be created
   - Explain that the implementation plan will be updated with actual GitHub issue numbers
   - Confirm before proceeding

## 2. PARSE IMPLEMENTATION PLAN

Extract from each issue section:

```markdown
### Issue #N: [Title]
- **Phase**: N - [Phase Name]
- **Type**: [Type]
- **Description**: [Description text]
- **Acceptance Criteria**:
  - [ ] Criterion 1
  - [ ] Criterion 2
- **Files**: [Expected files]
- **Dependencies**: #X, #Y (or None)
- **Tests**: [Test requirements]
```

Build a data structure:
```
issues = [
  {
    plan_number: 1,
    title: "...",
    phase: 1,
    type: "setup",
    description: "...",
    acceptance_criteria: [...],
    files: "...",
    dependencies: [3, 5],  # plan numbers
    tests: "..."
  },
  ...
]
```

## 3. CREATE ISSUES (Two-Pass Approach)

### Pass 1: Create all issues WITHOUT dependency references

Create issues sequentially and capture GitHub-assigned numbers:

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
*Generated from implementation plan*
EOF
)" \
  --label "phase:N" \
  --label "type:typename"
```

**Build the mapping** as each issue is created:
```
mapping = {
  1: 42,   # plan issue #1 -> GitHub issue #42
  2: 43,   # plan issue #2 -> GitHub issue #43
  ...
}
```

### Pass 2: Update issues with correct dependency references

For each issue that has dependencies, edit the issue body to include the mapped GitHub issue numbers:

```bash
gh issue edit GITHUB_NUMBER --body "$(cat <<'EOF'
[Original body content]

## Dependencies

Blocked by: #42, #43

EOF
)"
```

## 4. UPDATE IMPLEMENTATION PLAN DOCUMENT

After all GitHub issues are created, **rewrite the implementation plan** to use actual GitHub issue numbers:

1. **Update issue headers**: `### Issue #1:` → `### Issue #42:`
2. **Update dependency references**: `Dependencies: #1, #3` → `Dependencies: #42, #44`
3. **Update phases table**: `Issues | #1-#7` → `Issues | #42-#48`
4. **Update critical path**: `#1 -> #8 -> #16` → `#42 -> #49 -> #57`
5. **Update summary table** with new issue ranges

Use the Edit tool to make these replacements throughout the document.

**IMPORTANT**: This is a destructive update. The original plan numbers will be replaced with GitHub issue numbers. This ensures the plan and GitHub stay in sync.

## 5. VERIFY & REPORT

1. **Generate summary report**
   ```
   ## Issue Creation Summary

   Total issues created: 66

   | Phase | Issues Created |
   |-------|----------------|
   | 1 - Foundation | #42-#48 (7 issues) |
   | 2 - Game Engine | #49-#57 (9 issues) |
   | ... |

   ## Number Mapping

   | Original Plan # | GitHub Issue # |
   |-----------------|----------------|
   | 1 | 42 |
   | 2 | 43 |
   | ... |
   ```

2. **Confirm implementation plan was updated**
   - Show the user that docs/implementation-plan.md now uses GitHub issue numbers

## Guidelines

- **Sequential creation** - Create issues one at a time to maintain order
- **Two-pass for dependencies** - First create all issues, then add dependency links with correct numbers
- **Plan update is mandatory** - Always update the implementation plan with actual GitHub numbers
- **Preserve plan structure** - Only change issue numbers, not content or organization
- **Rate limiting** - Add small delays between API calls if hitting GitHub limits

## Error Handling

- If issue creation fails, note the failure and continue with remaining issues
- Report all failures at the end with the plan number that failed
- For failed issues, the mapping will be incomplete - warn user
- Provide commands to manually create failed issues

## Example Usage

```
/create-issues docs/implementation-plan.md
```

Or with default path:
```
/create-issues
```

## Workflow Summary

```
1. Parse implementation plan
   ↓
2. Create labels
   ↓
3. Create issues (capture GitHub numbers)
   ↓
4. Build plan-to-GitHub number mapping
   ↓
5. Update issues with mapped dependencies
   ↓
6. Rewrite implementation plan with GitHub numbers
   ↓
7. Report results
```
