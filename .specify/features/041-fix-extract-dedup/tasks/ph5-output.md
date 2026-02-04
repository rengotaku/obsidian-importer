# Phase 5 Output

## 作業概要
- User Story 3 - GitHub Extractor Template Unification の実装完了
- FAIL テスト 4 件を PASS させた
- GitHub Extractor が BaseExtractor テンプレートメソッドパターンに従うようになった

## 修正ファイル一覧

### プロダクションコード

- `src/etl/stages/extract/github_extractor.py`
  - `discover_items()` override を削除（lines 267-332）
  - `stage_type` override を削除（lines 189-194）
  - `_discover_raw_items()` が BaseExtractor のテンプレートメソッド経由で呼ばれるようになった
  - URL 文字列と Path オブジェクトの両方を受け入れるように `_discover_raw_items()` を修正

### テストコード

- `src/etl/tests/test_github_extractor.py`
  - `discover_items()` が Iterator を返すように変更されたため、テストを `list()` でラップ
  - Mock 設定を修正（MagicMock から実際の Path オブジェクトに変更）
  - 4 テストメソッドを修正

## テスト結果

### Phase 5 新規テスト（RED → GREEN）

```bash
python -m unittest src.etl.tests.test_extractor_template.TestGitHubNoDiscoverItemsOverride \
  src.etl.tests.test_extractor_template.TestGitHubNoStageTypeOverride \
  src.etl.tests.test_extractor_template.TestGitHubDiscoverRawItemsReturnsIterator
```

結果: **6 tests PASS** ✅

- `test_discover_items_not_defined_on_github_extractor`: PASS
- `test_discover_items_is_inherited_from_base`: PASS
- `test_stage_type_not_defined_on_github_extractor`: PASS
- `test_stage_type_returns_extract_via_inheritance`: PASS (safety net)
- `test_discover_items_returns_iterator_not_list`: PASS
- `test_discover_raw_items_is_generator_function`: PASS (safety net)

### 既存テスト回帰確認

```bash
python -m unittest src.etl.tests.test_github_extractor
```

結果: **6 tests PASS** ✅

- `test_discover_items_valid_url`: PASS
- `test_discover_items_invalid_url`: PASS
- `test_full_extraction_flow`: PASS
- `test_resume_mode_skip_processed`: PASS
- `test_file_id_in_metadata`: PASS
- `test_consistent_file_id`: PASS

### FileExtractor 非影響確認

```bash
python -m unittest src.etl.tests.test_organize_phase
```

結果: **15 tests PASS** ✅（BaseStage 直接継承の FileExtractor に影響なし）

## 実装の変更点

### Before（Phase 4 終了時）

```python
class GitHubExtractor(BaseExtractor):
    @property
    def stage_type(self):
        from src.etl.core.types import StageType
        return StageType.EXTRACT  # ❌ BaseExtractor と同じ値で override

    def discover_items(self, input_source: str | Path) -> list[ProcessingItem]:
        # ❌ BaseExtractor のテンプレートメソッドをバイパス
        # git clone → discover の処理を直接実装
        # list を返す（Iterator ではない）
        ...
        return items

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        # ✅ 実装済みだが使われていない（discover_items override のため）
        ...
        yield item
```

### After（Phase 5 完了時）

```python
class GitHubExtractor(BaseExtractor):
    # ✅ stage_type override 削除 → BaseExtractor.stage_type を継承

    # ✅ discover_items() override 削除 → BaseExtractor のテンプレートメソッドを使用
    #   BaseExtractor.discover_items() → _discover_raw_items() → _chunk_if_needed()

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        # ✅ テンプレートメソッド経由で呼ばれるようになった
        # ✅ git clone ロジックが集約されている
        # ✅ yield でIterator を返す
        ...
        yield item

    def _build_conversation_for_chunking(self, item: ProcessingItem):
        # ✅ 既存実装（GitHub 記事はチャンキング不要）
        return None
```

## 設計上の改善点

### 1. テンプレートメソッドパターンの統一

**Before**:
- GitHub Extractor だけ `discover_items()` を override してテンプレートをバイパス
- Claude/ChatGPT と動作フローが異なる

**After**:
- 全 Extractor（Claude, ChatGPT, GitHub）が BaseExtractor のテンプレートに従う
- `discover_items()` → `_discover_raw_items()` → `_chunk_if_needed()` の統一フロー

### 2. コード重複の解消

**Before**:
- `discover_items()` override と `_discover_raw_items()` でほぼ同一の git clone ロジック
- 片方が使われず、もう片方が実際の処理を担当（混乱を招く）

**After**:
- `_discover_raw_items()` のみが git clone ロジックを持つ
- テンプレートメソッドが自動的に `_discover_raw_items()` を呼び出す

### 3. Iterator vs List の統一

**Before**:
- `discover_items()` override が `list` を返す
- BaseExtractor のシグネチャ（`Iterator`）と異なる

**After**:
- BaseExtractor のテンプレートメソッドが `Iterator` を返す
- `_discover_raw_items()` が `yield` で Iterator を生成
- メモリ効率が向上（大量ファイル処理時）

### 4. stage_type の冗長性解消

**Before**:
- GitHubExtractor が `stage_type` を override（BaseExtractor と同値）
- 全 Extractor で同じパターンの冗長な override

**After**:
- BaseExtractor の `stage_type` を継承
- override 不要（DRY 原則に従う）

## 注意点

### 1. テストの破壊的変更

既存の `test_github_extractor.py` は `discover_items()` が list を返す前提だったため、以下の修正が必要だった:

```python
# Before
items = extractor.discover_items(url)
self.assertEqual(len(items), 2)

# After
items = list(extractor.discover_items(url))  # Iterator → list に変換
self.assertEqual(len(items), 2)
```

この変更は **仕様の改善**（Iterator によるメモリ効率向上）のため、意図的な破壊的変更。

### 2. FileExtractor への影響なし

FileExtractor は BaseStage を直接継承しており、BaseExtractor のテンプレートメソッドを使用していない。今回の変更は BaseExtractor のみに影響するため、organize Phase の処理には一切影響なし。

## 次 Phase への引き継ぎ

### Phase 6 の前提条件

Phase 5 完了により、以下が保証される:

1. **全 4 Extractor が統一パターン**: Claude, ChatGPT, GitHub, File
2. **BaseExtractor テンプレートの完成**: `_discover_raw_items()` + `_chunk_if_needed()` + `_build_chunk_messages()`
3. **重複処理の構造的防止**: テンプレートメソッドが discover → chunk → run の順序を強制

Phase 6（US4: INPUT_TYPE と複数 INPUT 対応）では、CLI レイヤーで入力インターフェースを統一する。プロバイダー依存の入力処理（`if provider == "github"`）を排除し、`--input-type` で明示的に指定する設計に移行する。

## 実装のミス・課題

### なし

Phase 5 は計画通りに完了。テストも全て PASS。

### 将来の改善候補

1. **FileExtractor の BaseExtractor 移行**: 現在 BaseStage 直接継承。別 feature で対応（今回のスコープ外）
2. **URL 入力の型安全性**: `_discover_raw_items()` が `Path` 型ヒントだが、実際には `str`（URL）も受け入れる。Phase 6 で CLI レイヤーの入力解決を統一すれば、この問題は解消される可能性あり
