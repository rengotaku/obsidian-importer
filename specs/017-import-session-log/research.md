# Research: Import Session Log

## 1. 既存セッション管理の再利用方針

### Decision
`normalizer/io/session.py` をそのまま再利用し、プレフィックス指定機能を追加する。

### Rationale
- 既存コードは安定しており、十分にテストされている
- `progress_bar()`, `timestamp()`, `log_message()`, `create_new_session()` 等の関数は汎用的
- 新たにモジュールを作成するよりも、既存モジュールを拡張する方が保守性が高い

### Alternatives Considered
1. **llm_import 専用の session モジュールを新規作成** - 却下: コード重複が発生
2. **共通モジュール `scripts/common/session.py` に移動** - 却下: 影響範囲が大きく、今回のスコープ外

### Implementation Notes
- `create_new_session()` にオプション引数 `prefix: str = ""` を追加
- prefix が指定された場合: `{prefix}_{YYYYMMDD_HHMMSS}`
- prefix が指定されない場合: 既存動作 `{YYYYMMDD_HHMMSS}`

---

## 2. llm_import の状態管理との整合性

### Decision
既存の `.extraction_state.json` は廃止せず、セッションログと併用する。

### Rationale
- `.extraction_state.json` は「どの会話が処理済みか」を追跡（重複処理防止）
- セッションログは「1回の実行の進捗」を記録（可視化・分析用）
- 役割が異なるため、両方を維持する

### Implementation Notes
- `StateManager` は既存のまま維持
- 新たに `SessionLogger` クラスを `llm_import/common/` に追加
- `SessionLogger` は `normalizer/io/session.py` の関数を呼び出す

---

## 3. コンソール出力とログの同期方法

### Decision
デュアル出力用のラッパー関数を作成し、print と log_message を同時に呼び出す。

### Rationale
- `normalizer/io/session.py` の `log_message()` は `also_print=True` で両方出力可能
- この仕組みをそのまま活用できる

### Implementation Notes
- `log_message(message, session_dir, also_print=True)` を使用
- プログレスバー更新時は `\r` でカーソル移動（ログファイルには改行で記録）

---

## 4. pipeline_stages.jsonl の記録タイミング

### Decision
各 Phase の完了直後に JSONL 形式で追記する。

### Rationale
- normalizer と同じフォーマットを採用することで互換性を確保
- 追記形式（append）により、処理中でも確認可能

### Format
```json
{"timestamp": "2026-01-16T18:30:08", "filename": "会話タイトル.md", "stage": "phase1", "executed": true, "timing_ms": 1234, "skipped_reason": null}
{"timestamp": "2026-01-16T18:30:38", "filename": "会話タイトル.md", "stage": "phase2", "executed": true, "timing_ms": 15678, "skipped_reason": null}
```

---

## 5. プログレスバー実装

### Decision
`normalizer/io/session.py` の `progress_bar()` 関数を使用する。

### Rationale
- 既存実装が Unicode ブロック文字で見やすいプログレスバーを生成
- `[████████░░░░░░░░] 25/100 (25.0%)` 形式

### Implementation Notes
- 各会話処理前に更新
- コンソールは `\r` で上書き、ログファイルは定期的に（10件ごとなど）記録

---

## 6. エラー時の graceful degradation

### Decision
セッションログ機能がエラーになっても、メイン処理は継続する。

### Rationale
- ログは補助機能であり、本来の処理を妨げてはならない
- ファイル書き込みエラー等は警告を出すが、処理は続行

### Implementation Notes
```python
try:
    session_logger.log(...)
except Exception as e:
    print(f"⚠️ ログ書き込みエラー: {e}")
    # 処理は継続
```
