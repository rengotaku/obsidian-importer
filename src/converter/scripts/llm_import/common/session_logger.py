"""
SessionLogger - llm_import 用セッションログラッパー

normalizer/io/session.py の機能を利用し、llm_import 専用の
セッション管理とログ出力を提供する。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Import normalizer functions - support both paths depending on execution context
# When run from .dev (llm_import tests): scripts.normalizer
# When run from .dev/scripts (normalizer tests): normalizer
import sys
from pathlib import Path

# Add scripts dir to path if not present
_scripts_dir = Path(__file__).resolve().parent.parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from normalizer.io.session import (
    create_new_session,
    get_log_file,
    log_message,
    progress_bar,
    timestamp,
)

from scripts.llm_import.common.folder_manager import FolderManager


class SessionLogger:
    """llm_import 用のセッションログラッパー

    Attributes:
        provider: プロバイダー名（例: "claude"）
        total_files: 処理対象の総会話数
        prefix: セッションディレクトリのプレフィックス
        session_dir: セッションディレクトリのパス（開始後に設定）
    """

    def __init__(
        self,
        provider: str,
        total_files: int,
        prefix: str = "import",
        source_session: str | None = None,
        folder_manager: FolderManager | None = None,
    ) -> None:
        """
        Args:
            provider: プロバイダー名（例: "claude"）
            total_files: 処理対象の総会話数
            prefix: セッションディレクトリのプレフィックス（デフォルト: "import"）
            source_session: リトライ元セッション ID（リトライ時のみ）
            folder_manager: フォルダ管理オブジェクト（新構造使用時）
        """
        self.provider = provider
        self.total_files = total_files
        self.prefix = prefix
        self.source_session = source_session
        self.folder_manager = folder_manager
        self._session_dir: Path | None = None
        self._session_paths: dict[str, Path] = {}

        # 内部状態リスト (US3)
        self._processed: list[dict] = []
        self._errors: list[dict] = []
        self._pending: list[dict] = []

        # Phase 別カウント
        self._phase1_completed = 0
        self._phase2_completed = 0

    @property
    def session_dir(self) -> Path | None:
        """セッションディレクトリのパス（開始前は None）"""
        return self._session_dir

    def get_paths(self) -> dict[str, Path]:
        """セッションのサブディレクトリパスを取得

        Returns:
            パス辞書。キー:
            - "session": セッションルート
            - "parsed": parsed/conversations/ (import のみ)
            - "output": output/ (import のみ)
            - "errors": errors/ (import のみ)
        """
        return self._session_paths

    @property
    def stats(self) -> dict[str, int]:
        """現在の統計情報"""
        return {
            "success": len(self._processed),
            "error": len(self._errors),
            "pending": len(self._pending),
        }

    def start_session(self) -> Path:
        """セッションを開始し、初期ファイルを作成する

        Returns:
            セッションディレクトリのパス

        Side Effects:
            - folder_manager がある場合: @session/{type}/{session_id}/ を作成
            - folder_manager がない場合: @session/{prefix}_YYYYMMDD_HHMMSS/ を作成（レガシー）
            - session.json を作成
            - execution.log を作成（ヘッダー書き込み）
        """
        try:
            # 新しいフォルダ構造（folder_manager がある場合）
            if self.folder_manager:
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._session_paths = self.folder_manager.create_session_structure(
                    self.prefix, session_id
                )
                self._session_dir = self._session_paths["session"]
            else:
                # レガシー構造（後方互換性）
                self._session_dir = create_new_session(prefix=self.prefix)
                self._session_paths = {"session": self._session_dir}

            # session.json を作成
            session_data = {
                "session_id": self._session_dir.name,
                "session_type": self.prefix,
                "started_at": timestamp(),
                "updated_at": timestamp(),
                "total_files": self.total_files,
                "provider": self.provider,
            }
            # リトライセッションの場合は source_session を追加
            if self.source_session:
                session_data["source_session"] = self.source_session
            session_file = self._session_dir / "session.json"
            session_file.write_text(
                json.dumps(session_data, ensure_ascii=False, indent=2)
            )

            # execution.log にヘッダーを書き込み
            log_file = get_log_file(self._session_dir)
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"  LLM Import - 処理開始 [{self.provider}]\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"処理対象: {self.total_files} 会話\n")
                f.write(f"セッション: {self._session_dir}\n")
                f.write(f"開始時刻: {timestamp()}\n\n")

        except Exception as e:
            # graceful degradation: エラー時は警告のみ
            print(f"⚠️ セッション作成エラー: {e}")
            self._session_dir = None

        return self._session_dir

    def log(self, message: str, also_print: bool = True) -> None:
        """ログメッセージを記録する

        Args:
            message: ログメッセージ
            also_print: コンソールにも出力するか（デフォルト: True）

        Side Effects:
            - execution.log に追記
            - also_print=True の場合、コンソールにも出力
        """
        try:
            if self._session_dir is not None:
                log_message(message, self._session_dir, also_print=also_print)
            elif also_print:
                print(message)
        except Exception:
            # graceful degradation
            if also_print:
                print(message)

    def log_progress(
        self,
        current: int,
        title: str,
        phase1_ok: bool,
        phase2_ok: bool | None,
        elapsed_sec: float,
        also_print: bool = True,
    ) -> None:
        """進捗を記録・表示する

        Args:
            current: 現在の処理番号（1-indexed）
            title: 会話タイトル
            phase1_ok: Phase 1 成功したか
            phase2_ok: Phase 2 成功したか（None = 未実行）
            elapsed_sec: この会話の処理時間（秒）
            also_print: コンソールにも出力するか

        Side Effects:
            - コンソールにプログレスバーと結果を表示
            - execution.log に記録
        """
        # プログレスバー
        bar = progress_bar(current, self.total_files)

        # Phase ステータス
        p1_status = "✅" if phase1_ok else "❌"
        if phase2_ok is None:
            p2_status = "⏭️"
        elif phase2_ok:
            p2_status = "✅"
        else:
            p2_status = "❌"

        # タイトルを短縮（長すぎる場合）
        max_title_len = 30
        display_title = title[:max_title_len] + "..." if len(title) > max_title_len else title

        # 進捗メッセージ
        progress_msg = f"[{current}/{self.total_files}] {display_title} Phase1 {p1_status} Phase2 {p2_status} ({elapsed_sec:.1f}s)"

        # ログ出力
        self.log(bar, also_print=also_print)
        self.log(progress_msg, also_print=also_print)

    def log_stage(
        self,
        filename: str,
        stage: str,
        timing_ms: int,
        skipped_reason: str | None = None,
        before_chars: int | None = None,
        after_chars: int | None = None,
        file_id: str | None = None,
    ) -> None:
        """処理ステージを記録する (US2)

        Args:
            filename: 処理対象のファイル名/会話タイトル
            stage: ステージ名（"phase1" | "phase2"）
            timing_ms: 処理時間（ミリ秒）
            skipped_reason: スキップ理由（None=実行済み）
            before_chars: 処理前の文字数（Phase 2のみ）
            after_chars: 処理後の文字数（Phase 2のみ）
            file_id: ファイル追跡用ID（12文字の16進数ハッシュ）

        Side Effects:
            - pipeline_stages.jsonl に追記
        """
        if self._session_dir is None:
            return

        try:
            record = {
                "timestamp": timestamp(),
                "filename": filename,
                "stage": stage,
                "timing_ms": timing_ms,
                "skipped_reason": skipped_reason,
            }

            # file_id（指定された場合のみ）
            if file_id is not None:
                record["file_id"] = file_id

            # 差分情報（Phase 2で指定された場合のみ）
            if before_chars is not None and after_chars is not None:
                record["before_chars"] = before_chars
                record["after_chars"] = after_chars
                if before_chars > 0:
                    record["diff_ratio"] = (after_chars - before_chars) / before_chars
                else:
                    record["diff_ratio"] = 0.0

            jsonl_file = self._session_dir / "pipeline_stages.jsonl"
            with open(jsonl_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            # Phase カウント更新（スキップされなかった場合）
            if skipped_reason is None:
                if stage == "phase1":
                    self._phase1_completed += 1
                elif stage == "phase2":
                    self._phase2_completed += 1

        except Exception as e:
            # graceful degradation
            print(f"⚠️ ステージログエラー: {e}")

    def add_processed(self, file: str, output: str) -> None:
        """処理成功を記録する (US3)

        Args:
            file: ファイル名/会話ID
            output: 出力先パス
        """
        self._processed.append({
            "file": file,
            "status": "success",
            "output": output,
            "timestamp": timestamp(),
        })

    def add_error(self, file: str, error: str, stage: str) -> None:
        """エラーを記録する (US3)

        Args:
            file: ファイル名/会話ID
            error: エラーメッセージ
            stage: エラー発生ステージ
        """
        self._errors.append({
            "file": file,
            "error": error,
            "stage": stage,
            "timestamp": timestamp(),
        })

    def add_pending(self, file: str, reason: str) -> None:
        """未処理を記録する (US3)

        Args:
            file: ファイル名/会話ID
            reason: 未処理理由
        """
        self._pending.append({
            "file": file,
            "reason": reason,
        })

    def finalize(self, elapsed_seconds: float, also_print: bool = True) -> None:
        """セッションを終了し、最終結果を記録する (US3)

        Args:
            elapsed_seconds: 総処理時間（秒）
            also_print: コンソールにサマリーを表示するか

        Side Effects:
            - processed.json を書き込み
            - errors.json を書き込み
            - pending.json を書き込み
            - results.json を書き込み
            - execution.log にサマリーを追記
            - コンソールにサマリーを表示
        """
        if self._session_dir is None:
            return

        try:
            # 状態ファイルを書き込み
            self._write_json("processed.json", self._processed)
            self._write_json("errors.json", self._errors)
            self._write_json("pending.json", self._pending)

            # results.json を作成
            success_count = len(self._processed)
            error_count = len(self._errors)
            pending_count = len(self._pending)
            total = success_count + error_count + pending_count

            avg_time = elapsed_seconds / total if total > 0 else 0

            results = {
                "total": self.total_files,
                "success": success_count,
                "error": error_count,
                "pending": pending_count,
                "skipped": 0,  # 将来用
                "phase1_completed": self._phase1_completed,
                "phase2_completed": self._phase2_completed,
                "elapsed_seconds": elapsed_seconds,
                "avg_time_per_conversation": avg_time,
            }
            self._write_json("results.json", results)

            # 中間ファイル情報を収集 (T029)
            intermediate_files = self._collect_intermediate_files()

            # session.json を更新
            session_file = self._session_dir / "session.json"
            if session_file.exists():
                session_data = json.loads(session_file.read_text())
                session_data["updated_at"] = timestamp()
                session_data["intermediate_files"] = intermediate_files
                session_file.write_text(
                    json.dumps(session_data, ensure_ascii=False, indent=2)
                )

            # サマリーを出力
            self._display_summary(results, elapsed_seconds, also_print)

        except Exception as e:
            print(f"⚠️ finalize エラー: {e}")

    def _collect_intermediate_files(self) -> dict:
        """中間ファイル情報を収集する (T029)

        Returns:
            中間ファイル情報の辞書:
            - parsed_count: parsed/ のファイル数
            - output_count: output/ のファイル数
            - parsed_files: parsed/ のファイルリスト
            - output_files: output/ のファイルリスト
        """
        result = {
            "parsed_count": 0,
            "output_count": 0,
            "parsed_files": [],
            "output_files": [],
        }

        if not self._session_paths:
            return result

        # parsed/ のファイルをカウント
        parsed_dir = self._session_paths.get("parsed")
        if parsed_dir and parsed_dir.exists():
            parsed_files = list(parsed_dir.glob("*.md"))
            result["parsed_count"] = len(parsed_files)
            result["parsed_files"] = [f.name for f in parsed_files]

        # output/ のファイルをカウント
        output_dir = self._session_paths.get("output")
        if output_dir and output_dir.exists():
            output_files = list(output_dir.glob("*.md"))
            result["output_count"] = len(output_files)
            result["output_files"] = [f.name for f in output_files]

        return result

    def _write_json(self, filename: str, data: dict | list) -> None:
        """JSON ファイルを書き込む"""
        if self._session_dir is None:
            return
        filepath = self._session_dir / filename
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _display_summary(
        self, results: dict, elapsed_seconds: float, also_print: bool
    ) -> None:
        """サマリーを表示・記録する"""
        # 時間フォーマット
        hours, remainder = divmod(int(elapsed_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            time_str = f"{hours}時間{minutes}分{seconds}秒"
        elif minutes > 0:
            time_str = f"{minutes}分{seconds}秒"
        else:
            time_str = f"{seconds}秒"

        lines = [
            "",
            "=" * 60,
            f"  LLM Import - 処理結果 [{self.provider}]",
            "=" * 60,
            "",
            "📊 処理結果サマリー",
            f"  ✅ 成功: {results['success']}",
            f"  ❌ エラー: {results['error']}",
            f"  📋 Phase 2 未処理: {results['pending']}",
            "",
            "📁 Phase 別内訳",
            f"  Phase 1 完了: {results['phase1_completed']}",
            f"  Phase 2 完了: {results['phase2_completed']}",
            "",
            "⏱️  処理時間",
            f"  総時間: {time_str}",
            f"  平均: {results['avg_time_per_conversation']:.1f}秒/会話",
            "",
            "📂 出力先",
            f"  セッションログ: {self._session_dir}",
            "",
        ]

        for line in lines:
            self.log(line, also_print=also_print)
