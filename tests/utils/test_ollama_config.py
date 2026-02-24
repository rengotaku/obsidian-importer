"""Tests for ollama_config module.

Phase 2 RED tests: OllamaConfig dataclass, get_ollama_config function.
These tests verify:
- get_ollama_config returns correct config for each function
- Function-specific overrides take precedence over defaults
- Defaults are applied when function-specific config is missing
"""

from __future__ import annotations

import unittest


class TestOllamaConfigDataclass(unittest.TestCase):
    """OllamaConfig: dataclass with correct fields and defaults."""

    def test_ollama_config_has_all_fields(self):
        """OllamaConfig が必要なフィールドをすべて持つこと。

        FR-002: システムは各関数で以下のパラメーターを設定可能にしなければならない
        - model, base_url, timeout, temperature, num_predict
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig

        config = OllamaConfig(
            model="gemma3:12b",
            base_url="http://localhost:11434",
            timeout=120,
            temperature=0.2,
            num_predict=-1,
        )

        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.timeout, 120)
        self.assertAlmostEqual(config.temperature, 0.2, places=2)
        self.assertEqual(config.num_predict, -1)

    def test_ollama_config_is_dataclass(self):
        """OllamaConfig が dataclass であること。"""
        from dataclasses import is_dataclass

        from obsidian_etl.utils.ollama_config import OllamaConfig

        self.assertTrue(is_dataclass(OllamaConfig))

    def test_ollama_config_defaults(self):
        """OllamaConfig のデフォルト値が正しいこと。

        Default values from data-model.md:
        - model: no default (required)
        - base_url: "http://localhost:11434"
        - timeout: 120
        - temperature: 0.2
        - num_predict: -1
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig

        config = OllamaConfig(model="gemma3:12b")

        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.timeout, 120)
        self.assertAlmostEqual(config.temperature, 0.2, places=2)
        self.assertEqual(config.num_predict, -1)


class TestGetConfigExtractKnowledge(unittest.TestCase):
    """get_ollama_config: extract_knowledge function configuration."""

    def test_get_config_extract_knowledge(self):
        """extract_knowledge 関数用の設定が正しく返されること。

        US1 - Acceptance Scenario 1:
        Given: parameters.yml に ollama.functions.extract_knowledge セクションが設定されている
        When: get_ollama_config(params, "extract_knowledge") が呼ばれる
        Then: 該当セクションのパラメーターが使用される

        Expected from contracts/parameters.yml:
        - num_predict: 16384
        - timeout: 300
        - Other values from defaults
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "extract_knowledge": {
                        "num_predict": 16384,
                        "timeout": 300,
                    },
                },
            }
        }

        config = get_ollama_config(params, "extract_knowledge")

        # Should be OllamaConfig instance
        self.assertIsInstance(config, OllamaConfig)

        # extract_knowledge overrides should be applied
        self.assertEqual(config.num_predict, 16384)
        self.assertEqual(config.timeout, 300)

        # Defaults should be applied for non-overridden fields
        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertAlmostEqual(config.temperature, 0.2, places=2)


class TestGetConfigTranslateSummary(unittest.TestCase):
    """get_ollama_config: translate_summary function configuration."""

    def test_get_config_translate_summary(self):
        """translate_summary 関数用の設定が正しく返されること。

        US1 - Acceptance Scenario 2:
        Given: parameters.yml に ollama.functions.translate_summary セクションが設定されている
        When: get_ollama_config(params, "translate_summary") が呼ばれる
        Then: 該当セクションのパラメーターが使用される

        Expected from contracts/parameters.yml:
        - num_predict: 1024
        - Other values from defaults
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "translate_summary": {
                        "num_predict": 1024,
                    },
                },
            }
        }

        config = get_ollama_config(params, "translate_summary")

        # Should be OllamaConfig instance
        self.assertIsInstance(config, OllamaConfig)

        # translate_summary override should be applied
        self.assertEqual(config.num_predict, 1024)

        # Defaults should be applied for non-overridden fields
        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.timeout, 120)
        self.assertAlmostEqual(config.temperature, 0.2, places=2)


