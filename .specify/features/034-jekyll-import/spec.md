# Feature Specification: Jekyll ブログインポート

**Feature Branch**: `034-jekyll-import`
**Created**: 2026-01-25
**Status**: Draft
**Input**: User description: "https://github.com/example-user/example-user.github.io/tree/master/_posts のインポートの作成"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - GitHub からの Jekyll ブログインポート (Priority: P1)

ユーザーは GitHub リポジトリの `_posts` ディレクトリに格納された Jekyll ブログ記事を、既存の ETL パイプラインを使って Obsidian ナレッジベースにインポートしたい。501件以上の技術記事を効率的に取り込み、既存の Claude/ChatGPT インポートと同様のワークフローで処理できるようにする。

**Why this priority**: Jekyll ブログには長年蓄積された技術知識が含まれており、これを Obsidian に統合することで検索・参照可能にすることが主目的。

**Independent Test**: `make import INPUT=<git-url> PROVIDER=github` コマンドで GitHub リポジトリから記事を取得し、Obsidian Markdown ファイルとして出力できることを確認。

**Acceptance Scenarios**:

1. **Given** GitHub リポジトリ URL（パス付き）が指定されている, **When** `make import INPUT=https://github.com/user/repo/tree/master/_posts PROVIDER=github` を実行, **Then** 指定パス内の Markdown ファイルが取得され、ETL パイプラインで処理される
2. **Given** Jekyll 形式のファイル（`YYYY-MM-DD-title.md`）がある, **When** インポート処理が実行される, **Then** Jekyll frontmatter が Obsidian 形式に変換され、`file_id` が付与される
3. **Given** 既にインポート済みのファイル（同じ `file_id`）がある, **When** 再度インポートを実行, **Then** 既存ファイルが更新される（重複作成されない）

---

### User Story 2 - Resume モードでの大量ファイル処理 (Priority: P2)

500件以上のファイルをインポートする際、処理が中断された場合でも `--session` オプションで続行できる。

**Why this priority**: 大量ファイルの処理は時間がかかり、中断のリスクがあるため、既存の Resume モード機能を活用することが重要。

**Independent Test**: 意図的に処理を中断し、`--session` オプションで再開した際に処理済みファイルがスキップされることを確認。

**Acceptance Scenarios**:

1. **Given** 100件中50件目で処理が中断された, **When** `--session` で再開, **Then** 51件目から処理が継続される
2. **Given** エラーで失敗したファイルがある, **When** `make retry` を実行, **Then** 失敗ファイルのみが再処理される

---

### Edge Cases

- **空のディレクトリ**: 警告ログを出力して正常終了
- **ファイル名が ID のみ**（例: `2022-11-27-532.md`）: タイトルは frontmatter.title から取得（必須）
- **日付が見つからない**: 現在日時をフォールバックとして使用
- **frontmatter.title がない**: ファイル名（拡張子・日付プレフィックス除く）をタイトルとして使用
- **不正な frontmatter**: YAML パースエラー時はファイル内容全体を本文として処理
- **GitHub アクセス失敗**: 適切なエラーメッセージと終了コード 3 を返す
- **git clone 失敗**: リポジトリが存在しない、または非公開の場合はエラー
- **非常に大きなファイル（25000文字超）**: 既存のチャンク分割機能を活用
- **無効な URL 形式**: `https://github.com/{owner}/{repo}/tree/{branch}/{path}` 以外はエラー

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは GitHub リポジトリ URL（パス付き）を入力として受け付け、指定パスの内容を git clone で取得できる MUST
  - URL 形式: `https://github.com/{owner}/{repo}/tree/{branch}/{path}`
  - 例: `https://github.com/user/repo/tree/master/_posts`
  - URL からリポジトリ、ブランチ、対象パスを解析する
- **FR-002**: システムは以下の優先順位で日付を抽出できる MUST
  1. frontmatter の `date` フィールド（ISO 8601 形式対応: `2020-01-20T15:12:41+09:00`）
  2. ファイル名の Jekyll 形式（`YYYY-MM-DD-*.md`）
  3. タイトルから正規表現で抽出（`YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY年MM月DD日`）
  4. 本文先頭から正規表現で抽出
  5. フォールバック: 現在日時
  - タイトルは frontmatter.title から取得（ファイル名は ID のみの場合あり: `2022-11-27-532.md`）
- **FR-003**: システムは frontmatter を Obsidian 形式に変換できる MUST
  - `title` → そのまま維持（必須）
  - `date` → `created` に変換（ISO 8601 → YYYY-MM-DD）
  - `tags`/`categories`/`keywords` → `tags` に統合
  - 本文中の `#tag` 形式 → `tags` に追加（正規表現で抽出）
  - `draft: true` または `private: true` → スキップ（除外）
  - 不要フィールドは削除: `layout`, `permalink`, `excerpt`, `slug`, `lastmod`, `headless`
- **FR-004**: システムは各ファイルに `file_id`（SHA256 ハッシュ）を生成して重複管理できる MUST
- **FR-005**: システムは既存の `--session`、`--debug`、`--dry-run`、`--limit` オプションをサポートする MUST
- **FR-006**: システムは処理結果を既存の session フォルダ構造（`import/extract/`, `import/transform/`, `import/load/`）に出力する MUST
- **FR-007**: システムは `@index` フォルダにも最終出力ファイルを配置する MUST
- **FR-008**: システムは `PROVIDER=github` または `--provider github` で GitHub インポートモードを選択できる MUST

### Key Entities

- **JekyllPost**: Jekyll ブログ記事
  - ファイル名から抽出した日付（`created`）
  - ファイル名から抽出したタイトル（`title`）
  - frontmatter のメタデータ（`tags`, `categories` 等）
  - 本文コンテンツ
- **ProcessingItem**: 既存 ETL モデルの拡張使用
  - `item_id`: ファイル名（拡張子なし）
  - `file_id`: SHA256 ハッシュ
  - `content`: 変換後 Markdown
  - `metadata`: 抽出されたメタデータ

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 500件以上の Jekyll 記事を1回のインポートで正常に処理できる
- **SC-002**: インポート完了後、すべての記事が Obsidian で正常に表示される（frontmatter エラーなし）
- **SC-003**: 同じリポジトリを再度インポートした際、変更のないファイルはスキップされる
- **SC-004**: 処理中断後の Resume で、処理済みファイルの再処理が発生しない
- **SC-005**: `--dry-run` モードで実際のファイル書き込みなしに処理内容をプレビューできる

## Assumptions

- GitHub パブリックリポジトリからの取得を前提とする（認証なし）
- URL で指定されたパス配下の Markdown ファイルを対象とする
- Markdown ファイル（`.md`）のみを対象とする（HTML ファイルは対象外）
- 画像等のアセットは本フェーズではインポート対象外（将来拡張）
- 既存の Ollama 知識抽出機能は使用しない（記事は既にタイトル・タグを持つため）
- git clone は `--depth 1` で shallow clone を使用（履歴不要）

## Out of Scope

- ローカルディレクトリからのインポート（GitHub URL のみ対応）
- GitHub プライベートリポジトリのアクセス（認証機能）
- 画像・添付ファイルのインポート
- Jekyll テーマやレイアウトの解析
- リンクの自動変換（Jekyll 内部リンク → Obsidian 内部リンク）
- 既存の Obsidian ノートとの自動リンク生成
