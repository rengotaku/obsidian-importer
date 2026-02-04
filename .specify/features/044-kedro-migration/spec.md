# 機能仕様書: データパイプラインの構造的再設計

**バージョン**: 1.2
**作成日**: 2026-02-04
**ブランチ**: 044-kedro-migration
**ステータス**: 確定

## 概要

現在の ETL パイプラインは「Phase（import / organize）」という独自の処理単位を持ち、各 Phase 内部に Extract → Transform → Load のサブ構造を繰り返す設計になっている。この構造は概念的なねじれを生んでおり、パイプライン全体を俯瞰すると import が「全体の Extract」、import の Transform + organize の一連処理が「全体の Transform と Load」に相当する。

本機能は、この概念的なねじれを解消し、業界標準のパイプラインオーケストレーション基盤に移行することで、処理の依存関係を明示的に管理し、中間データの受け渡しを宣言的に定義できるようにする。

## Clarifications

### Session 2026-02-04

- Q: セッション管理と Resume をどう設計するか？ → A: セッション管理を廃止。冪等なノード設計（出力が既にあればスキップ）のみで Resume を実現する
- Q: アイテム単位のエラーハンドリング方針は？ → A: Hook（`on_node_error`）でエラーを捕捉し、失敗アイテムをログに記録してパイプラインを継続する
- Q: CLI コマンド体系をどうするか？ → A: Kedro CLI にフル移行。`kedro run --pipeline=...` のみ。既存の make コマンドは廃止
- Q: retry コマンドの扱いは？ → A: 廃止。`kedro run` の再実行が冪等 retry として機能する（成功済みスキップ、失敗分のみ再処理）
- Q: status / item-trace コマンドの扱いは？ → A: 廃止。Kedro 組み込み機能（ログ、`kedro viz`）に委ねる

## 背景と動機

### 現状の課題

1. **概念のねじれ**: Phase と ETL の E/T/L が一致していない。import Phase 内の Load は「中間ファイル書き出し」であり、真の Load（Vault 配置）ではない
2. **中間データの暗黙的な受け渡し**: import の出力を organize が読み込む際、ファイルパスの暗黙的な規約に依存している
3. **処理の依存関係が不透明**: どの処理がどの処理に依存しているかがコード上で明示されていない
4. **テストの困難さ**: Phase 内の個別ステップを独立してテストするために多くのモックが必要
5. **新しい処理の追加コスト**: 新しい Phase を追加するたびに、ETL のサブ構造ごと実装する必要がある

### 期待される改善

- 処理の依存関係が DAG（有向非巡回グラフ）として可視化される
- 中間データの入出力が宣言的に管理される
- 個々の処理ノードを独立してテスト・実行できる
- 新しい処理の追加が、ノードの定義と依存関係の宣言だけで完了する

## ユーザーシナリオ

### シナリオ 1: 標準的なインポート処理

**アクター**: パイプライン利用者（CLI ユーザー）

1. ユーザーが CLI コマンドで Claude エクスポートデータのインポートから Vault 配置までを指示する
2. パイプラインが以下の処理を DAG に従い実行する：
   - 外部データの取得・パース・バリデーション
   - 知識抽出（LLM による要約・タグ付け）
   - メタデータ生成・フォーマット変換
   - ジャンル判定
   - 最終ファイルの Vault 配置
3. 各処理ノードの進捗と結果がログに出力される
4. 処理完了後、成功・失敗・スキップの件数が報告される

### シナリオ 2: 失敗後の再実行

**アクター**: パイプライン利用者

1. 前回の処理で一部アイテムが失敗した
2. 同じコマンドを再実行する
3. 冪等なノード設計により、出力が既に存在するアイテムはスキップされる
4. 失敗アイテムのみが再処理される

### シナリオ 3: 特定の処理ステップだけの実行

**アクター**: 開発者・デバッグ担当

1. 特定の処理ノードまたはノード範囲を指定して実行する
2. 入力データとして中間データセットを参照する
3. 処理結果がデータセットとして保存され、後続ノードの入力として利用可能

### シナリオ 4: 処理フローの可視化

**アクター**: 開発者

1. DAG 可視化コマンドを実行する
2. 処理ノード間の依存関係がグラフとして表示される
3. 各ノードの入力・出力データセットが一覧で確認できる

## 機能要件

### FR-1: 処理ノードの独立実行

- 各処理（パース、バリデーション、知識抽出、ジャンル判定等）が独立した純粋関数として定義されること
- 任意の処理ノードを、適切な入力データを与えれば単独で実行できること
- 処理ノード間の依存関係が入出力データセット名で宣言的に定義されていること

### FR-2: 中間データの宣言的管理

- 各処理ノードの入力・出力データが型情報付きで宣言されていること
- 中間データの永続化先（ファイルパス、形式）が設定ファイルで一元管理されること
- 中間データの読み書きが処理ロジックから分離されていること

### FR-3: CLI インターフェース

