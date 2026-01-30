"""
llm_import.common.state - 処理状態管理

処理済み会話の追跡と状態ファイルの読み書きを行う。
プロバイダーごとに独立した状態ファイルを管理。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ProcessedEntry:
    """
    処理済みエントリ

    Attributes:
        id: 会話ID（プロバイダー固有）
        provider: プロバイダー名
        input_file: Phase 1 出力ファイルパス
        output_file: Phase 2 出力ファイルパス
        processed_at: 処理日時（ISO 8601）
        status: "success" | "skipped" | "error"
        skip_reason: スキップ理由（status=skipped の場合）
        error_message: エラーメッセージ（status=error の場合）
        file_id: ファイル追跡用ハッシュID（12文字16進数）
    """
    id: str
    provider: str
    input_file: str
    output_file: str
    processed_at: str
    status: str  # "success" | "skipped" | "error"
    skip_reason: str | None = None
    error_message: str | None = None
    file_id: str | None = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ProcessedEntry:
        """辞書から生成（後方互換性を考慮）"""
        return cls(
            id=data["id"],
            provider=data["provider"],
            input_file=data["input_file"],
            output_file=data["output_file"],
            processed_at=data["processed_at"],
            status=data["status"],
            skip_reason=data.get("skip_reason"),
            error_message=data.get("error_message"),
            file_id=data.get("file_id"),
        )


@dataclass
class ProcessingState:
    """
    処理状態

    Attributes:
        provider: プロバイダー名
        processed_conversations: ID → ProcessedEntry のマッピング
        last_run: 最終実行日時（ISO 8601）
        version: 状態ファイルバージョン
    """
    provider: str
    processed_conversations: dict[str, ProcessedEntry] = field(default_factory=dict)
    last_run: str = ""
    version: str = "1.0"

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "version": self.version,
            "provider": self.provider,
            "last_run": self.last_run,
            "processed_conversations": {
                k: v.to_dict() for k, v in self.processed_conversations.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProcessingState:
        """辞書から生成"""
        conversations = {
            k: ProcessedEntry.from_dict(v)
            for k, v in data.get("processed_conversations", {}).items()
        }
        return cls(
            provider=data.get("provider", "unknown"),
            processed_conversations=conversations,
            last_run=data.get("last_run", ""),
            version=data.get("version", "1.0"),
        )


# =============================================================================
# State Manager
# =============================================================================


class StateManager:
    """
    状態ファイルの読み書きを管理

    状態ファイルの配置:
        @index/llm_exports/{provider}/.extraction_state.json
    """

    def __init__(self, provider: str, base_dir: Path):
        """
        Args:
            provider: プロバイダー名（例: 'claude'）
            base_dir: ベースディレクトリ（例: @index/llm_exports/）
        """
        self.provider = provider
        self.base_dir = base_dir
        self.state_file = base_dir / provider / ".extraction_state.json"
        self._state: ProcessingState | None = None

    @property
    def state(self) -> ProcessingState:
        """現在の状態を取得（遅延ロード）"""
        if self._state is None:
            self._state = self.load()
        return self._state

    def load(self) -> ProcessingState:
        """
        状態ファイルを読み込む

        Returns:
            ProcessingState（ファイルがなければ新規作成）
        """
        if not self.state_file.exists():
            return ProcessingState(provider=self.provider)

        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
            return ProcessingState.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  状態ファイル読み込みエラー: {e}")
            return ProcessingState(provider=self.provider)

    def save(self) -> None:
        """状態ファイルを保存"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state.last_run = datetime.now().isoformat()

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)

    def is_processed(self, conversation_id: str) -> bool:
        """
        会話が処理済みかどうかを確認

        Args:
            conversation_id: 会話ID

        Returns:
            処理済みなら True
        """
        return conversation_id in self.state.processed_conversations

    def get_entry(self, conversation_id: str) -> ProcessedEntry | None:
        """
        処理済みエントリを取得

        Args:
            conversation_id: 会話ID

        Returns:
            ProcessedEntry または None
        """
        return self.state.processed_conversations.get(conversation_id)

    def add_entry(
        self,
        conversation_id: str,
        input_file: str,
        output_file: str,
        status: str,
        skip_reason: str | None = None,
        error_message: str | None = None,
        file_id: str | None = None,
    ) -> None:
        """
        処理済みエントリを追加

        Args:
            conversation_id: 会話ID
            input_file: Phase 1 出力ファイルパス
            output_file: Phase 2 出力ファイルパス
            status: "success" | "skipped" | "error"
            skip_reason: スキップ理由
            error_message: エラーメッセージ
            file_id: ファイル追跡用ハッシュID（12文字16進数）
        """
        entry = ProcessedEntry(
            id=conversation_id,
            provider=self.provider,
            input_file=input_file,
            output_file=output_file,
            processed_at=datetime.now().isoformat(),
            status=status,
            skip_reason=skip_reason,
            error_message=error_message,
            file_id=file_id,
        )
        self.state.processed_conversations[conversation_id] = entry

    def reset(self) -> None:
        """状態をリセット"""
        self._state = ProcessingState(provider=self.provider)
        if self.state_file.exists():
            self.state_file.unlink()

    def get_stats(self) -> dict[str, int]:
        """
        処理統計を取得

        Returns:
            {"total": N, "success": N, "skipped": N, "error": N}
        """
        stats = {"total": 0, "success": 0, "skipped": 0, "error": 0}
        for entry in self.state.processed_conversations.values():
            stats["total"] += 1
            if entry.status in stats:
                stats[entry.status] += 1
        return stats

    def get_errors(self) -> list[ProcessedEntry]:
        """
        エラーエントリのリストを取得

        Returns:
            エラー状態のエントリリスト
        """
        return [
            entry
            for entry in self.state.processed_conversations.values()
            if entry.status == "error"
        ]