class TestGetConfigExtractTopic(unittest.TestCase):
    """get_ollama_config: extract_topic function configuration."""

    def test_get_config_extract_topic(self):
        """extract_topic 関数用の設定が正しく返されること。

        US1 - Acceptance Scenario 3:
        Given: parameters.yml に ollama.functions.extract_topic セクションが設定されている
        When: get_ollama_config(params, "extract_topic") が呼ばれる
        Then: 該当セクションのパラメーターが使用される

        Expected from contracts/parameters.yml:
        - model: "llama3.2:3b"
        - num_predict: 64
        - timeout: 30
        - Other values from defaults
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "extract_topic": {
                        "model": "llama3.2:3b",
                        "num_predict": 64,
                        "timeout": 30,
                    },
                },
            }
        }

        config = get_ollama_config(params, "extract_topic")

        # Should be OllamaConfig instance
        self.assertIsInstance(config, OllamaConfig)

        # extract_topic overrides should be applied
        self.assertEqual(config.model, "llama3.2:3b")
        self.assertEqual(config.num_predict, 64)
        self.assertEqual(config.timeout, 30)

        # Defaults should be applied for non-overridden fields
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertAlmostEqual(config.temperature, 0.2, places=2)


class TestFunctionOverridePriority(unittest.TestCase):
    """get_ollama_config: Function-specific values override defaults."""

    def test_function_override_priority(self):
        """関数別設定がデフォルト値をオーバーライドすること。

        Merge Logic from data-model.md:
        1. defaults から基本設定を取得
        2. functions.{function_name} でオーバーライド
        3. OllamaConfig として返却

        When same parameter is set in both defaults and functions:
        - Function-specific value should take precedence
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,  # Default timeout
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "extract_knowledge": {
                        "timeout": 300,  # Override timeout
                    },
                },
            }
        }

        config = get_ollama_config(params, "extract_knowledge")

        # Function-specific value (300) should override default (120)
        self.assertEqual(config.timeout, 300)

        # Non-overridden values should remain from defaults
        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertAlmostEqual(config.temperature, 0.2, places=2)
        self.assertEqual(config.num_predict, -1)

    def test_function_override_all_fields(self):
        """全フィールドをオーバーライドした場合、すべてが適用されること。"""
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "extract_knowledge": {
                        "model": "oss-gpt:20b",
                        "base_url": "http://custom-server:11434",
                        "timeout": 600,
                        "temperature": 0.5,
                        "num_predict": 32768,
                    },
                },
            }
        }

        config = get_ollama_config(params, "extract_knowledge")

        # All function-specific values should be applied
        self.assertEqual(config.model, "oss-gpt:20b")
        self.assertEqual(config.base_url, "http://custom-server:11434")
        self.assertEqual(config.timeout, 600)
        self.assertAlmostEqual(config.temperature, 0.5, places=2)
        self.assertEqual(config.num_predict, 32768)


class TestGetConfigUnknownFunction(unittest.TestCase):
    """get_ollama_config: Unknown function name falls back to defaults."""

    def test_unknown_function_uses_defaults(self):
        """存在しない関数名の場合、デフォルト値が使用されること。

        Edge case from spec.md:
        - 関数名の誤記: parameters.yml に存在しない関数名が設定された場合、
          無視してデフォルト値を使用する
        """
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "extract_knowledge": {
                        "num_predict": 16384,
                    },
                },
            }
        }

        # Unknown function name
        config = get_ollama_config(params, "nonexistent_function")

        # Should use defaults only (no function-specific overrides)
        self.assertIsInstance(config, OllamaConfig)
        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.timeout, 120)
        self.assertAlmostEqual(config.temperature, 0.2, places=2)
        self.assertEqual(config.num_predict, -1)


class TestGetConfigMissingFunctionsSection(unittest.TestCase):
    """get_ollama_config: Missing 'functions' section uses defaults."""

    def test_missing_functions_section_uses_defaults(self):
        """functions セクションがない場合、デフォルト値が使用されること。"""
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                # No 'functions' section
            }
        }

        config = get_ollama_config(params, "extract_knowledge")

        # Should use defaults
        self.assertIsInstance(config, OllamaConfig)
        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.timeout, 120)
        self.assertEqual(config.num_predict, -1)


# =============================================================================
# Phase 3 RED Tests: User Story 2 - デフォルト値の適用
# =============================================================================


