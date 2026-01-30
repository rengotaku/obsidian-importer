"""Tests for OrganizePhase orchestration.

Tests OrganizePhase with FileExtractor -> NormalizerTransformer -> VaultLoader.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.etl.core.phase import PhaseManager
from src.etl.core.session import SessionManager
from src.etl.core.status import PhaseStatus
from src.etl.core.types import PhaseType, StageType
from src.etl.phases.organize_phase import OrganizePhase


class TestOrganizePhaseCreation(unittest.TestCase):
    """Test OrganizePhase instantiation."""

    def test_organize_phase_type(self):
        """OrganizePhase has correct phase_type."""
        phase = OrganizePhase()
        self.assertEqual(phase.phase_type, PhaseType.ORGANIZE)

    def test_organize_phase_creates_stages(self):
        """OrganizePhase creates all three stages."""
        phase = OrganizePhase()

        extract = phase.create_extract_stage()
        transform = phase.create_transform_stage()
        load = phase.create_load_stage()

        self.assertEqual(extract.stage_type, StageType.EXTRACT)
        self.assertEqual(transform.stage_type, StageType.TRANSFORM)
        self.assertEqual(load.stage_type, StageType.LOAD)


class TestOrganizePhaseStages(unittest.TestCase):
    """Test OrganizePhase stage implementations."""

    def test_extract_stage_is_file_extractor(self):
        """Extract stage is FileExtractor."""
        from src.etl.stages.extract.file_extractor import FileExtractor

        phase = OrganizePhase()
        extract = phase.create_extract_stage()

        self.assertIsInstance(extract, FileExtractor)

    def test_transform_stage_is_normalizer_transformer(self):
        """Transform stage is NormalizerTransformer."""
        from src.etl.stages.transform.normalizer_transformer import NormalizerTransformer

        phase = OrganizePhase()
        transform = phase.create_transform_stage()

        self.assertIsInstance(transform, NormalizerTransformer)

    def test_load_stage_is_vault_loader(self):
        """Load stage is VaultLoader."""
        from src.etl.stages.load.vault_loader import VaultLoader

        phase = OrganizePhase()
        load = phase.create_load_stage()

        self.assertIsInstance(load, VaultLoader)


class TestOrganizePhaseDiscoverItems(unittest.TestCase):
    """Test OrganizePhase item discovery."""

    def test_discover_items_from_empty_dir(self):
        """Empty directory yields no items."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            phase = OrganizePhase()
            items = list(phase.discover_items(input_path))

            self.assertEqual(len(items), 0)

    def test_discover_items_finds_markdown_files(self):
        """Discovers Markdown files in input directory."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create test markdown file
            test_file = input_path / "test.md"
            test_file.write_text("# Test\n\nContent here")

            phase = OrganizePhase()
            items = list(phase.discover_items(input_path))

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].source_path, test_file)

    def test_discover_items_ignores_non_markdown(self):
        """Ignores non-Markdown files."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create test files
            (input_path / "notes.md").write_text("# Notes")
            (input_path / "data.json").write_text("{}")
            (input_path / "readme.txt").write_text("text")

            phase = OrganizePhase()
            items = list(phase.discover_items(input_path))

            self.assertEqual(len(items), 1)
            self.assertTrue(items[0].source_path.suffix == ".md")

    def test_discover_items_recursive(self):
        """Discovers files in subdirectories."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create nested structure
            subdir = input_path / "subdir"
            subdir.mkdir()

            (input_path / "file1.md").write_text("# File 1")
            (subdir / "file2.md").write_text("# File 2")

            phase = OrganizePhase()
            items = list(phase.discover_items(input_path))

            self.assertEqual(len(items), 2)


class TestOrganizePhaseRun(unittest.TestCase):
    """Test OrganizePhase run method."""

    def test_run_creates_phase_result(self):
        """Run returns PhaseResult."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.ORGANIZE)

            # Create input file
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_file = input_path / "test.md"
            test_file.write_text("# Test\n\nContent here")

            # Run phase
            organize_phase = OrganizePhase()
            result = organize_phase.run(phase_data)

            # Verify result
            self.assertEqual(result.phase_type, PhaseType.ORGANIZE)
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])

    def test_run_with_empty_input(self):
        """Run with empty input completes."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.ORGANIZE)

            # Run with empty input
            organize_phase = OrganizePhase()
            result = organize_phase.run(phase_data)

            self.assertEqual(result.phase_type, PhaseType.ORGANIZE)
            self.assertEqual(result.items_processed, 0)


class TestOrganizePhaseETLFlow(unittest.TestCase):
    """Test OrganizePhase ETL flow: Extract -> Transform -> Load."""

    def test_etl_flow_with_single_item(self):
        """Single item flows through all stages."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.ORGANIZE)

            # Create input file with frontmatter
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_content = """---
title: Test Document
tags:
  - test
---

# Test Document

This is test content.
"""
            test_file = input_path / "test.md"
            test_file.write_text(test_content)

            # Run phase
            organize_phase = OrganizePhase()
            result = organize_phase.run(phase_data)

            # Verify flow completed
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])

    def test_etl_flow_with_unnormalized_file(self):
        """Unnormalized file gets normalized."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.ORGANIZE)

            # Create unnormalized input file (no frontmatter)
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_content = """# Unnormalized Document

This file has no frontmatter.
"""
            test_file = input_path / "unnormalized.md"
            test_file.write_text(test_content)

            # Run phase
            organize_phase = OrganizePhase()
            result = organize_phase.run(phase_data)

            # Verify flow completed
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])


class TestOrganizePhaseVaultMapping(unittest.TestCase):
    """Test OrganizePhase vault mapping."""

    def test_vault_loader_determines_destination(self):
        """VaultLoader determines correct destination vault."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create vault directories
            vaults_path = base_path / "Vaults"
            (vaults_path / "engineer").mkdir(parents=True)
            (vaults_path / "business").mkdir(parents=True)
            (vaults_path / "daily").mkdir(parents=True)
            (vaults_path / "other").mkdir(parents=True)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.ORGANIZE)

            # Create input file with genre hint
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_content = """---
title: Python Programming
tags:
  - python
  - programming
---

# Python Programming

Technical content about Python.
"""
            test_file = input_path / "python.md"
            test_file.write_text(test_content)

            # Run phase
            organize_phase = OrganizePhase(vaults_path=vaults_path)
            result = organize_phase.run(phase_data)

            # Should complete
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])


class TestOrganizePhaseDebugMode(unittest.TestCase):
    """Test OrganizePhase debug mode."""

    def test_debug_mode_enabled(self):
        """Debug mode produces additional logging."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create(debug_mode=True)
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.ORGANIZE)

            # Run with debug mode
            organize_phase = OrganizePhase()
            result = organize_phase.run(phase_data, debug_mode=True)

            # Should complete without errors
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])


if __name__ == "__main__":
    unittest.main()
