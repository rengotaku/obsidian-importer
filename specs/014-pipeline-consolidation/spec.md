# Feature Specification: Normalizer Pipeline統合

**Feature Branch**: `014-pipeline-consolidation`
**Created**: 2026-01-15
**Status**: Draft
**Input**: User description: "Normalizer Pipeline統合: LLM呼び出し回数を5回から3回に削減し処理時間を短縮"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - パイプライン処理時間の短縮 (Priority: P1)

ユーザーが`/og:organize`コマンドで@indexフォルダ内のファイルを整理する際、現在の5回のLLM呼び出しが3回に統合されることで、処理時間が大幅に短縮される。

**Why this priority**: LLM呼び出しが処理時間のボトルネック。5回→3回の削減で40%の時間短縮が期待される。

**Independent Test**: 単一ファイルの正規化処理で、LLM呼び出し回数が3回であることを確認し、処理時間が以前より短縮されていることを計測できる。

**Acceptance Scenarios**:

1. **Given** @indexに未整理ファイルがある, **When** パイプラインを実行, **Then** LLM呼び出しは3回のみで完了する
2. **Given** Stage Aで"dust"判定されたファイル, **When** 処理継続, **Then** Stage B/Cはスキップされ、LLM呼び出しは1回のみ
3. **Given** 通常のファイル, **When** パイプライン完了, **Then** genre、subfolder、title、tags、summary、relatedが全て生成される

---

### User Story 2 - Stage A: 分類判定の統合 (Priority: P1)

従来のStage 1（Dust判定）とStage 2（ジャンル分類）を1回のLLM呼び出しで同時実行する。価値なしと判定された場合はdustとして処理終了、価値ありの場合はジャンルとサブフォルダを返す。

**Why this priority**: 2回のLLM呼び出しを1回に統合することで最大の効率化が得られる。

**Independent Test**: Stage Aのみを実行し、dust判定とジャンル分類が1回の呼び出しで正しく返されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 価値のないコンテンツ, **When** Stage Aを実行, **Then** `genre: "dust"`と`reason`が返される
2. **Given** 技術文書, **When** Stage Aを実行, **Then** `genre: "エンジニア"`と適切な`subfolder`が返される
3. **Given** 判断困難なコンテンツ, **When** Stage Aを実行, **Then** `genre: "unknown"`と`confidence: "low"`が返される

---

### User Story 3 - Stage C: メタデータ+Summary統合 (Priority: P1)

従来のStage 4（タイトル・タグ生成）とStage 5（Summary品質改善）を1回のLLM呼び出しで同時実行する。relatedフィールドも同時に生成する。

**Why this priority**: 出力フォーマットの統合により、一貫性のあるメタデータ生成が可能になる。

**Independent Test**: Stage Cのみを実行し、title、tags、summary、relatedが全て正しく生成されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 正規化済みコンテンツ, **When** Stage Cを実行, **Then** title、tags、summary、relatedが全て含まれるJSONが返される
2. **Given** AWSに関する技術文書, **When** Stage Cを実行, **Then** relatedに`["[[S3]]", "[[EC2]]"]`のような内部リンク形式が含まれる
3. **Given** summaryが2-3行以内, **When** frontmatterを生成, **Then** `summary:`プロパティとして定義され、Dataviewクエリで参照可能

---

### User Story 4 - Ollamaコンテキスト長の拡張 (Priority: P2)

gpt-oss:20bモデルのコンテキスト長をデフォルトの4096から16384に拡張し、長いドキュメントの処理精度を向上させる。

**Why this priority**: 長文ドキュメントでの切り捨てによる情報損失を防ぐ。処理精度向上に寄与。

**Independent Test**: 4000文字以上のドキュメントを処理し、コンテンツが切り捨てられずに正しく処理されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 10000文字のドキュメント, **When** Stage Bを実行, **Then** 全文が処理され、情報損失なく正規化される
2. **Given** Ollama API呼び出し, **When** リクエスト送信, **Then** `num_ctx: 16384`がオプションに含まれる

---

### Edge Cases

- Stage Aで`genre: "dust"`が返された場合
  - → `@dust`フォルダに配置
- Stage Aで`genre: "unknown"`が返された場合
  - → `@review`フォルダに配置（手動レビュー待ち）
- Stage Cでrelated候補が見つからない場合は？
  - → 空配列`[]`を返す（エラーではない）
- LLM応答がJSON形式でない場合は？
  - → 既存のリトライロジック（最大3回）を維持

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: パイプラインはLLM呼び出しを3回以内で完了しなければならない（Stage A, B, C）
- **FR-002**: Stage AはDust判定とジャンル分類を1回のLLM呼び出しで同時実行しなければならない
- **FR-003**: Stage Aの出力は`genre`、`subfolder`、`confidence`、`reason`を含まなければならない
- **FR-004**: Stage Bは既存のStage 3（Markdown正規化）を維持する
- **FR-005**: Stage Cはtitle、tags、summary（frontmatterプロパティ）、relatedを1回のLLM呼び出しで生成しなければならない
- **FR-006**: `related`フィールドはObsidian内部リンク形式`[["ファイル名"]]`で出力しなければならない
- **FR-007**: Ollama API呼び出し時に`num_ctx: 16384`を指定しなければならない
- **FR-008**: Dust判定時（Stage Aで`genre: "dust"`）はStage B/Cをスキップし、`@dust`フォルダに配置しなければならない
- **FR-009**: `genre: "unknown"`の場合は`@review`フォルダに配置しなければならない
- **FR-010**: 既存のpre_process（ルールベース前処理）とpost_process（結果統合）は維持する

### Key Entities

- **StageAResult**: genre, subfolder, confidence, reason
- **StageBResult**: normalized_content, improvements_made（既存Stage3Resultと同等）
- **StageCResult**: title, tags, summary, related
- **Frontmatter**: title, tags, created, summary（プロパティとして定義）, related

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 単一ファイルの処理でLLM呼び出しが3回以下であること
- **SC-002**: Dust判定時はLLM呼び出しが1回のみであること
- **SC-004**: 生成されるfrontmatterにtitle、tags、summary（プロパティ）、relatedが全て含まれること
- **SC-005**: relatedフィールドが内部リンク形式`[["ファイル名"]]`であること
- **SC-006**: 4000文字以上のドキュメントが情報損失なく処理されること

## Open Questions

- ~~**OQ-001**: gpt-oss:20bモデルが16384トークンのコンテキスト長をサポートするか~~ → **解決済み**: 128K (131072) サポート確認

## Assumptions
- 統合プロンプトでも各ステージと同等の品質を維持できる
- 既存のリトライロジック（最大3回）は各ステージで維持する
- summaryは**最大200文字**の簡潔な形式とする
- relatedは最大5件程度とする

## Testing Strategy

- 既存の`normalizer/tests/`配下のテスト構造を流用
- 項目ごと（title、tags、正規化など）のチェックを維持
- Stage A/B/C用にテストケースを追加・調整

## Out of Scope

- カスタムOllamaモデルの作成（Modelfileによる`num_ctx`固定化）
- ユーザー確認フロー（`unknown`判定時のインタラクティブ確認）
- 処理時間ベンチマーク（改善の検証は手動）
- 新規テストフレームワークの導入
