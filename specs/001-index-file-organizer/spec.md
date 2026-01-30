# Feature Specification: Index File Organizer

**Feature Branch**: `001-index-file-organizer`
**Created**: 2026-01-09
**Status**: Approved
**Input**: User description: "@index に置かれたファイルを精査、整形してvault内に適切に配置するフロー"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 単一ファイルの整理 (Priority: P1)

ユーザーは `@index/` に置かれた1つのファイルを、内容に基づいて適切な Vault に整理したい。ファイルは Obsidian 規約に従って整形され、正しいジャンルのフォルダに配置される。

**Why this priority**: 最も基本的な機能であり、これが動作しなければ他の機能も意味をなさない。MVP として単一ファイル処理ができれば価値を提供できる。

**Independent Test**: `@index/` に1つのテストファイルを置き、整理コマンドを実行して、正しい Vault に正規化された状態で配置されることを確認する。

**Acceptance Scenarios**:

1. **Given** `@index/` に技術的な内容のファイルがある, **When** 整理を実行, **Then** ファイルは `エンジニア/` に移動され、frontmatter が追加される
2. **Given** `@index/` にビジネス書の要約ファイルがある, **When** 整理を実行, **Then** ファイルは `ビジネス/` に移動され、正規化される
3. **Given** Jekyll形式のファイル名（`2022-10-17-Title.md`）がある, **When** 整理を実行, **Then** ファイル名は `Title.md` に変換される

---

### User Story 2 - 複数ファイルの一括整理 (Priority: P2)

ユーザーは `@index/` 内の複数ファイルをまとめて整理したい。各ファイルは個別に分類・整形され、それぞれ適切な Vault に配置される。

**Why this priority**: 実用的な運用では複数ファイルを一度に処理することが多い。P1 の機能を拡張する形で実装可能。

**Independent Test**: `@index/` に異なるジャンルの3つのファイルを置き、一括整理を実行して、それぞれが正しい Vault に配置されることを確認する。

**Acceptance Scenarios**:

1. **Given** `@index/` に5つの未整理ファイルがある, **When** 一括整理を実行, **Then** 各ファイルはジャンルに応じた Vault に移動される
2. **Given** 処理対象のファイルが10個以上ある, **When** 一括整理を実行, **Then** 処理前に確認プロンプトが表示される
3. **Given** 一括処理中にエラーが発生, **When** 1つのファイルで失敗, **Then** 残りのファイルは処理を継続し、エラーは最後にまとめて報告される

---

### User Story 3 - 整理結果のプレビュー (Priority: P3)

ユーザーは実際にファイルを移動する前に、どのファイルがどこに配置されるかをプレビューしたい。これにより誤分類を事前に発見・修正できる。

**Why this priority**: 安全性を高める機能だが、基本機能が動作してから追加すべき。

**Independent Test**: プレビューモードで実行し、ファイルが移動されずに分類結果のみが表示されることを確認する。

**Acceptance Scenarios**:

1. **Given** `@index/` に複数のファイルがある, **When** プレビューモードで実行, **Then** 各ファイルの移動先が一覧表示され、実際の移動は行われない
2. **Given** プレビュー結果を確認した, **When** ユーザーが承認, **Then** プレビュー通りにファイルが移動される
3. **Given** プレビュー結果に誤りがある, **When** ユーザーが手動で分類を変更, **Then** 変更された分類で移動が実行される

---

### Edge Cases

- `@index/` が空の場合: 「整理対象のファイルがありません」と通知
- 既に正規化済み（`normalized: true`）のファイル: スキップして通知
- 同名ファイルが移動先に存在: 番号を付与して重複を回避（`Title.md` → `Title_1.md`）
- frontmatter が壊れているファイル: エラーとして報告し、手動対応を促す
- バイナリファイルや非 Markdown ファイル: スキップして通知
- `@index/claude/` 内のファイル: Claude エクスポートデータ専用のため除外
- **価値なしと判断されたファイル**: Ollama が「意味不明な文字列」「テスト投稿」等と判定した場合、`@dust/` フォルダに振り分け
- **処理中断からの再開**: 状態ファイルを参照し、処理済みファイルをスキップして続行

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `@index/` 内の Markdown ファイル（`.md`）を検出できなければならない
- **FR-002**: システムはファイル内容を解析し、5つのジャンル（エンジニア、ビジネス、経済、日常、その他）のいずれかに分類できなければならない
- **FR-003**: システムはファイルを Obsidian 規約に従って正規化できなければならない（YAML frontmatter 追加、内部リンク変換、空行整理）
- **FR-004**: システムは正規化後のファイルを適切な Vault に移動できなければならない
- **FR-005**: システムは移動したファイルへの参照（内部リンク）を自動更新できなければならない
- **FR-006**: システムは `ClaudedocKnowledges/` への自動振り分けを禁止しなければならない
- **FR-007**: システムは処理結果（成功/失敗/スキップ）をユーザーに報告しなければならない
- **FR-008**: システムは10個以上のファイルを処理する前にユーザー確認を求めなければならない
- **FR-009**: システムは Ollama が「価値なし」と判定したファイル（意味不明、テスト投稿等）を `@dust/` フォルダに振り分けなければならない
- **FR-010**: システムは処理状態を記録し、中断後も再開可能でなければならない

