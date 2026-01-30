"""Tests for Session management.

Tests for:
- Session creation
- Session ID format (YYYYMMDD_HHMMSS)
- SessionManager (create, load, save)
- session.json serialization
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


class TestSessionCreation(unittest.TestCase):
    """Test Session dataclass creation."""

    def test_session_creation_with_defaults(self):
        """Session can be created with minimal arguments."""
        from src.etl.core.session import Session
        from src.etl.core.status import SessionStatus

        session = Session(
            session_id="20260119_143052",
            base_path=Path("/tmp/test"),
        )

        self.assertEqual(session.session_id, "20260119_143052")
        self.assertEqual(session.status, SessionStatus.PENDING)
        self.assertFalse(session.debug_mode)
        self.assertEqual(session.phases, {})  # Now dict by default

    def test_session_creation_with_all_fields(self):
        """Session can be created with all fields specified."""
        from src.etl.core.session import PhaseStats, Session
        from src.etl.core.status import SessionStatus

        created = datetime(2026, 1, 19, 14, 30, 52)
        stats = PhaseStats(
            status="completed",
            success_count=10,
            error_count=0,
            completed_at=created.isoformat(),
        )
        session = Session(
            session_id="20260119_143052",
            created_at=created,
            status=SessionStatus.RUNNING,
            phases={"import": stats},
            debug_mode=True,
            base_path=Path("/tmp/test"),
        )

        self.assertEqual(session.session_id, "20260119_143052")
        self.assertEqual(session.created_at, created)
        self.assertEqual(session.status, SessionStatus.RUNNING)
        self.assertIn("import", session.phases)
        self.assertTrue(session.debug_mode)

    def test_session_base_path_is_path_object(self):
        """Session base_path should be a Path object."""
        from src.etl.core.session import Session

        session = Session(
            session_id="20260119_143052",
            base_path=Path("/tmp/test/20260119_143052"),
        )

        self.assertIsInstance(session.base_path, Path)


class TestSessionIdFormat(unittest.TestCase):
    """Test Session ID format validation."""

    def test_generate_session_id_format(self):
        """Generated session_id follows YYYYMMDD_HHMMSS format."""
        from src.etl.core.session import generate_session_id

        session_id = generate_session_id()

        # Format: YYYYMMDD_HHMMSS
        pattern = r"^\d{8}_\d{6}$"
        self.assertRegex(session_id, pattern)

    def test_generate_session_id_contains_valid_date(self):
        """Generated session_id contains a valid datetime."""
        from src.etl.core.session import generate_session_id

        session_id = generate_session_id()

        # Should be parseable as datetime
        dt = datetime.strptime(session_id, "%Y%m%d_%H%M%S")
        self.assertIsInstance(dt, datetime)

    def test_validate_session_id_valid(self):
        """validate_session_id returns True for valid format."""
        from src.etl.core.session import validate_session_id

        self.assertTrue(validate_session_id("20260119_143052"))
        self.assertTrue(validate_session_id("20251231_235959"))

    def test_validate_session_id_invalid(self):
        """validate_session_id returns False for invalid formats."""
        from src.etl.core.session import validate_session_id

        # Invalid formats
        self.assertFalse(validate_session_id("2026-01-19_143052"))
        self.assertFalse(validate_session_id("20260119-143052"))
        self.assertFalse(validate_session_id("2026011914305"))  # Too short
        self.assertFalse(validate_session_id("202601191430521"))  # Too long
        self.assertFalse(validate_session_id(""))

    def test_validate_session_id_invalid_datetime(self):
        """validate_session_id returns False for invalid datetime values."""
        from src.etl.core.session import validate_session_id

        # Invalid month (13)
        self.assertFalse(validate_session_id("20261319_143052"))
        # Invalid day (32)
        self.assertFalse(validate_session_id("20260132_143052"))
        # Invalid hour (25)
        self.assertFalse(validate_session_id("20260119_253052"))


class TestSessionManager(unittest.TestCase):
    """Test SessionManager operations."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_session_manager_create(self):
        """SessionManager.create() creates a new session with folder."""
        from src.etl.core.session import SessionManager
        from src.etl.core.status import SessionStatus

        manager = SessionManager(base_dir=self.session_dir)
        session = manager.create()

        # Session object is created
        self.assertIsNotNone(session)
        self.assertEqual(session.status, SessionStatus.PENDING)

        # Session folder is created
        self.assertTrue(session.base_path.exists())
        self.assertTrue(session.base_path.is_dir())

    def test_session_manager_create_with_debug(self):
        """SessionManager.create() respects debug_mode."""
        from src.etl.core.session import SessionManager

        manager = SessionManager(base_dir=self.session_dir)
        session = manager.create(debug_mode=True)

        self.assertTrue(session.debug_mode)

    def test_session_manager_save(self):
        """SessionManager.save() writes session.json."""
        from src.etl.core.session import PhaseStats, SessionManager
        from src.etl.core.status import SessionStatus

        manager = SessionManager(base_dir=self.session_dir)
        session = manager.create()
        session.status = SessionStatus.RUNNING
        stats = PhaseStats(
            status="completed",
            success_count=5,
            error_count=0,
            completed_at="2026-01-24T12:00:00",
        )
        session.phases = {"import": stats}

        manager.save(session)

        # session.json is written
        session_file = session.base_path / "session.json"
        self.assertTrue(session_file.exists())

        # Content is valid JSON
        with open(session_file) as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], session.session_id)
        self.assertEqual(data["status"], "running")
        self.assertIn("import", data["phases"])
        self.assertEqual(data["phases"]["import"]["success_count"], 5)

    def test_session_manager_load(self):
        """SessionManager.load() reads session from session.json."""
        from src.etl.core.session import PhaseStats, SessionManager
        from src.etl.core.status import SessionStatus

        manager = SessionManager(base_dir=self.session_dir)

        # Create and save a session
        original = manager.create()
        original.status = SessionStatus.COMPLETED
        stats1 = PhaseStats(
            status="completed",
            success_count=10,
            error_count=0,
            completed_at="2026-01-24T12:00:00",
        )
        stats2 = PhaseStats(
            status="completed",
            success_count=5,
            error_count=1,
            completed_at="2026-01-24T12:10:00",
        )
        original.phases = {"import": stats1, "organize": stats2}
        manager.save(original)

        # Load the session
        loaded = manager.load(original.session_id)

        self.assertEqual(loaded.session_id, original.session_id)
        self.assertEqual(loaded.status, SessionStatus.COMPLETED)
        self.assertIn("import", loaded.phases)
        self.assertIn("organize", loaded.phases)
        self.assertEqual(loaded.phases["import"].success_count, 10)
        self.assertEqual(loaded.phases["organize"].error_count, 1)

    def test_session_manager_load_nonexistent(self):
        """SessionManager.load() raises error for nonexistent session."""
        from src.etl.core.session import SessionManager

        manager = SessionManager(base_dir=self.session_dir)

        with self.assertRaises(FileNotFoundError):
            manager.load("99991231_235959")

    def test_session_manager_list_sessions(self):
        """SessionManager.list_sessions() returns all session IDs."""
        from src.etl.core.session import SessionManager

        manager = SessionManager(base_dir=self.session_dir)

        # Create multiple sessions
        s1 = manager.create()
        manager.save(s1)
        s2 = manager.create()
        manager.save(s2)

        sessions = manager.list_sessions()

        self.assertIn(s1.session_id, sessions)
        self.assertIn(s2.session_id, sessions)