- パイプライン全体またはサブパイプラインを指定して実行するコマンドが提供されること
- ノード範囲指定（`--from-nodes`, `--to-nodes`）による部分実行が可能なこと
- 主要なパラメータ（入力パス、プロバイダー種別、処理件数上限等）がコマンドライン引数またはパラメータ設定で指定できること

### FR-4: 冪等性による Resume

- 各ノードの出力データセットが存在する場合、そのノードの再実行をスキップできること
- コマンドの再実行が実質的な Resume / Retry として機能すること
- LLM 呼び出しなど高コストな処理の不要な再実行が回避されること

### FR-5: エラーハンドリング

- 個別アイテムの処理失敗がパイプライン全体を停止させないこと（Hook によるエラー捕捉）
- 失敗アイテムのエラー詳細（バックトレース、LLM プロンプト/出力）がログに記録されること
- コマンド再実行により失敗アイテムのみが再処理されること（冪等性による）

### FR-6: デバッグ・可視化

- ノード実行ログにより各処理ステップの結果が確認できること
- DAG 可視化機能により処理ノードの依存関係と入出力データセットが一覧表示できること

### FR-7: 複数プロバイダー対応

- Claude、ChatGPT、GitHub Jekyll の各プロバイダーからのインポートが動作すること
- プロバイダー固有の処理（ZIP 展開、ツリー走査、git clone 等）が適切に分離されていること

## スコープ

### スコープ内

- `src/etl/` 配下のパイプライン処理のゼロからの再構築
- CLI の Kedro CLI への移行
- 冪等ノード設計による Resume 機能の実現
- 全プロバイダー（Claude、ChatGPT、GitHub Jekyll）の対応
- テストのゼロからの再作成

### スコープ外

- `src/converter/`（レガシーコード）の変更
- 新しいプロバイダーの追加
- RAG 機能（`src/rag/`）への影響
- Obsidian Vault の構造変更
- Web UI やダッシュボードの追加

### 廃止する既存機能

- `make import`, `make organize`, `make retry`, `make status`, `make item-trace` 等の独自 CLI コマンド
- セッション管理（session.json, phase.json）
- 独自の Resume モード（セッションベース）

## 移行方針

- **一括移行**: 全処理ノードを一度に新基盤へ移行する。旧コードとの互換性は維持しない
- **テスト全面刷新**: 既存テストは破棄し、新基盤に適したテストをゼロから作成する
- **旧コード削除**: 移行完了後、旧 `src/etl/` のコードは削除する

## 成功基準

1. **機能的同等性**: 移行前と移行後で、同一の入力データに対して同一の出力ファイルが生成される（内容一致率 100%）
2. **処理時間**: 移行後のパイプライン処理時間が移行前の 120% 以内に収まる
3. **ステップ独立実行**: 任意の処理ノードを単独で実行した場合、正しい結果が得られる
4. **冪等 Resume**: コマンド再実行時に完了済みアイテムが再処理されず、未処理アイテムのみが正しく処理される

## 主要エンティティ

| エンティティ | 説明 | 現在の対応物 |
|------------|------|------------|
| パイプライン | 処理ノードの DAG 全体 | Phase（import, organize） |
| ノード | 単一の処理単位（純粋関数: 入力→出力） | Step（BaseStep サブクラス） |
| データセット | ノード間で受け渡される型付きデータ | ProcessingItem / JSONL / Markdown |
| カタログ | データセットの永続化先の宣言的定義 | .staging/ フォルダ構造（暗黙的） |
| ランナー | パイプラインの実行方式（逐次/並列） | BasePhaseOrchestrator.run() |
| Hook | ノード実行前後の横断的関心事（エラー捕捉、ログ） | tenacity retry / step tracker |

## 依存関係

- 既存の Ollama API クライアント（LLM 呼び出し）
- パイプラインオーケストレーション基盤

## 前提条件

- 既存のパイプラインが安定稼働しており、リグレッションの基準となる入出力データが存在する
- パイプラインオーケストレーション基盤の選定が完了していること

## 想定事項

- `src/converter/`（レガシーコード）は移行対象外とし、一切変更しない
- 単一ユーザー・ローカル実行環境のため、分散実行やスケーラビリティは考慮しない
- 既存のフォルダ構造（`.staging/@session/`）は再設計の対象とする（旧構造の互換性は不要）

## リスクと緩和策

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| 一括移行による機能退行 | 処理結果が変わる | 移行前の入出力データをゴールデンデータとして保存し、比較テストを実施 |
| 移行期間中の開発停止 | 新機能追加ができない | 移行を最優先タスクとし、短期集中で完了させる |
| LLM 呼び出しの再実行 | 不要なコスト発生 | 冪等ノード設計を最優先で実装する |
| Hook ベースのエラーハンドリングの制約 | 複雑なリトライ戦略が難しい | 単純な「再実行=リトライ」で運用し、複雑なリトライが必要になった時点で再検討する |

## 処理ステップ対応表

既存の全処理ステップと Kedro ノードへの対応。処理漏れ防止のためのチェックリストとして使用する。

### Claude プロバイダー

