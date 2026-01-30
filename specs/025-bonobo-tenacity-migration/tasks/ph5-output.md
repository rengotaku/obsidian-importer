# Phase 5: User Story 2 - Custom ETL Pipeline - Output

**Date**: 2026-01-19
**Status**: Complete

## Summary

Phase 5 implemented the custom ETL pipeline framework with BaseStage, BaseStep abstract classes and concrete Stage/Phase implementations for Import and Organize pipelines.

## Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| T051 | Read previous phase output: ph4-output.md | Done |
| T052 | Create test for Stage base class | Done |
| T053 | Create test for import Phase orchestration | Done |
| T054 | Create test for organize Phase orchestration | Done |
| T055 | Implement Stage abstract base class | Done |
| T056 | Implement ClaudeExtractor stage | Done |
| T057 | Implement FileExtractor stage | Done |
| T058 | Implement KnowledgeTransformer stage | Done |
| T059 | Implement NormalizerTransformer stage | Done |
| T060 | Implement SessionLoader stage | Done |
| T061 | Implement VaultLoader stage | Done |
| T062 | Implement ImportPhase orchestration | Done |
| T063 | Implement OrganizePhase orchestration | Done |
| T064 | Run make test | Done (all pass) |
| T065 | Generate phase output | Done |

## Artifacts Created

### Directory Structure Update

```
src/etl/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── status.py         # (from Phase 2)
│   ├── types.py          # (from Phase 2)
│   ├── models.py         # (from Phase 2)
│   ├── retry.py          # (from Phase 3)
│   ├── session.py        # (from Phase 4)
│   ├── phase.py          # (from Phase 4)
│   ├── stage.py          # UPDATED: + BaseStage, BaseStep, StageContext
│   ├── step.py           # (from Phase 4)
│   └── config.py         # (from Phase 4)
├── phases/
│   ├── __init__.py       # UPDATED: exports
│   ├── import_phase.py   # NEW: ImportPhase orchestration
│   └── organize_phase.py # NEW: OrganizePhase orchestration
├── stages/
│   ├── __init__.py       # UPDATED: exports
│   ├── extract/
│   │   ├── __init__.py           # UPDATED: exports
│   │   ├── claude_extractor.py   # NEW: ClaudeExtractor
│   │   └── file_extractor.py     # NEW: FileExtractor
│   ├── transform/
│   │   ├── __init__.py               # UPDATED: exports
│   │   ├── knowledge_transformer.py  # NEW: KnowledgeTransformer
│   │   └── normalizer_transformer.py # NEW: NormalizerTransformer
│   └── load/
│       ├── __init__.py       # UPDATED: exports
│       ├── session_loader.py # NEW: SessionLoader
│       └── vault_loader.py   # NEW: VaultLoader
└── tests/
    ├── __init__.py
    ├── test_models.py        # (from Phase 2)
    ├── test_retry.py         # (from Phase 3)
    ├── test_session.py       # (from Phase 4)
    ├── test_phase.py         # (from Phase 4)
    ├── test_stages.py        # NEW: BaseStage/BaseStep tests
    ├── test_import_phase.py  # NEW: ImportPhase tests
    └── test_organize_phase.py # NEW: OrganizePhase tests
```

### File Details

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `src/etl/core/stage.py` | Stage dataclass + Base classes | Stage, StageContext, BaseStep, BaseStage |
| `src/etl/stages/extract/claude_extractor.py` | Claude export extraction | ClaudeExtractor, ParseJsonStep, ValidateStructureStep |
| `src/etl/stages/extract/file_extractor.py` | Markdown file extraction | FileExtractor, ReadMarkdownStep, ParseFrontmatterStep |
| `src/etl/stages/transform/knowledge_transformer.py` | Knowledge extraction | KnowledgeTransformer, ExtractKnowledgeStep, GenerateMetadataStep, FormatMarkdownStep |
| `src/etl/stages/transform/normalizer_transformer.py` | Markdown normalization | NormalizerTransformer, ClassifyGenreStep, NormalizeFrontmatterStep, CleanContentStep |
| `src/etl/stages/load/session_loader.py` | Session output writing | SessionLoader, WriteToSessionStep, UpdateIndexStep |
| `src/etl/stages/load/vault_loader.py` | Vault organization | VaultLoader, DetermineVaultStep, MoveToVaultStep |
| `src/etl/phases/import_phase.py` | Import phase orchestration | ImportPhase, PhaseResult |
| `src/etl/phases/organize_phase.py` | Organize phase orchestration | OrganizePhase, PhaseResult |
| `src/etl/tests/test_stages.py` | Stage base class tests | 14 tests |
| `src/etl/tests/test_import_phase.py` | ImportPhase tests | 12 tests |
| `src/etl/tests/test_organize_phase.py` | OrganizePhase tests | 15 tests |

