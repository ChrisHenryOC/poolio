---
allowed-tools: Read, Write, Glob, Grep, Task, mcp__sequential-thinking__sequentialthinking
description: Create a comprehensive architecture document from requirements and codebase analysis
---

Generate a comprehensive architecture document for: $ARGUMENTS

This command synthesizes requirements analysis, codebase pattern extraction, and platform constraints into a production-quality architecture document.

---

## PHASE 1: GATHER INPUTS

### 1.1 Locate and Read Requirements

1. If `$ARGUMENTS` is a file path, read it as the requirements document
2. If `$ARGUMENTS` is a feature/project name, search for:
   - `docs/requirements.md`
   - `docs/$ARGUMENTS-requirements.md`
   - `requirements/*.md`
3. If no requirements file exists, inform the user and stop

### 1.2 Analyze Existing Codebase (if applicable)

Search for existing code patterns:

- **Project structure**: `Glob` for `src/**/*.py`, `src/**/*.cpp`, `lib/**/*`
- **Existing abstractions**: `Grep` for `class`, `interface`, `abstract`
- **Configuration patterns**: Look for `config.json`, `settings.toml`, `*.ini`
- **Test patterns**: `Grep` in `tests/` for testing conventions
- **Similar features**: Find implementations of related functionality

### 1.3 Check for Reference Architecture

Look for:
- `CLAUDE.md` project instructions
- Existing `docs/architecture*.md` files
- `README.md` with architecture guidance

---

## PHASE 2: REQUIREMENTS ANALYSIS

Extract and organize requirements into categories:

| Category | What to Identify |
|----------|------------------|
| **System Purpose** | Problem being solved, target users, success criteria |
| **Functional Requirements** | Core features, capabilities, user interactions |
| **Data Entities** | What data is stored, processed, transmitted |
| **Integrations** | External systems, APIs, protocols, services |
| **Non-Functional Requirements** | Performance, reliability, security, scalability |
| **Constraints** | Technology mandates, platform limitations, timeline |

---

## PHASE 3: PLATFORM CONSTRAINT ANALYSIS

### 3.1 Identify Target Platforms

Determine all runtime environments:
- Desktop/server (Python, Node.js, etc.)
- Embedded/microcontroller (CircuitPython, MicroPython, Arduino)
- Browser (JavaScript)
- Mobile (iOS, Android)

### 3.2 Document Platform Limitations

For each constrained platform, identify:

| Constraint Type | Examples |
|-----------------|----------|
| **Unavailable modules** | `dataclasses`, `abc`, `asyncio`, `typing` |
| **Memory limits** | Heap size, stack size, file system |
| **Processing limits** | No threads, limited float precision |
| **Library availability** | Which packages exist for the platform |

### 3.3 Define Compatibility Patterns

For each limitation, specify the workaround pattern:

```markdown
| Unavailable | Use Instead | Example |
|-------------|-------------|---------|
| `@dataclass` | Plain class with `__init__` | `class Foo: def __init__(self, x): self.x = x` |
| `ABC` | Duck typing + `NotImplementedError` | Base class methods raise `NotImplementedError` |
```

### 3.4 Dual Implementation Strategy

If code must run on multiple platforms (e.g., device + desktop tests):
- Identify which features need dual implementations
- Specify how to detect runtime environment
- Define testing strategy for each platform

---

## PHASE 4: CODEBASE PATTERN EXTRACTION

### 4.1 Structural Patterns

Document existing conventions:
- Directory organization and naming
- Module/package structure
- File naming conventions
- Import organization

### 4.2 Code Patterns

Extract established approaches with file:line references:
- Error handling patterns
- Logging conventions
- Configuration loading
- Resource management (cleanup, context managers)
- State management

### 4.3 Interface Patterns

Identify how components interact:
- Function signature conventions
- Class design patterns
- Dependency injection approach
- Event/callback patterns

### 4.4 Testing Patterns

