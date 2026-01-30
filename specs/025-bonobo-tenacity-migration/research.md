# Research: Bonobo & Tenacity Migration

**Date**: 2026-01-19
**Feature**: 025-bonobo-tenacity-migration

## 1. Bonobo 安定性調査

### 調査結果

| 項目 | 状況 |
|------|------|
| 最新バージョン | 0.6.4（alpha） |
| 最終リリース | 6年以上前 |
| 開発状態 | 停滞（actively maintained ではない） |
| Python 対応 | 3.5+ |

### 既知の制限事項

1. **Alpha ステータス**: API 変更の可能性あり
2. **シンプルなデータ処理**: 行単位のノード処理、大規模データセット非推奨
3. **GIL 制限**: 真の並列処理は制限される
4. **メモリ消費**: 大量データでメモリ圧迫の可能性

### 決定

**Decision**: bonobo の導入を **保留** し、代替アプローチを採用

**Rationale**:
- 6年以上開発が停滞しており、長期的なメンテナンス性に懸念
- 本プロジェクトの規模（単一ユーザー、ローカル環境）では bonobo のメリットが限定的
- 既存のパイプライン構造（Stage A → B → C）をそのまま ETL パターンに再編成可能

**Alternatives Considered**:
1. **bonobo 導入** → 開発停滞で却下
2. **Luigi/Airflow** → オーバーエンジニアリング、却下
3. **カスタム ETL フレームワーク** → 採用。シンプルな Stage ベース設計

### 代替アプローチ: カスタム ETL フレームワーク

```python
# シンプルな Stage ベースパイプライン
class Stage(ABC):
    @abstractmethod
    def extract(self, input_path: Path) -> Iterator[ProcessingItem]: ...

    @abstractmethod
    def transform(self, item: ProcessingItem) -> ProcessingItem: ...

    @abstractmethod
    def load(self, item: ProcessingItem, output_path: Path) -> None: ...
```

**利点**:
- 依存関係なし（標準ライブラリのみ）
- 既存コードとの互換性が高い
- テスト容易性を維持

---

## 2. Tenacity 統合パターン

### ベストプラクティス

| パターン | 用途 | 設定例 |
|---------|------|--------|
| Exponential Backoff + Jitter | API 呼び出し | `wait_random_exponential(multiplier=1, max=60)` |
| Fixed + Random | Rate Limit 対策 | `wait_fixed(3) + wait_random(0, 2)` |
| Stop After Attempts | 無限ループ防止 | `stop_after_attempt(3)` |
| Exception-specific | 選択的リトライ | `retry_if_exception_type(ConnectionError)` |

### Ollama API 向け推奨設定

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_log,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before=before_log(logger, logging.WARNING),
)
def call_ollama(prompt: str) -> str:
    ...
```

### 決定

**Decision**: tenacity を **採用**

**Rationale**:
- 活発にメンテナンスされている
- デコレータベースで既存コードへの組み込みが容易
- Ollama API のタイムアウト/接続エラーに対応可能

---

## 3. 既存コード分析

### llm_import モジュール構造

```
llm_import/
├── cli.py                 # エントリポイント（main, cmd_process, cmd_retry 等）
├── base.py                # BaseMessage, BaseConversation, BaseParser
├── providers/claude/      # Claude 固有パーサー
└── common/
    ├── ollama.py          # Ollama API クライアント → tenacity 適用対象
    ├── retry.py           # 手動リトライ → tenacity で置換
    ├── session_logger.py  # セッションログ → Session/Phase 構造に統合
    └── knowledge_extractor.py  # ナレッジ抽出 → Transform Stage
```

### normalizer モジュール構造

```
normalizer/
├── models.py              # NormalizationResult, Frontmatter 等
├── pipeline/
│   ├── runner.py          # run_pipeline_v2 → Phase.run() に移行
│   └── stages.py          # stage_a, stage_b, stage_c → Stage 実装に移行
├── processing/
│   ├── single.py          # 単一ファイル処理
│   └── batch.py           # バッチ処理
└── io/
    ├── session.py         # セッション管理 → Session クラスに統合
    └── ollama.py          # Ollama 呼び出し → tenacity 適用
```

### 移行マッピング

| 既存 | 移行先 | 備考 |
|------|--------|------|
| `llm_import/cli.py` | `etl/cli.py` | コマンド統合 |
| `llm_import/common/retry.py` | `etl/core/retry.py` | tenacity ベース |
| `llm_import/common/session_logger.py` | `etl/core/session.py` | Session 構造統合 |
| `llm_import/common/knowledge_extractor.py` | `etl/stages/transform/knowledge_transformer.py` | |
| `normalizer/pipeline/runner.py` | `etl/phases/organize_phase.py` | |
| `normalizer/pipeline/stages.py` | `etl/stages/transform/normalizer_transformer.py` | |

---

## 4. 設計決定サマリー

| 項目 | 決定 | 理由 |
|------|------|------|
| bonobo | 不採用 | 開発停滞、alpha 状態 |
| tenacity | 採用 | 活発なメンテナンス、デコレータベース |
| パイプライン | カスタム実装 | シンプル、依存なし |
| 並列処理 | 将来検討 | MVP では単一スレッド |

---

## Sources

- [Bonobo Project](https://www.bonobo-project.org/)
- [Bonobo GitHub](https://github.com/python-bonobo)
- [Tenacity Documentation](https://tenacity.readthedocs.io/)
- [Tenacity GitHub](https://github.com/jd/tenacity)
- [Python Retry Logic with Tenacity](https://python.useinstructor.com/concepts/retrying/)
