# Phase 2 Output

## 作業概要
- Phase 2 - User Story 1: 関数別パラメーター設定 の実装完了
- FAIL テスト 10 件を PASS させた
- `get_ollama_config()` 関数により、関数別に異なる Ollama パラメーターを取得可能

## 修正ファイル一覧
- `src/obsidian_etl/utils/ollama_config.py` - 新規作成
  - `OllamaConfig` dataclass: Ollama パラメーター設定を保持
  - `get_ollama_config()` 関数: 関数別パラメーター取得とマージ処理
  - `VALID_FUNCTION_NAMES` 定数: 有効な関数名のセット

## 実装詳細

### OllamaConfig dataclass

```python
@dataclass
class OllamaConfig:
    """Ollama configuration for a specific function."""
    model: str = "gemma3:12b"
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    temperature: float = 0.2
    num_predict: int = -1  # -1 = unlimited
```

### get_ollama_config() 関数

**マージ優先順位**:
1. OllamaConfig のデフォルト値（ハードコード）
2. `params["ollama"]["defaults"]`
3. `params["ollama"]["functions"][function_name]`

**動作**:
- `defaults` セクションから基本設定を取得
- `functions.{function_name}` セクションがあればオーバーライド
- 未知の関数名でもエラーにせず、デフォルト値を返却

### テスト結果

全 323 テスト PASS:

| テストクラス | テスト件数 | 内容 |
|-------------|-----------|------|
| TestOllamaConfigDataclass | 3 | OllamaConfig dataclass の構造・デフォルト値 |
| TestGetConfigExtractKnowledge | 1 | extract_knowledge 用パラメーター取得 |
| TestGetConfigTranslateSummary | 1 | translate_summary 用パラメーター取得 |
| TestGetConfigExtractTopic | 1 | extract_topic 用パラメーター取得 |
| TestFunctionOverridePriority | 2 | 関数別設定のオーバーライド優先度 |
| TestGetConfigUnknownFunction | 1 | 未知の関数名でのフォールバック |
| TestGetConfigMissingFunctionsSection | 1 | functions セクションなしのフォールバック |

## 注意点

### 既存テストへの影響
- 全 323 テスト PASS - リグレッションなし
- 既存機能への影響なし

### 次 Phase で必要な情報

**Phase 3 (User Story 2 - デフォルト値の適用)**:
- バリデーション機能追加: `timeout` (1-600), `temperature` (0.0-2.0) の範囲チェック
- レガシー互換性: `import.ollama`, `organize.ollama` からのフォールバック
- HARDCODED_DEFAULTS 定数の明示化

**Phase 4 (User Story 3 - extract_topic の統一実装)**:
- `src/obsidian_etl/pipelines/organize/nodes.py` での `get_ollama_config()` 使用
- `_extract_topic_via_llm()` のリファクタリング

**Phase 5 (Integration)**:
- `src/obsidian_etl/utils/knowledge_extractor.py` での `get_ollama_config()` 使用
- `extract_knowledge()`, `translate_summary()` の統一

## 実装のミス・課題

なし。全テスト PASS。

## Checkpoint

User Story 1 完了:
- ✅ `get_ollama_config()` が各関数用の正しい設定を返す
- ✅ 関数別設定がデフォルト値をオーバーライドする
- ✅ 未知の関数名でもデフォルト値にフォールバック
- ✅ functions セクションなしでもデフォルト値を使用