Document testing conventions:
- Test file organization
- Fixture patterns
- Mocking approach
- CI/CD integration

---

## PHASE 5: ARCHITECTURAL DECISIONS

**REQUIRED**: Use `mcp__sequential-thinking__sequentialthinking` for complex decisions.

### 5.1 Initial Analysis (6-10 thoughts)

Work through key architectural questions:

1. **Domain modeling** - What are the core concepts and relationships?
2. **Component boundaries** - Where should module boundaries be drawn?
3. **Integration contract** - What is the primary integration mechanism?
4. **Technology selection** - What technologies best fit requirements + constraints?
5. **Trade-off resolution** - How to balance competing requirements?

### 5.2 Decision Points Requiring Sequential Thinking

| Decision Area | Questions to Resolve |
|---------------|---------------------|
| **Architecture style** | Monolith vs microservices vs hybrid? |
| **Communication** | Sync vs async? REST vs message queue vs events? |
| **Data storage** | SQL vs NoSQL vs file-based? Centralized vs distributed? |
| **State management** | Where does state live? How is it synchronized? |
| **Error handling** | Fail-fast vs resilient? Retry strategies? |
| **Security model** | Authentication, authorization, secrets management? |

### 5.3 When to Branch Thinking

Use `branchFromThought` when:
- Multiple valid approaches exist with different trade-offs
- The choice significantly impacts implementation effort
- Stakeholder input might change the direction

### 5.4 Document All Decisions

For each significant decision, capture:
- **Decision**: What was chosen
- **Rationale**: Why this approach
- **Alternatives rejected**: What else was considered and why not
- **Consequences**: What this decision enables/constrains

---

## PHASE 6: GENERATE ARCHITECTURE DOCUMENT

Create the architecture document with the following structure:

```markdown
# Architecture: [Project Name]

> Generated from: [requirements file path]
> Date: [current date]

## Table of Contents

[Auto-generate based on sections included]

---

## System Overview

[2-3 paragraphs describing the system, its purpose, and key goals]

### System Architecture Diagram

[ASCII diagram showing major components and their relationships]

### Component Summary

| Component | Purpose | Technology | Communication |
|-----------|---------|------------|---------------|
| [Name] | [What it does] | [Language/framework] | [How it talks to others] |

---

## Architecture Principles

### Core Principle: [Primary Integration Mechanism]

[Explain the fundamental architectural approach - e.g., "Message Protocol as Integration Contract"]

**Why this approach?**
- [Reason 1]
- [Reason 2]

**What this enables:**
- [Benefit 1]
- [Benefit 2]

### Design Rationale Evolution

[Document how the architecture evolved through analysis - show the thinking process]

---

## Architecture Decisions

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| [Choice made] | [Why] | [What else was considered] |

---

## Components

### [Component Name]

**Location:** `path/to/component/`

**Purpose:** [What this component does]

**Technology:** [Language, framework, platform]

**Interfaces:**
- Inputs: [What it receives]
- Outputs: [What it produces]
- Dependencies: [What it requires]

**Key Interfaces:**

```python
# Actual class/function signatures with docstrings
class ComponentName:
    def __init__(self, config, dependencies):
        """
        Args:
            config: Configuration object
            dependencies: Required dependencies
        """
        ...

    def primary_method(self, input_param):
        """
        Description of what this does.

        Args:
            input_param: Description (type)

        Returns:
            Description of return value (type)
        """
        ...
```

**Structure:**

```text
component/
├── __init__.py
├── main.py          # Entry point
├── core.py          # Core logic
└── utils.py         # Utilities
```

[Repeat for each component]

---

## Directory Structure

```text
project/
├── src/
│   ├── [module]/
│   └── ...
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── config/
└── scripts/
```

---

## Data Flow

### [Flow Name] Flow

```text
[Component A]              [Component B]              [Component C]
     │                          │                          │
     │── [action] ─────────────>│                          │
     │                          │── [action] ─────────────>│
     │                          │                          │
     │<── [response] ───────────│<── [response] ───────────│
