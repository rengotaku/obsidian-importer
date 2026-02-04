# Research: Extract Stage Discovery 委譲

**Date**: 2026-01-23
**Feature**: 031-extract-discovery-delegation

## Overview

本機能は既存コードベースの内部リファクタリングであり、外部技術の調査は不要。
以下は既存実装の分析結果。

## Existing Implementation Analysis

### 1. ChatGPTExtractor.discover_items()

**場所**: `src/etl/stages/extract/chatgpt_extractor.py:203-344`

**機能**:
- ZIP ファイルから conversations.json を読み込み
- ChatGPT の mapping ツリー構造を走査
- メッセージを時系列順に抽出
- Claude 互換フォーマット（chat_messages 配列）に変換
- ProcessingItem を生成して返却

**既に実装済み** - 変更不要

### 2. ImportPhase.discover_items()

**場所**: `src/etl/phases/import_phase.py:125-310`

**機能**:
- conversations.json を直接読み込み（Claude 形式専用）
- chat_messages 配列を期待
- チャンキング処理（25000 文字超で分割）
- source_provider をメタデータに設定

**移植対象** - ClaudeExtractor に移動

### 3. BaseStage.run()

**場所**: `src/etl/core/stage.py:254-317`

**シグネチャ**:
```python
def run(self, ctx: StageContext, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
```

**変更方針**: シグネチャは変更しない。ImportPhase が discover_items() を呼び出してから run() に渡す。

## Design Decisions

### Decision 1: discover 委譲方式

**選択**: ImportPhase が Extract stage の discover_items() を呼び出す

**理由**:
- BaseStage.run() のシグネチャ変更を避ける
- Transform/Load stage への影響なし
- テストの変更量を最小化

**却下した代替案**:
- BaseStage.run() を items=None 許容に変更 → 影響範囲が大きすぎる
- Extract stage だけ run() をオーバーライド → 一貫性がない

### Decision 2: チャンキングロジックの配置

**選択**: ClaudeExtractor.discover_items() 内に移植

**理由**:
- チャンキングは discover フェーズの責務
- provider ごとの違いを吸収
- 単一責任の原則に従う

### Decision 3: provider 必須化

**選択**: --provider オプションを必須とし、省略時はエラー

**理由**:
- 自動検出の複雑さを避ける
- 明示的な指定によるミス防止
- 将来の拡張が容易

## Conclusion

外部調査は不要。既存実装の移植とリファクタリングで対応可能。
主要なリスクは既存テストの破壊だが、段階的な変更で対処する。