class TestHardcodedDefaultsApplied(unittest.TestCase):
    """get_ollama_config: Empty params returns hardcoded defaults."""

    def test_empty_params_returns_hardcoded_defaults(self):
        """空の params で HARDCODED_DEFAULTS が返されること。

        US2 - Acceptance Scenario 2:
        Given: ollama セクションが空である
        When: いずれかの関数が実行される
        Then: 全パラメーターにデフォルト値が適用される

        Expected HARDCODED_DEFAULTS from data-model.md:
        - model: no default (KeyError expected)
        - base_url: "http://localhost:11434"
        - timeout: 120
        - temperature: 0.2
        - num_predict: -1
        """
        from obsidian_etl.utils.ollama_config import get_ollama_config

        # Empty params - should fail because model is required
        params = {}

        with self.assertRaises(TypeError) as ctx:
            get_ollama_config(params, "extract_knowledge")

        # Should indicate missing required argument 'model'
        self.assertIn("model", str(ctx.exception).lower())

    def test_empty_ollama_section_returns_hardcoded_defaults(self):
        """ollama セクションが空の場合、HARDCODED_DEFAULTS が返されること。"""
        from obsidian_etl.utils.ollama_config import get_ollama_config

        # ollama section exists but is empty - should fail because model is required
        params = {"ollama": {}}

        with self.assertRaises(TypeError) as ctx:
            get_ollama_config(params, "extract_knowledge")

        # Should indicate missing required argument 'model'
        self.assertIn("model", str(ctx.exception).lower())


class TestPartialDefaultsMerge(unittest.TestCase):
    """get_ollama_config: Partial defaults merged with hardcoded."""

    def test_partial_defaults_merge(self):
        """defaults で一部のみ指定した場合、残りは HARDCODED_DEFAULTS が使用されること。

        US2 - Acceptance Scenario 1:
        Given: ollama.defaults に一部パラメーターのみ設定されている
        When: 関数が実行される
        Then: 未指定パラメーターにはハードコードされたデフォルト値が適用される
        """
        from obsidian_etl.utils.ollama_config import (
            HARDCODED_DEFAULTS,
            OllamaConfig,
            get_ollama_config,
        )

        # Model and timeout specified in defaults
        params = {
            "ollama": {
                "defaults": {
                    "model": "custom-model",  # Required field
                    "timeout": 200,
                }
            }
        }

        config = get_ollama_config(params, "extract_knowledge")

        # Model should be custom value
        self.assertEqual(config.model, "custom-model")
        self.assertEqual(config.timeout, 200)

        # Other values should be hardcoded defaults
        self.assertEqual(config.base_url, HARDCODED_DEFAULTS["base_url"])
        self.assertAlmostEqual(config.temperature, HARDCODED_DEFAULTS["temperature"], places=2)
        self.assertEqual(config.num_predict, HARDCODED_DEFAULTS["num_predict"])


class TestPartialFunctionOverride(unittest.TestCase):
    """get_ollama_config: Partial function override uses defaults for rest."""

    def test_partial_function_override(self):
        """関数別設定で一部のみオーバーライドした場合、残りは defaults/HARDCODED が使用されること。

        Test merge priority:
        1. HARDCODED_DEFAULTS (lowest)
        2. ollama.defaults
        3. ollama.functions.{function_name} (highest)

        Input:
        - defaults.model = "gemma3:12b"
        - defaults.timeout = 100
        - functions.extract_knowledge.num_predict = 8000

        Expected output:
        - timeout = 100 (from defaults)
        - num_predict = 8000 (from function override)
        - others from HARDCODED_DEFAULTS
        """
        from obsidian_etl.utils.ollama_config import (
            HARDCODED_DEFAULTS,
            OllamaConfig,
            get_ollama_config,
        )

        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",  # Required field
                    "timeout": 100,  # Override hardcoded default
                },
                "functions": {
                    "extract_knowledge": {
                        "num_predict": 8000,  # Function-specific override
                    }
                },
            }
        }

        config = get_ollama_config(params, "extract_knowledge")

        # Function override should be applied
        self.assertEqual(config.num_predict, 8000)

        # Defaults override should be applied
        self.assertEqual(config.timeout, 100)

        # Model from defaults
        self.assertEqual(config.model, "gemma3:12b")

        # Hardcoded defaults for non-specified fields
        self.assertEqual(config.base_url, HARDCODED_DEFAULTS["base_url"])
        self.assertAlmostEqual(config.temperature, HARDCODED_DEFAULTS["temperature"], places=2)


