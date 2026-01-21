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

## 3. USE SEQUENTIAL THINKING FOR DECOMPOSITION

**REQUIRED**: Use `mcp__sequential-thinking__sequentialthinking` to break down the implementation:

### Issue Decomposition (estimate 8-12 thoughts)

1. **Map features to components** - Which architectural components implement which features?
2. **Identify dependencies** - What must be built before what?
3. **Find the critical path** - What sequence determines minimum timeline?
4. **Size the work** - Is each issue small enough for one session?
5. **Verify completeness** - Do all issues sum to full requirements coverage?
6. **Revise as needed** - Use `isRevision: true` when finding gaps or oversized issues

### Key Questions to Resolve

- What is the natural build order based on dependencies?
- Are there issues that can be parallelized?
- Where are the integration risk points?
- What needs to be stubbed/mocked early?

### When to Branch Thinking

Use `branchFromThought` when facing decisions like:

- Bottom-up vs. top-down implementation order
- Depth-first (one feature complete) vs. breadth-first (all features partial)
- Which component to tackle first when multiple are independent

## 4. DECOMPOSE INTO ISSUES

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

**IMPORTANT**: Use phase-prefixed format `X.Y` where X = phase number, Y = sequence within phase.

Examples: `1.1`, `1.2`, `1.3`, `2.1`, `2.2`, `3.1`...

This ensures:

- **Unambiguous IDs**: Plan issue `2.3` is clearly different from GitHub issue `#47`
- **Self-documenting**: The phase is encoded directly in the issue ID
- **Safe replacement**: When create-git-issues runs, no collision risk between formats
- **Traceability**: Final document can show mapping (e.g., `#47 (was 2.3)`)

Dependencies use the same format: `Dependencies: 1.2, 1.5`

## 5. DEFINE DEPENDENCIES

Create a dependency graph:

- Identify which issues block others
- Group into implementation phases
- Ensure no circular dependencies
- Mark critical path items

## 6. GENERATE PLAN DOCUMENT

Create the implementation plan with this structure:

```markdown
# Implementation Plan: [Project Name]

> Generated from:
> - Requirements: [path]
> - Architecture: [path]
> - Date: [current date]

## Overview

[Brief summary of what will be built and approach]

## Sequential Thinking Summary

[Document the decomposition process:]

- **Initial approach**: [How you first planned to break down the work]
- **Revisions made**: [Issues that were split, merged, or reordered]
- **Key insights**: [What the thinking process revealed about dependencies/risks]

## Phases

| Phase | Name          | Description                        | Issues     |
| ----- | ------------- | ---------------------------------- | ---------- |
| 1     | Foundation    | Setup and core infrastructure      | 1.1-1.7    |
| 2     | Core Domain   | Core models and business logic     | 2.1-2.8    |
| 3     | Services      | Service layer implementation       | 3.1-3.7    |
| 4     | API/Interface | External interfaces                | 4.1-4.6    |
| 5     | Integration   | Final integration, edge cases      | 5.1-5.7    |

## Issue Backlog

### Issue 1.1: [Title]

- **Phase**: 1 - Foundation
- **Type**: Setup
- **Description**: [What needs to be done]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]
- **Files**: [Expected files to create/modify]
- **Dependencies**: None
- **Tests**: [What tests to write]

### Issue 1.2: [Title]

- **Phase**: 1 - Foundation
- **Type**: [Type]
- **Description**: [What needs to be done]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
- **Files**: [Expected files]
- **Dependencies**: 1.1
- **Tests**: [Test requirements]

### Issue 2.1: [Title]

- **Phase**: 2 - Core Domain
- **Type**: Core
- **Description**: [What needs to be done]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
- **Files**: [Expected files]
- **Dependencies**: 1.3, 1.5
- **Tests**: [Test requirements]

[Continue for all issues...]

## Dependency Graph

```text
Phase 1: [1.1] -> [1.2] -> [1.3]
                      \
Phase 2:               -> [2.1] -> [2.2]
                              \
Phase 3:                       -> [3.1] -> [3.2]
```

## Critical Path

[List the sequence of issues that determines minimum timeline]

`1.1 -> 1.2 -> 2.1 -> 3.1 -> 4.1`

## Risk Items

| Risk   | Impact   | Mitigation         |
| ------ | -------- | ------------------ |
| [Risk] | [Impact] | [How to address]   |

## Open Questions

[Any decisions needed before implementation can begin]

## Summary

| Metric                   | Count |
| ------------------------ | ----- |
| Total Issues             | [N]   |
| Phase 1 (Foundation)     | [n]   |
| Phase 2 (Core Domain)    | [n]   |
| ...                      | ...   |
| Critical Path Length     | [n]   |
```

## 7. WRITE OUTPUT

1. Write to `implementation-plan.md` in the same directory as the requirements file
2. Report total issue count and phase breakdown
3. Highlight any blocking dependencies or risks identified

---

## Guidelines

- **Phase-prefixed numbering**: Use X.Y format (phase.sequence) for clear distinction from GitHub numbers
- **Self-documenting IDs**: Issue 2.3 = Phase 2, issue 3 within that phase
- **Keep issues small**: An AI agent should complete each in one session
- **Clear dependencies**: Every issue explicitly lists what it depends on (e.g., "Dependencies: 1.3, 1.5")
- **Testable**: Each issue includes specific test requirements
- **TDD-ready**: Issues are structured for Red-Green-Refactor workflow
- **No gaps**: The sum of all issues should fully implement the requirements
- **GitHub-ready**: Issue format is designed for easy translation to GitHub issues
- **Document thinking**: Include the Sequential Thinking Summary to show decomposition rationale

## Sequential Thinking Integration Points

| Planning Phase           | When to Use Sequential Thinking                      |
| ------------------------ | ---------------------------------------------------- |
| Feature mapping          | Complex features spanning multiple components        |
| Dependency analysis      | Unclear build order or circular dependency risk      |
| Issue sizing             | Features that may need splitting or combining        |
| Critical path finding    | Multiple potential paths through the dependency graph |
| Risk identification      | Integration points or external dependencies          |

## Troubleshooting

If the decomposition feels wrong or incomplete:

1. **Use Sequential Thinking** to diagnose:
   - Set `isRevision: true` to reconsider earlier decisions
   - Use `branchFromThought` to explore alternative orderings
   - Continue until decomposition feels natural and complete

2. Update the plan with revised issues
3. Re-verify that all requirements are covered
