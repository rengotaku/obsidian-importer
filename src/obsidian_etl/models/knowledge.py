"""LLM ナレッジ抽出結果の構造体。

バリデーション内蔵の dataclass。フィールド追加だけで
自動的にバリデーション対象になる。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


class LLMFieldValidationError(Exception):
    """LLM レスポンスの必須フィールドが空の場合に発生。"""

    def __init__(self, missing_fields: list[str]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"LLM returned empty fields: {', '.join(missing_fields)}")


@dataclass(frozen=True)
class LLMKnowledge:
    """LLM が返すナレッジの構造体。

    全フィールドが自動バリデーション対象。
    str フィールド: 空文字列・空白のみで検出
    list フィールド: 空リストで検出
    フィールドを追加するだけで検証される。
    """

    title: str
    summary: str
    summary_content: str
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """構築時に全フィールドを自動バリデーション。"""
        missing = []
        for f in fields(self):
            value = getattr(self, f.name)
            if (isinstance(value, str) and (not value or not value.strip())) or (
                isinstance(value, list) and not value
            ):
                missing.append(f.name)
        if missing:
            raise LLMFieldValidationError(missing)

    def to_generated_metadata(self) -> dict[str, Any]:
        """generated_metadata 形式の dict を返す。"""
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> LLMKnowledge:
        """dict から LLMKnowledge を構築。バリデーション発火。"""
        return LLMKnowledge(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            summary_content=data.get("summary_content", ""),
            tags=data.get("tags", []),
        )

    def with_summary(self, new_summary: str) -> LLMKnowledge:
        """summary を差し替えた新しいインスタンスを返す（イミュータブル対応）。"""
        return LLMKnowledge(
            title=self.title,
            summary=new_summary,
            summary_content=self.summary_content,
            tags=list(self.tags),
        )
