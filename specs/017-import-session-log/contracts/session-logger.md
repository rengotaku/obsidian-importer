# Contract: SessionLogger

内部 API 定義（Python クラスインターフェース）

## Class: SessionLogger

`llm_import` 用のセッションログラッパー。

### Constructor

```python
def __init__(
    self,
    provider: str,
    total_files: int,
    prefix: str = "import"
) -> None:
    """
    Args:
        provider: プロバイダー名（例: "claude"）
        total_files: 処理対象の総会話数
        prefix: セッションディレクトリのプレフィックス（デフォルト: "import"）
    """
```

### Methods

#### start_session

```python
def start_session(self) -> Path:
    """
    セッションを開始し、初期ファイルを作成する。

    Returns:
        セッションディレクトリのパス

    Side Effects:
        - .staging/@plan/{prefix}_YYYYMMDD_HHMMSS/ を作成
        - session.json を作成
        - execution.log を作成（ヘッダー書き込み）
    """
```

#### log

```python
def log(self, message: str, also_print: bool = True) -> None:
    """
    ログメッセージを記録する。

    Args:
        message: ログメッセージ
        also_print: コンソールにも出力するか（デフォルト: True）

    Side Effects:
        - execution.log に追記
        - also_print=True の場合、コンソールにも出力
    """
```

#### log_stage

```python
def log_stage(
    self,
    filename: str,
    stage: str,
    timing_ms: int,
    executed: bool = True,
    skipped_reason: str | None = None
) -> None:
    """
    処理ステージを記録する。

    Args:
        filename: 処理対象のファイル名/会話タイトル
        stage: ステージ名（"phase1" | "phase2"）
        timing_ms: 処理時間（ミリ秒）
        executed: 実行されたか
        skipped_reason: スキップ理由

    Side Effects:
        - pipeline_stages.jsonl に追記
    """
```

#### log_progress

```python
def log_progress(self, current: int, title: str, phase1_ok: bool, phase2_ok: bool | None, elapsed_sec: float) -> None:
    """
    進捗を記録・表示する。

    Args:
        current: 現在の処理番号（1-indexed）
        title: 会話タイトル
        phase1_ok: Phase 1 成功したか
        phase2_ok: Phase 2 成功したか（None = 未実行）
        elapsed_sec: この会話の処理時間（秒）

    Side Effects:
        - コンソールにプログレスバーと結果を表示
        - execution.log に記録
    """
```

#### add_processed

```python
def add_processed(self, file: str, output: str) -> None:
    """
    処理成功を記録する。

    Args:
        file: ファイル名/会話ID
        output: 出力先パス
    """
```

#### add_error

```python
def add_error(self, file: str, error: str, stage: str) -> None:
    """
    エラーを記録する。

    Args:
        file: ファイル名/会話ID
        error: エラーメッセージ
        stage: エラー発生ステージ
    """
```

#### add_pending

```python
def add_pending(self, file: str, reason: str) -> None:
    """
    未処理を記録する。

    Args:
        file: ファイル名/会話ID
        reason: 未処理理由
    """
```

#### finalize

```python
def finalize(self, elapsed_seconds: float) -> None:
    """
    セッションを終了し、最終結果を記録する。

    Args:
        elapsed_seconds: 総処理時間（秒）

    Side Effects:
        - processed.json を書き込み
        - errors.json を書き込み
        - pending.json を書き込み
        - results.json を書き込み
        - execution.log にサマリーを追記
        - コンソールにサマリーを表示
    """
```

### Properties

```python
@property
def session_dir(self) -> Path | None:
    """セッションディレクトリのパス（開始前は None）"""

@property
def stats(self) -> dict[str, int]:
    """現在の統計情報 {"success": N, "error": N, "pending": N}"""
```

---

## Function: create_new_session (既存拡張)

`normalizer/io/session.py` の関数を拡張。

```python
def create_new_session(prefix: str = "") -> Path:
    """
    新しいセッションディレクトリを作成する。

    Args:
        prefix: ディレクトリ名のプレフィックス（空文字の場合は従来動作）

    Returns:
        作成されたセッションディレクトリのパス

    Examples:
        create_new_session()          -> .staging/@plan/20260116_185500/
        create_new_session("import")  -> .staging/@plan/import_20260116_185500/
        create_new_session("test")    -> .staging/@plan/test_20260116_185500/
    """
```