| ETL Stage | 現在の Step クラス | 処理内容 | Kedro Pipeline | Kedro Node |
|-----------|-------------------|---------|----------------|------------|
| E | ParseJsonStep | JSON パース・構造解析 | data_engineering | parse_claude_json |
| E | ValidateStructureStep | 構造バリデーション（uuid, chat_messages 必須） | data_engineering | validate_structure |
| E | ValidateContentStep | コンテンツ量バリデーション（空メッセージ除外） | data_engineering | validate_content |
| E | *(BaseExtractor)* | チャンク分割（25000 文字超の会話を分割） | data_engineering | chunk_conversation |
| T | ExtractKnowledgeStep | LLM 知識抽出（タイトル・要約・タグ）+ 英語 Summary 翻訳 | data_science | extract_knowledge |
| T | GenerateMetadataStep | メタデータ生成（file_id、created、source_provider 等） | data_science | generate_metadata |
| T | FormatMarkdownStep | Markdown フォーマット（YAML frontmatter 付き） | data_science | format_markdown |

### ChatGPT プロバイダー

| ETL Stage | 現在の Step クラス | 処理内容 | Kedro Pipeline | Kedro Node |
|-----------|-------------------|---------|----------------|------------|
| E | *(ChatGPTExtractor._discover)* | ZIP 展開・conversations.json 抽出・ツリー走査 | data_engineering | parse_chatgpt_zip |
| E | ValidateMinMessagesStep | メッセージ数バリデーション + file_id 生成 | data_engineering | validate_min_messages |
| E | *(BaseExtractor)* | チャンク分割 | data_engineering | chunk_conversation |
| T | ExtractKnowledgeStep | LLM 知識抽出（Claude と共通） | data_science | extract_knowledge |
| T | GenerateMetadataStep | メタデータ生成（Claude と共通） | data_science | generate_metadata |
| T | FormatMarkdownStep | Markdown フォーマット（Claude と共通） | data_science | format_markdown |

### GitHub Jekyll プロバイダー

| ETL Stage | 現在の Step クラス | 処理内容 | Kedro Pipeline | Kedro Node |
|-----------|-------------------|---------|----------------|------------|
| E | CloneRepoStep | git clone（sparse-checkout） | data_engineering | clone_github_repo |
| E | ParseJekyllStep | Jekyll frontmatter パース・draft/private 除外 | data_engineering | parse_jekyll |
| E | ConvertFrontmatterStep | frontmatter 変換（Jekyll → Obsidian 形式） | data_engineering | convert_frontmatter |
| T | GenerateMetadataStep | メタデータ生成（GitHub 用分岐） | data_science | generate_metadata |
| T | FormatMarkdownStep | Markdown フォーマット（GitHub Jekyll はパススルー） | data_science | format_markdown |

### Organize（ジャンル判定・Vault 配置）

| ETL Stage | 現在の Step クラス | 処理内容 | Kedro Pipeline | Kedro Node |
|-----------|-------------------|---------|----------------|------------|
| E | ReadMarkdownStep | Markdown ファイル読み込み | data_science | read_markdown |
| E | ParseFrontmatterStep | YAML frontmatter パース | data_science | parse_organize_frontmatter |
| T | ClassifyGenreStep | ジャンル判定（キーワードベース） | data_science | classify_genre |
| T | NormalizeFrontmatterStep | frontmatter 正規化 + LLM タグ生成 | data_science | normalize_frontmatter |
| T | CleanContentStep | コンテンツ整形（余分な空行削除等） | data_science | clean_content |
| L | DetermineVaultStep | ジャンル → Vault パスのマッピング | data_publishing | determine_vault |
| L | MoveToVaultStep | Vault へのファイル配置 | data_publishing | move_to_vault |

### 横断的処理（Step クラス外）

| 処理 | 現在の実装箇所 | Kedro での対応 |
|------|--------------|---------------|
| セッション作成・状態管理 | Session, Phase クラス | 廃止（冪等ノード設計で代替） |
| Resume（処理済みスキップ） | CompletedItemsCache | 廃止（DataCatalog の存在チェックで代替） |
| リトライ（tenacity） | ExtractKnowledgeStep 内 | Hook or ノード内 tenacity で維持 |
| エラー詳細記録 | error_writer.py | Hook（on_node_error）で記録 |
| JSONL ステップログ | BaseStage._log_step() | Kedro ログ + Hook で代替 |
| file_id 生成 | file_id.py | ユーティリティ関数として維持 |
| Ollama API 呼び出し | ollama.py | ユーティリティ関数として維持 |
| 知識抽出プロンプト | prompts/*.txt | Kedro パラメータまたはファイルとして維持 |

### 処理ステップ総数

| 区分 | 件数 |
|------|------|
| Import Extract（全プロバイダー） | 10 |
| Import Transform | 3（プロバイダー間で共有） |
| Organize Extract | 2 |
| Organize Transform | 3 |
| Organize Load | 2 |
| 横断的処理 | 8 |
| **合計** | **28** |
