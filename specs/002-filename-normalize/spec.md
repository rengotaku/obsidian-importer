# Feature Specification: Filename Normalize

**Feature Branch**: `002-filename-normalize`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User description: "/og:organize を実行すると、2022-10-7-Pull-a-docker-image-from-Elastic-Container-Reposit_1.md のように日付をファイルに含めるのだがやめたい。またタイトルがハイフン区切りで適切ではない。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 日付なしのファイル名で整理 (Priority: P1)

ユーザーが `/og:organize` コマンドを実行すると、元ファイル名に含まれるJekyll形式の日付プレフィックス（例：`2022-10-7-`）が出力ファイル名から除去され、クリーンなファイル名で保存される。

**Why this priority**: ファイル名の可読性と検索性に直接影響する基本機能。日付プレフィックスはObsidianの作成日プロパティで管理すべきであり、ファイル名に含める必要がない。

**Independent Test**: `@index/2022-10-7-Test-Article.md` を処理し、出力ファイル名に日付が含まれないことを確認できる。

**Acceptance Scenarios**:

1. **Given** `@index/2022-10-7-Pull-a-docker-image.md` が存在する, **When** `/og:organize` を実行, **Then** 出力ファイル名は `Pull a docker image.md` となる（日付なし、スペース区切り）
2. **Given** `@index/2022_10_17_Another-Test.md` が存在する, **When** `/og:organize` を実行, **Then** 出力ファイル名は `Another Test.md` となる（アンダースコア形式の日付も除去）
3. **Given** `@index/NoDate-Just-Title.md` が存在する, **When** `/og:organize` を実行, **Then** 出力ファイル名は `NoDate Just Title.md` となる（日付がない場合もハイフンをスペースに変換）

---

### User Story 2 - 人間が読みやすいタイトルへの変換 (Priority: P1)

ファイル名のハイフン区切り（`Pull-a-docker-image`）を人間が読みやすい形式（`Pull a docker image`）に変換する。

**Why this priority**: ハイフン区切りのファイル名はURL向けのスラグ形式であり、Obsidianナレッジベースでは不適切。自然な日本語タイトルまたは英語タイトルが望ましい。

**Independent Test**: ハイフン区切りのファイル名を処理し、スペース区切りまたは適切な日本語タイトルに変換されることを確認できる。

**Acceptance Scenarios**:

1. **Given** ファイル名が `Pull-a-docker-image-from-ECR.md`, **When** 正規化処理を実行, **Then** ファイル名は `Pull a docker image from ECR.md` となる
2. **Given** ファイル名が `AWS-Cloud-Practitioner.md`, **When** 正規化処理を実行, **Then** ファイル名は `AWS Cloud Practitioner.md` となる（頭字語は保持）
3. **Given** ファイル名が `日本語タイトル.md`, **When** 正規化処理を実行, **Then** ファイル名は `日本語タイトル.md` のまま維持される

---

### User Story 3 - Frontmatter との整合性維持 (Priority: P2)

ファイル名とfrontmatterのtitleプロパティが一致するよう正規化する。

**Why this priority**: Obsidianではファイル名がノートのタイトルとして表示されるため、frontmatterのtitleと一致させることで一貫性を保つ。

**Independent Test**: 正規化後のファイル名とfrontmatter内のtitleが一致することを確認できる。

**Acceptance Scenarios**:

1. **Given** ファイルを正規化処理, **When** 処理完了, **Then** ファイル名（拡張子除く）とfrontmatter.titleが一致する
2. **Given** Ollamaが日本語タイトルを生成, **When** 処理完了, **Then** ファイル名も同じ日本語タイトルとなる

---

### User Story 4 - 重複ファイル名の安全な処理 (Priority: P2)

同名ファイルが既に存在する場合、連番サフィックスを追加して安全に保存する。

**Why this priority**: データ損失を防ぐための安全機能。

**Independent Test**: 同名ファイルが存在する状態で処理を実行し、`_1`, `_2` 等のサフィックスが付与されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `エンジニア/Docker image.md` が既に存在, **When** `@index/2022-10-7-Docker-image.md` を処理, **Then** `エンジニア/Docker image_1.md` として保存される
2. **Given** `エンジニア/Docker image.md` と `Docker image_1.md` が存在, **When** 同名ファイルを処理, **Then** `Docker image_2.md` として保存される

---

### Edge Cases

- ファイル名が日付のみの場合（`2022-10-17.md`）→ Ollamaが内容からタイトルを生成する
- ファイル名にアンダースコアとハイフンが混在（`2022_10_17-My-Title.md`）→ 両方とも適切に処理
- ファイル名に特殊文字が含まれる場合（`<>:"/\|?*`）→ Obsidian互換の文字に置換
- 非常に長いファイル名（200文字以上）→ 適切な長さに切り詰める
- 空白のみの結果になる場合 → Ollamaが生成したタイトルを使用

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはJekyll形式の日付プレフィックス（`YYYY-MM-DD-` または `YYYY_MM_DD_`）をファイル名から除去すること
- **FR-002**: システムはファイル名のハイフン（`-`）をスペース（` `）に変換すること（ただし頭字語や技術用語内のハイフンは考慮）
- **FR-003**: システムは出力ファイル名とfrontmatter.titleを一致させること
- **FR-004**: システムは重複ファイル名を検出し、連番サフィックス（`_1`, `_2`, ...）を追加すること
- **FR-005**: システムはファイルシステム禁止文字（`<>:"/\|?*`）を安全な文字に置換すること
- **FR-006**: システムはファイル名を200文字以内に制限すること
- **FR-007**: システムは元ファイル名から抽出した日付をfrontmatter.createdに保存すること
- **FR-008**: システムはOllamaが生成したタイトルをファイル名として優先使用すること（Ollamaタイトルが適切な場合）

### Key Entities

- **SourceFile**: 元ファイル（@index内のファイル）
  - path: ファイルパス
  - original_filename: 元のファイル名
  - content: ファイル内容

- **NormalizedFile**: 正規化後のファイル
  - path: 移動先パス
  - filename: 正規化後のファイル名
  - frontmatter: タイトル、タグ、作成日を含むメタデータ
  - content: 正規化後の内容

- **FilenameTransformation**: ファイル名変換ルール
  - date_extraction: 日付抽出パターン
  - hyphen_to_space: ハイフン→スペース変換
  - illegal_char_replacement: 禁止文字置換

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 処理後のファイル名にJekyll形式の日付プレフィックス（`YYYY-MM-DD-` または `YYYY_MM_DD_`）が含まれないこと
- **SC-002**: 処理後のファイル名にURL用のハイフン区切り（例：`Word-Word-Word`）が含まれないこと（技術用語を除く）
- **SC-003**: 処理後のファイル名とfrontmatter.titleが一致すること（成功率100%）
- **SC-004**: 元ファイルに含まれていた日付情報がfrontmatter.createdに正しく保存されること
- **SC-005**: 既存ファイルとの重複時に適切なサフィックスが付与され、データ損失がないこと（成功率100%）
- **SC-006**: ユーザーが処理結果を確認し、ファイル名が「自然で読みやすい」と感じること
