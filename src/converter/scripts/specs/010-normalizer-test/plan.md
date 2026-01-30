# Implementation Plan: Normalizer Test Infrastructure

## Technical Context

| Item | Value |
|------|-------|
| Branch | 010-normalizer-test |
| Spec | specs/010-normalizer-test/spec.md |
| Language | Python 3.11+ |
| Test Framework | unittest (標準ライブラリ) |
| Dependencies | なし（標準ライブラリのみ） |

## Design Decisions

### D1: テストディレクトリ切り替え方式

**Decision**: `config.py` の `INDEX_DIR` を環境変数で上書き可能にする

**Rationale**:
- 既存コードの変更を最小限に
- テスト時のみ `TEST_INDEX_DIR` 環境変数を設定
- 本番コードに影響なし

**Implementation**:
```python
# config.py に追加
import os
INDEX_DIR = Path(os.environ.get("NORMALIZER_INDEX_DIR", str(BASE_DIR / "@index")))
```

### D2: Ollama API モック方式

**Decision**: `unittest.mock.patch` で `io/ollama.py` の `call_ollama` をモック

**Rationale**:
- テスト実行時間短縮
- ネットワーク依存排除
- 期待するレスポンスを制御可能

### D3: テスト構成

**Decision**: モジュールごとにテストファイルを分離

```
tests/
├── __init__.py
├── test_files.py       # io/files.py
├── test_validators.py  # validators/
├── test_pipeline.py    # pipeline/stages.py
├── test_english.py     # detection/english.py
├── test_session.py     # state/, io/session.py
└── fixtures/
    ├── with_frontmatter.md
    ├── without_frontmatter.md
    ├── english_doc.md
    └── japanese_doc.md
```

## Implementation Tasks

### Phase 1: インフラ整備

| ID | Task | Module | Lines |
|----|------|--------|-------|
| T01 | config.py に環境変数対応追加 | config.py | ~5 |
| T02 | tests/__init__.py 作成 | tests/ | ~10 |
| T03 | テストフィクスチャ作成 | tests/fixtures/ | ~100 |

### Phase 2: 主要機能テスト

| ID | Task | Module | Lines |
|----|------|--------|-------|
| T04 | test_files.py - ファイル読み書き | tests/ | ~80 |
| T05 | test_validators.py - frontmatter | tests/ | ~100 |
| T06 | test_pipeline.py - ジャンル分類 | tests/ | ~80 |
| T07 | test_english.py - 英語検出 | tests/ | ~60 |
| T08 | test_session.py - セッション管理 | tests/ | ~80 |

### Phase 3: Makefile統合

| ID | Task | Module | Lines |
|----|------|--------|-------|
| T09 | Makefile に test ターゲット追加 | Makefile | ~10 |

## Makefile Target

```makefile
# テスト実行
test:
	@NORMALIZER_INDEX_DIR=$(BASE_DIR)/@test $(PYTHON) -m unittest discover -s tests -v

# テスト（カバレッジなし、高速）
test-quick:
	@NORMALIZER_INDEX_DIR=$(BASE_DIR)/@test $(PYTHON) -m unittest discover -s tests
```

## Success Verification

1. `make test` で全テスト実行 → PASS
2. `@index` フォルダが変更されていないこと
3. 各モジュールの主要機能が検証されていること
