# Feature Specification: Transform Stage Debug Step Output

**Feature Branch**: `027-debug-step-output`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "transformはdebug時はstep毎のoutputを出力する"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Debug Transform Processing (Priority: P1)

As an ETL pipeline developer, I need to see intermediate output from each step in the Transform stage when debugging issues, so I can identify exactly where data transformations are failing or producing unexpected results.

**Why this priority**: This is the core functionality requested - enabling step-by-step visibility during debugging. Without this, developers cannot effectively troubleshoot Transform stage issues.

**Independent Test**: Can be fully tested by enabling debug mode and verifying that each Transform step writes its output to a designated location, delivering immediate troubleshooting value.

**Acceptance Scenarios**:

1. **Given** debug mode is enabled and Transform stage is processing, **When** each step completes, **Then** the step's output data is written to a step-specific output location
2. **Given** debug mode is disabled and Transform stage is processing, **When** each step completes, **Then** no intermediate step output is written (only final stage output)
3. **Given** debug mode is enabled and a Transform step fails, **When** the failure occurs, **Then** the partial output from that step is still written to help diagnose the issue

---

### User Story 2 - Output Organization (Priority: P2)

As an ETL pipeline developer, I need the debug outputs organized in a clear structure, so I can quickly locate and compare outputs from different steps during investigation.

**Why this priority**: While seeing the output is critical (P1), having it organized properly significantly improves the debugging experience but is not absolutely essential for basic functionality.

**Independent Test**: Can be tested by running a debug session and verifying that outputs are organized in a predictable directory structure with clear naming.

**Acceptance Scenarios**:

1. **Given** debug mode is enabled with multiple Transform steps, **When** all steps complete, **Then** each step's output is stored in a separate, clearly labeled location
2. **Given** debug mode is enabled and multiple pipeline runs occur, **When** viewing the output structure, **Then** outputs from different sessions are kept separate to avoid confusion

---

### User Story 3 - Output Format Consistency (Priority: P3)

As an ETL pipeline developer, I need the debug outputs in the same format as other stage outputs, so I can use the same tools and scripts to analyze them.

**Why this priority**: Format consistency is valuable for tooling and workflow integration, but the fundamental debugging capability works without it.

**Independent Test**: Can be tested by comparing debug output format with existing stage output format and verifying they match.

**Acceptance Scenarios**:

1. **Given** debug mode is enabled, **When** step outputs are written, **Then** they use the same file format (JSONL, JSON, or Markdown) as the final Transform stage output
2. **Given** debug mode is enabled, **When** step outputs contain metadata, **Then** the metadata structure matches the patterns used in other pipeline stages

---

### Edge Cases

- What happens when debug output directory already exists from a previous run?
  → **Resolution**: Overwrite files. Session path provides uniqueness.
- How does the system handle disk space issues when writing debug outputs?
  → **Resolution**: Let OS error propagate. Item marked as failed, pipeline continues with next item.
- What happens if a step produces no output (empty result)?
  → **Resolution**: Write JSONL file with empty metadata (status: "skipped", content: null).
- How are very large step outputs handled (e.g., thousands of records)?
  → **Resolution**: No truncation. Full content written per SC-002. Disk space is user's responsibility.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Transform stage MUST check if debug mode is enabled before each step execution
- **FR-002**: Transform stage MUST write step output to a dedicated location when debug mode is enabled
- **FR-003**: Transform stage MUST NOT write intermediate step outputs when debug mode is disabled
- **FR-004**: System MUST preserve the final Transform stage output location regardless of debug mode
- **FR-005**: Each debug step output MUST be identifiable by its step name or sequence number
- **FR-006**: Debug output location MUST be within the session structure to maintain ETL organization
- **FR-007**: System MUST continue to function normally when debug mode is disabled (no performance impact)
- **FR-008**: JSONL output MUST be written as one JSON object per line without line breaks within each JSON record (compact format)
- **FR-009**: When a step produces no transformable output, debug output MUST still be written with status "skipped" and null content fields

### Key Entities

- **Transform Stage**: Processing component that runs multiple sequential steps on extracted data
- **Debug Step Output**: Intermediate data produced by individual Transform steps, written only in debug mode
- **Debug Configuration**: Setting that controls whether step-by-step output is captured

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can identify which Transform step produces incorrect data within 2 minutes of enabling debug mode
- **SC-002**: Debug outputs contain 100% of the data that flows between Transform steps
- **SC-003**: Debug mode has zero impact on pipeline behavior when disabled (same final output)
- **SC-004**: Step outputs are organized such that developers spend less than 30 seconds locating a specific step's output

## Scope

### In Scope

- Writing intermediate step outputs during Transform stage execution
- Debug mode toggle mechanism
- Output organization within session structure
- Maintaining existing Transform stage behavior when debug disabled

### Out of Scope

- Debug output for Extract or Load stages (only Transform)
- Interactive debugging or breakpoints
- Automatic comparison of step outputs
- Debug output retention policies
- UI or visualization of debug outputs

## Dependencies

- Existing debug mode configuration mechanism (src/etl/core/config.py)
- Session folder structure (.staging/@session/YYYYMMDD_HHMMSS/)
- Transform stage base class (src/etl/core/stage.py)

## Assumptions

- Debug mode is controlled by a boolean flag accessible to Transform stage
- Transform stage already has a step-based processing structure
- File I/O for writing debug outputs is acceptable (no in-memory-only constraint)
- JSONL format is preferred for structured data outputs (consistent with current pipeline)
- Session folder structure already supports subdirectories for debug information