```

[Repeat for each major flow]

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| [Layer name] | [Technology] | [Why chosen] |

---

## Platform Compatibility

### [Platform Name] Constraints

| Unavailable | Use Instead | Pattern |
|-------------|-------------|---------|
| [Module/feature] | [Alternative] | [Code example] |

### Dual Implementation Strategy

| Environment | Runtime | Features | Notes |
|-------------|---------|----------|-------|
| [On-device] | [Platform] | [Subset] | [Limitations] |
| [Desktop/CI] | [Platform] | [Full] | [Testing focus] |

---

## [Protocol/API] Specification

### Message/Request Structure

```json
{
  "field": "description",
  ...
}
```

### [Type] Types

| Type | Direction | Purpose |
|------|-----------|---------|
| [Name] | [In/Out/Both] | [Description] |

### Validation Rules

| Rule | Value | Rationale |
|------|-------|-----------|
| Max size | [limit] | [why] |
| Timestamp freshness | [limit] | [why] |

### Example Messages/Requests

```json
// [Scenario name]
{
  ...
}
```

---

## Reliability Patterns

### [Pattern Name]

```python
# Code example showing the pattern
def pattern_example():
    ...
```

**Configuration:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| [Name] | [Value] | [What it controls] |

[Repeat for each reliability pattern: retry, circuit breaker, watchdog, etc.]

---

## Configuration

### Environment Model

| Environment | Identifier | Hardware | Use Case |
|-------------|------------|----------|----------|
| [Name] | [prefix/key] | [Enabled/Disabled] | [Purpose] |

### Configuration Schema

```json
{
  "setting": {
    "type": "string",
    "default": "value",
    "description": "What this controls"
  }
}
```

### Hot-Reload vs Restart-Required

| Category | Parameters | Behavior |
|----------|------------|----------|
| **Hot-reloadable** | [list] | Applied immediately |
| **Restart-required** | [list] | Requires restart |

---

## Credential Management

### Storage by Platform

| Platform | Storage Mechanism | Notes |
|----------|-------------------|-------|
| [Platform] | [Where/how stored] | [Security notes] |

### Provisioning Flow

1. [Step 1]
2. [Step 2]
...

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| [Aspect] | [Dev approach] | [Prod approach] |

---

## Deployment

### [Platform/Component] Deployment

**Deploy Script:** `scripts/deploy_[component].sh`

```bash
#!/bin/bash
# Actual deployment script content
```

**File Structure After Deployment:**

```text
[target]/
├── [file]
└── ...
```

### Environment-Specific Configuration

| Environment | Config File | Key Differences |
|-------------|-------------|-----------------|
| [Name] | [Path] | [What changes] |

### Rollback Plan

1. [How to identify last good version]
2. [How to retrieve previous version]
3. [How to redeploy]
4. [How to verify]

---

## Testing & CI/CD

### Testing Strategy

| Test Type | Framework | Location | Purpose |
|-----------|-----------|----------|---------|
| Unit | [framework] | `tests/unit/` | [What's tested] |
| Integration | [framework] | `tests/integration/` | [What's tested] |

### Platform Testing Setup

```python
# Example conftest.py or test setup
```

### Integration Test Scenarios

| Scenario | Description | Expected Behavior |
|----------|-------------|-------------------|
| [Name] | [What's being tested] | [What should happen] |

### CI/CD Pipeline

```yaml
# GitHub Actions or equivalent
name: CI
on: [push, pull_request]
jobs:
  test:
    ...