class TestTimeoutValidation(unittest.TestCase):
    """get_ollama_config: Timeout validation (1-600 seconds)."""

    def test_timeout_below_min_raises(self):
        """timeout が 0 以下の場合、ValueError が発生すること。

        Edge case from spec.md:
        無効なパラメーター値: timeout に負の値が設定された場合、
        デフォルト値にフォールバックする

        Note: Implementation may either raise ValueError or fallback.
        This test expects ValueError for strict validation.
        """
        from obsidian_etl.utils.ollama_config import get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "timeout": 0,  # Invalid: below minimum of 1
                }
            }
        }

        with self.assertRaises(ValueError) as ctx:
            get_ollama_config(params, "extract_knowledge")

        self.assertIn("timeout", str(ctx.exception).lower())

    def test_timeout_above_max_raises(self):
        """timeout が 600 超の場合、ValueError が発生すること。

        From research.md constraints:
        timeout: {min: 1, max: 600}  # seconds
        """
        from obsidian_etl.utils.ollama_config import get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "timeout": 601,  # Invalid: above maximum of 600
                }
            }
        }

        with self.assertRaises(ValueError) as ctx:
            get_ollama_config(params, "extract_knowledge")

        self.assertIn("timeout", str(ctx.exception).lower())

    def test_timeout_at_boundary_valid(self):
        """timeout が境界値 (1, 600) の場合、正常に動作すること。"""
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        # Test minimum boundary
        params_min = {"ollama": {"defaults": {"model": "gemma3:12b", "timeout": 1}}}
        config_min = get_ollama_config(params_min, "extract_knowledge")
        self.assertEqual(config_min.timeout, 1)

        # Test maximum boundary
        params_max = {"ollama": {"defaults": {"model": "gemma3:12b", "timeout": 600}}}
        config_max = get_ollama_config(params_max, "extract_knowledge")
        self.assertEqual(config_max.timeout, 600)


class TestTemperatureValidation(unittest.TestCase):
    """get_ollama_config: Temperature validation (0.0-2.0)."""

    def test_temperature_below_min_raises(self):
        """temperature が 0.0 未満の場合、ValueError が発生すること。

        From research.md constraints:
        temperature: {min: 0.0, max: 2.0}
        """
        from obsidian_etl.utils.ollama_config import get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "temperature": -0.1,  # Invalid: below minimum of 0.0
                }
            }
        }

        with self.assertRaises(ValueError) as ctx:
            get_ollama_config(params, "extract_knowledge")

        self.assertIn("temperature", str(ctx.exception).lower())

    def test_temperature_above_max_raises(self):
        """temperature が 2.0 超の場合、ValueError が発生すること。

        From research.md constraints:
        temperature: {min: 0.0, max: 2.0}
        """
        from obsidian_etl.utils.ollama_config import get_ollama_config

        params = {
            "ollama": {
                "defaults": {
                    "temperature": 2.1,  # Invalid: above maximum of 2.0
                }
            }
        }

        with self.assertRaises(ValueError) as ctx:
            get_ollama_config(params, "extract_knowledge")

        self.assertIn("temperature", str(ctx.exception).lower())

    def test_temperature_at_boundary_valid(self):
        """temperature が境界値 (0.0, 2.0) の場合、正常に動作すること。"""
        from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config

        # Test minimum boundary
        params_min = {"ollama": {"defaults": {"model": "gemma3:12b", "temperature": 0.0}}}
        config_min = get_ollama_config(params_min, "extract_knowledge")
        self.assertAlmostEqual(config_min.temperature, 0.0, places=2)

        # Test maximum boundary
        params_max = {"ollama": {"defaults": {"model": "gemma3:12b", "temperature": 2.0}}}
        config_max = get_ollama_config(params_max, "extract_knowledge")
        self.assertAlmostEqual(config_max.temperature, 2.0, places=2)


if __name__ == "__main__":
    unittest.main()
