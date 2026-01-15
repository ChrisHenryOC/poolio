---
allowed-tools: Read,Write,Glob,Grep
description: Create an architecture document from a requirements file
---

Generate an architecture document from requirements file: $ARGUMENTS

## 1. VALIDATE INPUT

1. Read the requirements file at path: `$ARGUMENTS`
2. If file doesn't exist or isn't readable, inform the user and stop
3. Determine output path (same directory as input, named `architecture.md`)

## 2. ANALYZE REQUIREMENTS

Read and analyze the requirements document to identify:

- **System Purpose**: What problem does this solve? Who are the users?
- **Key Features**: Core capabilities and functionality
- **Data Entities**: What data will be stored/processed?
- **Integrations**: External systems, APIs, services
- **Non-Functional Requirements**: Performance, security, scalability constraints

## 3. GENERATE ARCHITECTURE DOCUMENT

Create the architecture document with these sections:

### Output Template

```markdown
# Architecture: [Project Name]

> Generated from: [requirements file path]
> Date: [current date]

## System Overview

[2-3 paragraph description of the system, its purpose, and key goals based on requirements]

## Components

[Describe each major component/module:]

### [Component Name]
- **Responsibility**: What this component does
- **Interfaces**: How other components interact with it
- **Dependencies**: What it depends on

[Repeat for each component]

## Data Flow

[Describe how data moves through the system:]

1. [Entry point] -> [Processing] -> [Storage/Output]
2. [Additional flows as needed]

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.11+ | [reason based on requirements] |
| [Layer] | [Tech] | [reason] |

## Directory Structure

```
src/[project_name]/
├── core/           # Core domain logic
├── api/            # API layer
├── services/       # Business logic
├── models/         # Data models
└── utils/          # Utilities

tests/
├── unit/           # Unit tests
└── integration/    # Integration tests
```

## Key Design Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| [Decision] | [Why] | [What else was considered] |

## Open Questions

[List any ambiguities or decisions that need stakeholder input]
```

## 4. WRITE OUTPUT

1. Write the generated document to `architecture.md` in the same directory as the input file
2. Inform the user of the output location
3. Summarize key architectural decisions made

---

## Guidelines

- **Be specific**: Base all recommendations on the actual requirements, not generic advice
- **Stay minimal**: Only include components needed by the requirements
- **Follow project philosophy**: Apply Kent Beck's principles (simplest thing that works)
- **Flag uncertainties**: Use "Open Questions" for anything requiring clarification