## Implementation Details

### Abstract Base Classes

```python
# BaseStep - smallest unit of processing
class BaseStep(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def process(self, item: ProcessingItem) -> ProcessingItem: ...

    def validate_input(self, item: ProcessingItem) -> bool:
        return True  # Override for custom validation

    def on_error(self, item: ProcessingItem, error: Exception) -> ProcessingItem | None:
        return None  # Override for fallback behavior


# BaseStage - container for steps
class BaseStage(ABC):
    @property
    @abstractmethod
    def stage_type(self) -> StageType: ...

    @property
    @abstractmethod
    def steps(self) -> list[BaseStep]: ...

    def run(self, ctx: StageContext, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]: ...
```

### Stage Context

```python
@dataclass
class StageContext:
    phase: Phase
    stage: Stage
    debug_mode: bool = False

    @property
    def input_path(self) -> Path: ...

    @property
    def output_path(self) -> Path: ...
```

### Phase Orchestration

```python
# ImportPhase: ClaudeExtractor -> KnowledgeTransformer -> SessionLoader
class ImportPhase:
    phase_type = PhaseType.IMPORT

    def create_extract_stage(self) -> ClaudeExtractor
    def create_transform_stage(self) -> KnowledgeTransformer
    def create_load_stage(self) -> SessionLoader
    def discover_items(input_path: Path) -> Iterator[ProcessingItem]
    def run(phase_data: Phase, debug_mode: bool) -> PhaseResult


# OrganizePhase: FileExtractor -> NormalizerTransformer -> VaultLoader
class OrganizePhase:
    phase_type = PhaseType.ORGANIZE

    def create_extract_stage(self) -> FileExtractor
    def create_transform_stage(self) -> NormalizerTransformer
    def create_load_stage(self) -> VaultLoader
    def discover_items(input_path: Path) -> Iterator[ProcessingItem]
    def run(phase_data: Phase, debug_mode: bool) -> PhaseResult
```

### Stage Implementations

| Stage | Type | Steps | Purpose |
|-------|------|-------|---------|
| ClaudeExtractor | EXTRACT | ParseJsonStep, ValidateStructureStep | Parse Claude export JSON |
| FileExtractor | EXTRACT | ReadMarkdownStep, ParseFrontmatterStep | Read Markdown files |
| KnowledgeTransformer | TRANSFORM | ExtractKnowledgeStep, GenerateMetadataStep, FormatMarkdownStep | Extract knowledge from conversations |
| NormalizerTransformer | TRANSFORM | ClassifyGenreStep, NormalizeFrontmatterStep, CleanContentStep | Normalize Markdown to Obsidian format |
| SessionLoader | LOAD | WriteToSessionStep, UpdateIndexStep | Write to session output folder |
| VaultLoader | LOAD | DetermineVaultStep, MoveToVaultStep | Move to appropriate Vault folder |

## Test Results

- **New Tests**: 41 tests (14 stages + 12 import + 15 organize)
- **Total ETL Tests**: 130 tests
- **All Tests**: Pass

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| test_stages.py | 14 | Pass |
| test_import_phase.py | 12 | Pass |
| test_organize_phase.py | 15 | Pass |
| **Total New** | **41** | **All Pass** |

### Test Class Summary

**test_stages.py:**
- TestBaseStageAbstract: 3 tests
- TestBaseStageImplementation: 3 tests
- TestStageContext: 2 tests
- TestBaseStep: 4 tests
- TestStageWithMultipleSteps: 1 test
- TestStageErrorHandling: 2 tests