class TestSessionJsonSerialization(unittest.TestCase):
    """Test session.json serialization format."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_session_to_dict(self):
        """Session.to_dict() returns correct dictionary."""
        from src.etl.core.session import PhaseStats, Session
        from src.etl.core.status import SessionStatus

        created = datetime(2026, 1, 19, 14, 30, 52)
        stats = PhaseStats(
            status="completed",
            success_count=15,
            error_count=0,
            completed_at="2026-01-19T14:30:52",
        )
        session = Session(
            session_id="20260119_143052",
            created_at=created,
            status=SessionStatus.RUNNING,
            phases={"import": stats},
            debug_mode=True,
            base_path=Path("/tmp/test"),
        )

        d = session.to_dict()

        self.assertEqual(d["session_id"], "20260119_143052")
        self.assertEqual(d["created_at"], "2026-01-19T14:30:52")
        self.assertEqual(d["status"], "running")
        self.assertIn("import", d["phases"])
        self.assertEqual(d["phases"]["import"]["success_count"], 15)
        self.assertTrue(d["debug_mode"])

    def test_session_from_dict(self):
        """Session.from_dict() creates Session from dictionary (new format)."""
        from src.etl.core.session import Session
        from src.etl.core.status import SessionStatus

        data = {
            "session_id": "20260119_143052",
            "created_at": "2026-01-19T14:30:52",
            "status": "running",
            "phases": {
                "import": {
                    "status": "completed",
                    "success_count": 20,
                    "error_count": 1,
                    "completed_at": "2026-01-19T14:30:52",
                }
            },
            "debug_mode": True,
        }

        session = Session.from_dict(data, base_path=Path("/tmp/test"))

        self.assertEqual(session.session_id, "20260119_143052")
        self.assertEqual(session.created_at, datetime(2026, 1, 19, 14, 30, 52))
        self.assertEqual(session.status, SessionStatus.RUNNING)
        self.assertIn("import", session.phases)
        self.assertEqual(session.phases["import"].success_count, 20)
        self.assertTrue(session.debug_mode)

    def test_session_json_roundtrip(self):
        """Session serialization/deserialization is lossless."""
        from src.etl.core.session import PhaseStats, SessionManager
        from src.etl.core.status import SessionStatus

        manager = SessionManager(base_dir=self.session_dir)
        original = manager.create(debug_mode=True)
        original.status = SessionStatus.PARTIAL
        stats1 = PhaseStats(
            status="completed",
            success_count=8,
            error_count=0,
            completed_at="2026-01-24T12:00:00",
        )
        stats2 = PhaseStats(
            status="partial",
            success_count=3,
            error_count=2,
            completed_at="2026-01-24T12:15:00",
        )
        original.phases = {"import": stats1, "organize": stats2}
        manager.save(original)

        loaded = manager.load(original.session_id)

        self.assertEqual(loaded.session_id, original.session_id)
        self.assertEqual(loaded.status, original.status)
        self.assertIn("import", loaded.phases)
        self.assertIn("organize", loaded.phases)
        self.assertEqual(loaded.phases["import"].success_count, 8)
        self.assertEqual(loaded.phases["organize"].success_count, 3)
        self.assertEqual(loaded.debug_mode, original.debug_mode)


class TestPhaseStats(unittest.TestCase):
    """Test PhaseStats dataclass (T015)."""

    def test_phase_stats_creation(self):
        """PhaseStats can be created with all fields."""
        from src.etl.core.session import PhaseStats

        stats = PhaseStats(
            status="completed",
            success_count=42,
            error_count=3,
            completed_at="2026-01-24T12:05:30",
        )

        self.assertEqual(stats.status, "completed")
        self.assertEqual(stats.success_count, 42)
        self.assertEqual(stats.error_count, 3)
        self.assertEqual(stats.completed_at, "2026-01-24T12:05:30")
        self.assertIsNone(stats.error)

    def test_phase_stats_with_error(self):
        """PhaseStats can include error message."""
        from src.etl.core.session import PhaseStats

        stats = PhaseStats(
            status="crashed",
            success_count=0,
            error_count=0,
            completed_at="2026-01-24T12:03:15",
            error="Connection refused to Ollama API",
        )

        self.assertEqual(stats.status, "crashed")
        self.assertEqual(stats.error, "Connection refused to Ollama API")

    def test_phase_stats_to_dict(self):
        """PhaseStats.to_dict() serializes correctly."""
        from src.etl.core.session import PhaseStats

        stats = PhaseStats(
            status="partial",
            success_count=10,
            error_count=2,
            completed_at="2026-01-24T12:10:00",
        )

        d = stats.to_dict()

        self.assertEqual(d["status"], "partial")
        self.assertEqual(d["success_count"], 10)
        self.assertEqual(d["error_count"], 2)
        self.assertEqual(d["completed_at"], "2026-01-24T12:10:00")
        self.assertNotIn("error", d)  # None should be excluded

    def test_phase_stats_to_dict_with_error(self):
        """PhaseStats.to_dict() includes error if set."""
        from src.etl.core.session import PhaseStats

        stats = PhaseStats(
            status="failed",
            success_count=0,
            error_count=5,
            completed_at="2026-01-24T12:15:00",
            error="Disk full",
        )

        d = stats.to_dict()

        self.assertIn("error", d)
        self.assertEqual(d["error"], "Disk full")

    def test_phase_stats_from_dict(self):
        """PhaseStats.from_dict() deserializes correctly."""
        from src.etl.core.session import PhaseStats

        data = {
            "status": "completed",
            "success_count": 100,
            "error_count": 0,
            "completed_at": "2026-01-24T13:00:00",
        }

        stats = PhaseStats.from_dict(data)

        self.assertEqual(stats.status, "completed")
        self.assertEqual(stats.success_count, 100)
        self.assertEqual(stats.error_count, 0)
        self.assertEqual(stats.completed_at, "2026-01-24T13:00:00")
        self.assertIsNone(stats.error)


class TestSessionPhasesDictFormat(unittest.TestCase):
    """Test Session with dict-based phases format (T016)."""

    def test_session_phases_dict_format(self):
        """Session.phases can be dict of PhaseStats."""
        from src.etl.core.session import PhaseStats, Session

        stats = PhaseStats(
            status="completed",
            success_count=42,
            error_count=3,
            completed_at="2026-01-24T12:05:30",
        )
        session = Session(
            session_id="20260124_120000",
            base_path=Path("/tmp/test"),
            phases={"import": stats},
        )

        self.assertIsInstance(session.phases, dict)
        self.assertIn("import", session.phases)
        self.assertEqual(session.phases["import"].success_count, 42)

    def test_session_to_dict_with_phases_dict(self):
        """Session.to_dict() serializes phases as dict."""
        from src.etl.core.session import PhaseStats, Session

        stats = PhaseStats(
            status="completed",
            success_count=42,
            error_count=3,
            completed_at="2026-01-24T12:05:30",
        )
        session = Session(
            session_id="20260124_120000",
            base_path=Path("/tmp/test"),
            phases={"import": stats},
        )

        d = session.to_dict()

        self.assertIsInstance(d["phases"], dict)
        self.assertIn("import", d["phases"])
        self.assertEqual(d["phases"]["import"]["success_count"], 42)
        self.assertEqual(d["phases"]["import"]["status"], "completed")


class TestSessionBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with old list-based phases format (T017)."""

    def test_session_from_dict_old_list_format(self):
        """Session.from_dict() handles old list format."""
        from src.etl.core.session import Session

        data = {
            "session_id": "20260124_120000",
            "created_at": "2026-01-24T12:00:00",
            "status": "completed",
            "phases": ["import", "organize"],  # Old format: list
            "debug_mode": True,
        }

        session = Session.from_dict(data, base_path=Path("/tmp/test"))

        # Converted to dict format with default stats
        self.assertIsInstance(session.phases, dict)
        self.assertIn("import", session.phases)
        self.assertIn("organize", session.phases)
        self.assertEqual(session.phases["import"].status, "completed")
        self.assertEqual(session.phases["import"].success_count, 0)
        self.assertEqual(session.phases["import"].error_count, 0)

    def test_session_from_dict_new_dict_format(self):
        """Session.from_dict() handles new dict format."""
        from src.etl.core.session import Session

        data = {
            "session_id": "20260124_120000",
            "created_at": "2026-01-24T12:00:00",
            "status": "completed",
            "phases": {
                "import": {
                    "status": "completed",
                    "success_count": 42,
                    "error_count": 3,
                    "completed_at": "2026-01-24T12:05:30",
                }
            },
            "debug_mode": True,
        }

        session = Session.from_dict(data, base_path=Path("/tmp/test"))

        self.assertIsInstance(session.phases, dict)
        self.assertEqual(session.phases["import"].success_count, 42)
        self.assertEqual(session.phases["import"].error_count, 3)