```

---

## Build Sequence

### Phase 1: [Name] ([duration estimate])

**Goal:** [What this phase achieves]

**Tasks:**
- [ ] [Task 1]
- [ ] [Task 2]
...

**Exit Criteria:** [How to know phase is complete]

[Repeat for each phase]

---

## Critical Details

### Error Handling

**[Component Name]:**
- [Specific error handling approach]
- [What exceptions to catch]
- [Recovery strategy]

### State Management

**[Component Name]:**
- [State machine if applicable]
- [Persistence approach]
- [Recovery on restart]

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| [Metric] | [Value] | [How to measure] |

### Security Considerations

- [Security concern 1 and mitigation]
- [Security concern 2 and mitigation]

### Source Control & Secrets

**Files to gitignore:**

```gitignore
# Secrets
[pattern]
```

**Template files to commit:**

| Template | Actual | Purpose |
|----------|--------|---------|
| [.template file] | [actual file] | [What it contains] |

---

## Sequential Thinking Summary

**Initial hypothesis:** [What the architecture was first thought to be]

**Key insights:**
1. [Insight from thinking process]
2. [Insight from thinking process]

**Revisions made:**
- [How understanding evolved]

**Final rationale:** [Why this architecture was chosen]

---

## Resolved Questions

| Question | Decision | Rationale |
|----------|----------|-----------|
| [Question that came up] | [What was decided] | [Why] |

---

## Open Questions

[List any ambiguities or decisions requiring stakeholder input]

1. **[Question]** - [Context and options being considered]

---

## PHASE 7: QUALITY VERIFICATION

Before finalizing, verify the document against this checklist:

### Completeness Checklist

- [ ] **System overview** with diagram and component summary
- [ ] **Architecture principles** explaining the core approach
- [ ] **Decision table** with rationale and alternatives
- [ ] **All components** have:
  - [ ] Purpose and location
  - [ ] Actual code interfaces (class/function signatures)
  - [ ] Directory structure
  - [ ] Dependencies documented
- [ ] **Data flows** with sequence diagrams
- [ ] **Tech stack** with rationale for each choice
- [ ] **Platform compatibility** patterns (if constrained platforms)
- [ ] **Protocol/API specification** with:
  - [ ] Message/request structure
  - [ ] Validation rules
  - [ ] Examples
- [ ] **Reliability patterns** with code examples
- [ ] **Configuration** with:
  - [ ] Environment model
  - [ ] Schema
  - [ ] Hot-reload vs restart-required
- [ ] **Credential management** approach
- [ ] **Deployment** with:
  - [ ] Actual scripts
  - [ ] Rollback plan
- [ ] **Testing & CI/CD** with:
  - [ ] Test strategy
  - [ ] Integration scenarios
  - [ ] CI pipeline configuration
- [ ] **Build sequence** with phases, tasks, exit criteria
- [ ] **Critical details** (error handling, state, performance, security)
- [ ] **Sequential thinking summary** showing decision process
- [ ] **Resolved questions** documenting decisions made
- [ ] **Open questions** for stakeholder input

### Quality Checks

- [ ] All code examples are syntactically correct
- [ ] All file paths are consistent with directory structure
- [ ] All component names are used consistently throughout
- [ ] Platform constraints have corresponding compatibility patterns
- [ ] Each decision has clear rationale
- [ ] No placeholder text remains (e.g., "[TBD]", "[TODO]")

---

## PHASE 8: WRITE OUTPUT

1. Determine output path:
   - Same directory as input requirements file
   - Named `architecture.md`
   - Or as specified by user

2. Write the generated document

3. Summarize for user:
   - Output file location
   - Key architectural decisions made
   - Open questions requiring input
   - Suggested next steps

---

## Guidelines

- **Be specific**: Base all recommendations on actual requirements and codebase patterns
- **Be concrete**: Include actual code, not pseudocode placeholders
- **Be complete**: Address all aspects of implementation, deployment, and operations
- **Be honest**: Flag uncertainties in "Open Questions" rather than guessing
- **Follow project conventions**: Match existing code style and patterns
- **Document thinking**: Include Sequential Thinking Summary to show decision rationale
- **Make decisions**: Choose one approach and commit rather than listing options
