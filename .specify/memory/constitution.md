<!--
Sync Impact Report:
- Version change: NEW → 1.0.0
- New constitution created from project policies
- Principles derived from CLAUDE.md project policies
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check section expanded with concrete checklist
  ✅ spec-template.md - Already aligned with quality principles
  ✅ tasks-template.md - Already enforces TDD and testing requirements
  ✅ checklist-template.md - Generic template, no updates needed
- Follow-up TODOs: None
-->

# Project Constitution: obsidian-importer

**Version**: 1.0.0
**Ratification Date**: 2025-02-25
**Last Amended**: 2025-02-25

## Purpose

This constitution establishes the core principles and governance for the obsidian-importer project—an ETL system that transforms LLM conversation history into an Obsidian knowledge base. These principles guide all technical decisions, feature development, and architectural changes.

## Core Principles

### Principle 1: Simplicity Over Complexity

**Rule**: Favor clear, straightforward designs over elaborate abstractions. When choosing between a simple solution and a complex one, choose simplicity unless complexity provides demonstrable value.

**Rationale**: Complex systems are harder to maintain, debug, and extend. Simplicity reduces cognitive load and accelerates development velocity.

**Examples**:
- Prefer flat data structures over deeply nested ones
- Use direct file operations over custom abstraction layers
- Choose standard library solutions over third-party dependencies when practical

### Principle 2: No Backward Compatibility Constraints

**Rule**: Breaking changes are permitted and encouraged when they improve design quality. Do not compromise on better solutions to maintain backward compatibility.

**Rationale**: This is a personal/local-use tool, not a public API. The freedom to refactor aggressively enables continuous improvement without technical debt accumulation.

**Examples**:
- Restructure data formats when better alternatives emerge
- Rename functions, modules, or parameters for clarity
- Change configuration schemas to improve usability

### Principle 3: Quality Through Testing

**Rule**: Maintain minimum 80% test coverage. All features MUST include unit tests; critical paths MUST include integration tests.

**Rationale**: High test coverage prevents regressions, documents expected behavior, and enables confident refactoring (aligns with Principle 2).

**Testing Requirements**:
- Unit tests for all business logic
- Integration tests for pipeline nodes
- E2E tests for critical workflows (golden file validation)
- Test failures block commits (CI enforcement)

### Principle 4: Code Quality Enforcement

**Rule**: All code MUST pass both `ruff` and `pylint` checks before commit. CI automatically enforces these checks on PRs and main branch pushes.

**Rationale**: Automated linting catches common errors, enforces style consistency, and improves code readability.

**Standards**:
- Zero tolerance for linting violations
- Follow PEP 8 conventions
- Type hints required for public APIs

### Principle 5: Idempotency and Resume Safety

**Rule**: Pipeline operations MUST be idempotent. Re-running a pipeline with identical inputs MUST skip completed work and produce identical outputs.

**Rationale**: Supports iterative development, crash recovery, and partial pipeline execution without side effects.

**Implementation**:
- Use Kedro PartitionedDataset for resume tracking
- SHA256 file_id for duplicate detection
- Atomic operations where possible

### Principle 6: Data Integrity and Traceability

**Rule**: Every processed conversation MUST be traceable to its source via `file_id` (SHA256 hash). Duplicate detection MUST prevent redundant processing.

**Rationale**: Ensures data lineage, prevents duplicate content in knowledge base, and enables provenance tracking.

**Requirements**:
- All output Markdown includes `file_id` in frontmatter
- Collision handling documented
- Audit trail for transformations

## Governance

### Amendment Process

1. Proposals for constitutional changes must be documented in an issue or PR
2. Changes require explicit rationale and impact analysis
3. Version bumps follow semantic versioning:
   - **MAJOR**: Backward incompatible principle changes or removals
   - **MINOR**: New principles added or material expansions
   - **PATCH**: Clarifications, wording fixes, non-semantic changes

### Compliance Review

Constitution compliance is reviewed during:
- Feature planning (via spec.md)
- Implementation (via code review)
- Pull request approval
- Quarterly retrospectives

### Versioning Policy

- Constitution version tracked in this document header
- Sync Impact Report prepended as HTML comment on each update
- Dependent templates (.specify/templates/*.md) updated within same commit

### Conflict Resolution

If principles conflict in a specific scenario:
1. Principle 3 (Quality) and Principle 4 (Code Quality) take precedence over velocity
2. Principle 1 (Simplicity) takes precedence over feature richness
3. Escalate unresolvable conflicts to project maintainer

## Alignment with Templates

This constitution informs:
- **spec-template.md**: Requirements must align with quality principles
- **plan-template.md**: Implementation plans must respect simplicity and testing requirements
- **tasks-template.md**: Tasks categorized by principle (e.g., testing, refactoring)
- **checklist-template.md**: Checklists enforce quality and compliance checks

## Metadata

- **Project Type**: Personal ETL Tool
- **Primary Language**: Python 3.11+
- **Primary Framework**: Kedro 1.1.1
- **Target Environment**: Local development only
- **User Base**: Single user (maintainer)