**test_import_phase.py:**
- TestImportPhaseCreation: 2 tests
- TestImportPhaseStages: 3 tests
- TestImportPhaseDiscoverItems: 3 tests
- TestImportPhaseRun: 2 tests
- TestImportPhaseETLFlow: 1 test
- TestImportPhaseDebugMode: 1 test

**test_organize_phase.py:**
- TestOrganizePhaseCreation: 2 tests
- TestOrganizePhaseStages: 3 tests
- TestOrganizePhaseDiscoverItems: 4 tests
- TestOrganizePhaseRun: 2 tests
- TestOrganizePhaseETLFlow: 2 tests
- TestOrganizePhaseVaultMapping: 1 test
- TestOrganizePhaseDebugMode: 1 test

## Dependencies Verified

| Dependency | Version | Status |
|------------|---------|--------|
| tenacity | 9.1.2 | Used (from Phase 3) |
| Python | 3.13 | Verified |

## Next Phase

**Phase 6: CLI Implementation**

Key files to create:
- `src/etl/cli.py` - CLI entry point with argparse
- `src/etl/__main__.py` - Module entry point
- `src/etl/tests/test_cli.py` - CLI tests

Commands to implement:
- `import` - Run ImportPhase
- `organize` - Run OrganizePhase
- `status` - Show session status
- `retry` - Retry failed items
- `clean` - Clean old sessions

## Import Path Examples

```python
# Stage base classes
from src.etl.core.stage import BaseStage, BaseStep, StageContext, Stage

# Extract stages
from src.etl.stages.extract.claude_extractor import ClaudeExtractor
from src.etl.stages.extract.file_extractor import FileExtractor

# Transform stages
from src.etl.stages.transform.knowledge_transformer import KnowledgeTransformer
from src.etl.stages.transform.normalizer_transformer import NormalizerTransformer

# Load stages
from src.etl.stages.load.session_loader import SessionLoader
from src.etl.stages.load.vault_loader import VaultLoader

# Phase orchestration
from src.etl.phases.import_phase import ImportPhase
from src.etl.phases.organize_phase import OrganizePhase
```

## Checkpoint Validation

Custom ETL pipeline is operational:

1. BaseStep abstract class with name, process, validate_input, on_error
2. BaseStage abstract class with stage_type, steps, run method
3. StageContext provides phase, stage, debug_mode, and paths
4. Six Stage implementations covering Extract, Transform, Load
5. ImportPhase orchestrates ClaudeExtractor -> KnowledgeTransformer -> SessionLoader
6. OrganizePhase orchestrates FileExtractor -> NormalizerTransformer -> VaultLoader
7. Item discovery (JSON for import, Markdown for organize)
8. Full ETL flow tested with single items

## Implementation Notes

### Stub Implementations

Some Steps are stub implementations that will be enhanced later:

- **ExtractKnowledgeStep**: Passes content through (full impl will use Ollama)
- **ClassifyGenreStep**: Simple keyword matching (full impl will use Ollama)

### Genre Classification

Current keyword-based classification:

| Genre | Keywords |
|-------|----------|
| engineer | python, code, programming, api, database, etc. |
| business | meeting, project, strategy, management, etc. |
| economy | market, stock, investment, economic, etc. |
| daily | today, personal, diary, memo, etc. |
| other | (default) |

### Vault Mapping

Default mapping:

```python
GENRE_VAULT_MAP = {
    "engineer": "Vaults/engineer",
    "business": "Vaults/business",
    "economy": "Vaults/economy",
    "daily": "Vaults/daily",
    "other": "Vaults/other",
}
```

## Usage Example

```python
from pathlib import Path
from src.etl.core.session import SessionManager
from src.etl.core.phase import PhaseManager
from src.etl.core.types import PhaseType
from src.etl.phases.import_phase import ImportPhase

# Create session
session_manager = SessionManager(Path(".staging/@session"))
session = session_manager.create(debug_mode=True)
session_manager.save(session)

# Create phase with folder structure
phase_manager = PhaseManager(session.base_path)
phase_data = phase_manager.create(PhaseType.IMPORT)

# Copy input files to extract/input/
# ...

# Run import phase
import_phase = ImportPhase()
result = import_phase.run(phase_data, debug_mode=True)

print(f"Status: {result.status}")
print(f"Processed: {result.items_processed}")
print(f"Failed: {result.items_failed}")
```
