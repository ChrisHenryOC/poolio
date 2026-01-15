---
allowed-tools: Read,Write,Glob,Grep
description: Create an implementation plan from requirements and architecture docs
---

# Implementation Plan Generator

Generate an implementation plan from: $ARGUMENTS

**Expected arguments:** `<requirements.md> <architecture.md>`

## 1. VALIDATE INPUTS

1. Parse arguments to get paths to both documents
2. Read the requirements document
3. Read the architecture document
4. Determine output path (same directory as requirements, named `implementation-plan.md`)

## 2. ANALYZE DOCUMENTS

From the **requirements document**, extract:

- Feature list and acceptance criteria
- Priority indicators (must-have vs nice-to-have)
- User stories or use cases

From the **architecture document**, extract:

- Component structure and boundaries
- Dependencies between components
- Tech stack decisions
- Data models

## 3. DECOMPOSE INTO ISSUES

Break down the implementation into small, AI-agent-sized issues:

### Issue Sizing Guidelines

Each issue should:

- Be completable in a single focused session (1-2 hours of work)
- Touch no more than 3-5 files
- Have a single clear objective
- Be independently testable
- Follow TDD (include test requirements)

### Issue Types

- **Setup**: Project scaffolding, dependencies, configuration
- **Model**: Data models and schemas
- **Core**: Core domain logic
- **Service**: Business logic services
- **API**: Endpoints and interfaces
- **Integration**: External system connections
- **Test**: Additional test coverage
- **Docs**: Documentation updates

### Issue Numbering

**IMPORTANT**: Use simple incrementing integers (1, 2, 3, ...) for issue IDs, NOT phase-prefixed numbers (1.1, 1.2, 2.1).

This ensures:
- Issue numbers can align with GitHub issue numbers when created in order
- Single numbering scheme reduces confusion
- Dependencies reference simple numbers (e.g., "Depends on: #3" not "Depends on: Issue 1.3")

Phases are tracked via the **Phase** field on each issue, not via the issue number.

## 4. DEFINE DEPENDENCIES

Create a dependency graph:

- Identify which issues block others
- Group into implementation phases
- Ensure no circular dependencies
- Mark critical path items

## 5. GENERATE PLAN DOCUMENT

Create the implementation plan with this structure:

```markdown
# Implementation Plan: [Project Name]

> Generated from:
> - Requirements: [path]
> - Architecture: [path]
> - Date: [current date]

## Overview

[Brief summary of what will be built and approach]

## Phases

| Phase | Name | Description | Issues |
|-------|------|-------------|--------|
| 1 | Foundation | Setup and core infrastructure | #1-#7 |
| 2 | Core Domain | Core models and business logic | #8-#15 |
| 3 | Services | Service layer implementation | #16-#22 |
| 4 | API/Interface | External interfaces | #23-#28 |
| 5 | Integration & Polish | Final integration, edge cases | #29-#35 |

## Issue Backlog

### Issue #1: [Title]
- **Phase**: 1 - Foundation
- **Type**: Setup
- **Description**: [What needs to be done]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]
- **Files**: [Expected files to create/modify]
- **Dependencies**: None
- **Tests**: [What tests to write]

### Issue #2: [Title]
- **Phase**: 1 - Foundation
- **Type**: [Type]
- **Description**: [What needs to be done]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
- **Files**: [Expected files]
- **Dependencies**: #1
- **Tests**: [Test requirements]

### Issue #8: [Title]
- **Phase**: 2 - Core Domain
- **Type**: Core
- **Description**: [What needs to be done]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
- **Files**: [Expected files]
- **Dependencies**: #3, #5
- **Tests**: [Test requirements]

[Continue for all issues...]

## Dependency Graph

```text
Phase 1: [#1] -> [#2] -> [#3]
                    \
Phase 2:             -> [#8] -> [#9]
                           \
Phase 3:                    -> [#16] -> [#17]
```

## Critical Path

[List the sequence of issues that determines minimum timeline]

#1 -> #2 -> #8 -> #16 -> #23

## Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | [Impact] | [How to address] |

## Open Questions

[Any decisions needed before implementation can begin]

## Summary

| Metric | Count |
|--------|-------|
| Total Issues | [N] |
| Phase 1 (Foundation) | [n] |
| Phase 2 (Core Domain) | [n] |
| ... | ... |
| Critical Path Length | [n] |
```

## 6. WRITE OUTPUT

1. Write to `implementation-plan.md` in the same directory as the requirements file
2. Report total issue count and phase breakdown
3. Highlight any blocking dependencies or risks identified

---

## Guidelines

- **Simple numbering**: Use #1, #2, #3... to align with GitHub issue numbers
- **Phase as metadata**: Each issue has a Phase field, not a phase-prefixed ID
- **Keep issues small**: An AI agent should complete each in one session
- **Clear dependencies**: Every issue explicitly lists what it depends on (e.g., "Dependencies: #3, #5")
- **Testable**: Each issue includes specific test requirements
- **TDD-ready**: Issues are structured for Red-Green-Refactor workflow
- **No gaps**: The sum of all issues should fully implement the requirements
- **GitHub-ready**: Issue format is designed for easy translation to GitHub issues