### Key Entities

- **Index File**: `@index/` に置かれた未整理の Markdown ファイル。タイトル、内容、現在のパスを持つ
- **Genre**: ファイルの分類カテゴリ。エンジニア、ビジネス、経済、日常、その他、dust の6種類
- **Vault**: ジャンルに対応する保存先ディレクトリ。それぞれ独自の構造を持つ
- **Dust Folder**: Ollama が「価値なし」と判定したファイルの隔離先。削除候補として一時保管
- **Normalization State**: ファイルの正規化状態。frontmatter の `normalized` フィールドで管理

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーは1ファイルあたり5秒以内に整理を完了できる（手動作業の90%削減）
- **SC-002**: ジャンル分類の精度は90%以上を達成する（10ファイル中9ファイル以上が正しい Vault に配置）
- **SC-003**: 正規化されたファイルは100% Obsidian 規約に準拠する（frontmatter 必須フィールド完備）
- **SC-004**: `@index/` 内のファイル数を週次で50%以上削減できる運用が可能になる
- **SC-005**: 処理エラー発生時も既存ファイルのデータ損失は0件を維持する

## Architecture

### 役割分担（トークン効率化設計）

| コンポーネント | 役割 | 処理内容 |
|---------------|------|---------|
| **Claude Code** | 起動のみ | スクリプト実行 + 結果表示 |
| **Python Script** | オーケストレーター | ファイル操作、Ollama呼び出し、キーワードマッチング、移動処理 |
| **Ollama** (`gpt-oss:20b`) | コンテンツ処理 | ジャンル分類（dust含む）、キーワード抽出、正規化（frontmatter生成） |

### 処理フロー

```
Claude Code: スクリプト起動
    ↓
Python Script (ollama_normalizer.py):
    for each file in @index/:
        1. ファイル読み込み
        2. Ollama API 呼び出し:
           - ジャンル判定（エンジニア/ビジネス/経済/日常/その他/dust）
           - 関連キーワード抽出
           - frontmatter 生成 + 本文整形
        3. [genre == "dust"?] → @dust/ へ移動
        4. キーワード → 既存ファイル名マッチング → related 生成
        5. 正規化済みファイルを Vault へ移動
    ↓
    結果JSON出力
    ↓
Claude Code: 結果表示
```

### Ollama 出力形式

```json
{
  "genre": "エンジニア",
  "confidence": 0.9,
  "is_dust": false,
  "dust_reason": null,
  "related_keywords": ["AWS", "IAM", "セキュリティ"],
  "frontmatter": {
    "title": "AWS IAM の基礎",
    "tags": ["AWS", "セキュリティ", "IAM"],
    "created": "2026-01-09"
  },
  "normalized_content": "..."
}
```

### 既存資産

- `.claude/scripts/ollama_genre_classifier.py`: ジャンル分類スクリプト（拡張して使用）
- Ollama API: `http://localhost:11434/api/chat`
- 確信度閾値: 0.7 以上で自動移動、未満は要確認

## Assumptions

- ファイルの内容は日本語または英語で記述されている
- ジャンル判定・正規化はローカル LLM（Ollama `gpt-oss:20b`）が処理し、Claude Code はワークフロー管理のみ担当
- 移動先の Vault フォルダ構造は既に存在する
- Ollama サーバーが `localhost:11434` で稼働している
- 大量ファイル処理時のトークン消費を抑えるため、コンテンツ解析は Ollama に委譲する