class TestSessionJsonPhasesFormat(unittest.TestCase):
    """Test session.json phases format after CLI execution (T063)."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_session_json_phases_format(self):
        """session.json contains phases as dict with PhaseStats."""
        from src.etl.core.session import PhaseStats, SessionManager

        # Create session with phase stats
        session_dir = self.test_dir / "sessions"
        manager = SessionManager(session_dir)
        session = manager.create()

        stats = PhaseStats(
            status="completed",
            success_count=15,
            error_count=2,
            completed_at="2026-01-24T14:30:00",
        )
        session.phases["import"] = stats
        manager.save(session)

        # Load raw session.json and check format
        session_file = session.base_path / "session.json"
        with open(session_file, encoding="utf-8") as f:
            data = json.load(f)

        # Phases should be a dict
        self.assertIsInstance(data["phases"], dict)
        self.assertIn("import", data["phases"])

        # Each phase should have PhaseStats fields
        import_stats = data["phases"]["import"]
        self.assertEqual(import_stats["status"], "completed")
        self.assertEqual(import_stats["success_count"], 15)
        self.assertEqual(import_stats["error_count"], 2)
        self.assertEqual(import_stats["completed_at"], "2026-01-24T14:30:00")
        self.assertNotIn("error", import_stats)  # None should be excluded

    def test_session_json_crashed_phase_format(self):
        """session.json records crashed phase with error field."""
        from src.etl.core.session import PhaseStats, SessionManager

        # Create session with crashed phase
        session_dir = self.test_dir / "sessions"
        manager = SessionManager(session_dir)
        session = manager.create()

        stats = PhaseStats(
            status="crashed",
            success_count=0,
            error_count=0,
            completed_at="2026-01-24T14:35:00",
            error="RuntimeError: Simulated crash",
        )
        session.phases["import"] = stats
        manager.save(session)

        # Load raw session.json and check error field
        session_file = session.base_path / "session.json"
        with open(session_file, encoding="utf-8") as f:
            data = json.load(f)

        import_stats = data["phases"]["import"]
        self.assertEqual(import_stats["status"], "crashed")
        self.assertIn("error", import_stats)
        self.assertEqual(import_stats["error"], "RuntimeError: Simulated crash")


class TestSessionProvider(unittest.TestCase):
    """Test Session provider field for Resume mode."""

    def test_session_provider_field_default(self):
        """Session.provider defaults to None."""
        from src.etl.core.session import Session

        session = Session(
            session_id="20260128_092507",
            base_path=Path("/tmp/test"),
        )

        self.assertIsNone(session.provider)

    def test_session_provider_field_set(self):
        """Session.provider can be set to 'claude', 'openai', or 'github'."""
        from src.etl.core.session import Session

        for provider in ["claude", "openai", "github"]:
            session = Session(
                session_id="20260128_092507",
                base_path=Path("/tmp/test"),
                provider=provider,
            )
            self.assertEqual(session.provider, provider)

    def test_session_to_dict_with_provider(self):
        """Session.to_dict() includes provider field."""
        from src.etl.core.session import Session

        session = Session(
            session_id="20260128_092507",
            base_path=Path("/tmp/test"),
            provider="claude",
        )

        d = session.to_dict()

        self.assertIn("provider", d)
        self.assertEqual(d["provider"], "claude")

    def test_session_to_dict_without_provider(self):
        """Session.to_dict() excludes provider if None."""
        from src.etl.core.session import Session

        session = Session(
            session_id="20260128_092507",
            base_path=Path("/tmp/test"),
        )

        d = session.to_dict()

        self.assertNotIn("provider", d)

    def test_session_from_dict_with_provider(self):
        """Session.from_dict() loads provider field."""
        from src.etl.core.session import Session

        data = {
            "session_id": "20260128_092507",
            "created_at": "2026-01-28T09:25:07",
            "status": "pending",
            "phases": {},
            "debug_mode": True,
            "provider": "openai",
        }

        session = Session.from_dict(data, base_path=Path("/tmp/test"))

        self.assertEqual(session.provider, "openai")

    def test_session_from_dict_without_provider_backward_compat(self):
        """Session.from_dict() defaults provider to None if not present (backward compat)."""
        from src.etl.core.session import Session

        data = {
            "session_id": "20260128_092507",
            "created_at": "2026-01-28T09:25:07",
            "status": "pending",
            "phases": {},
            "debug_mode": True,
        }

        session = Session.from_dict(data, base_path=Path("/tmp/test"))

        self.assertIsNone(session.provider)

    def test_session_manager_roundtrip_with_provider(self):
        """SessionManager can save and load provider field."""
        from src.etl.core.session import SessionManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SessionManager(base_dir=Path(temp_dir))

            # Create session with provider
            original = manager.create(debug_mode=True)
            original.provider = "github"
            manager.save(original)

            # Load and verify
            loaded = manager.load(original.session_id)
            self.assertEqual(loaded.provider, "github")

    def test_session_json_includes_provider(self):
        """session.json file includes provider field."""
        from src.etl.core.session import SessionManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SessionManager(base_dir=Path(temp_dir))

            # Create session with provider
            session = manager.create(debug_mode=True)
            session.provider = "claude"
            manager.save(session)

            # Read raw JSON and verify
            session_file = session.base_path / "session.json"
            with open(session_file, encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("provider", data)
            self.assertEqual(data["provider"], "claude")


if __name__ == "__main__":
    unittest.main()
