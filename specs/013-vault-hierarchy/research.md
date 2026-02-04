# Research: Vault配下ファイル階層化

**Date**: 2026-01-15
**Feature**: 013-vault-hierarchy

## 1. 既存システム分析

### 現状のスクリプト構成

| スクリプト | 役割 |
|-----------|------|
| `ollama_genre_classifier.py` | ジャンル判定（エンジニア/ビジネス/経済/日常） |
| `markdown_normalizer.py` | Markdown正規化（frontmatter整形） |
| `tag_extractor.py` | タグ抽出 |
| `normalize_obsidian.py` | Obsidian形式への変換 |

### 現状のファイル分布

| Vault | ルート直下ファイル数 | 既存サブフォルダ数 |
|-------|---------------------|-------------------|
| エンジニア | 927 | 12 |

### 既存サブフォルダ構造（エンジニアVault）

```
エンジニア/
├── AWS Technical Essentials Part 1/
├── AWS Technical Essentials Part 2/
├── AWS学習/
├── DevOps・メトリクス/
├── キャリア/
├── セキュリティ/
├── テスト・QA/
├── データベース/
├── ネットワーク/
├── マネジメント/
└── index/
```

## 2. 技術的決定事項

### Decision 1: LLMプロンプト拡張方式

**Decision**: 既存の`ollama_genre_classifier.py`のプロンプトを拡張し、ジャンル＋サブフォルダを同時判定

**Rationale**:
- 既存コードを最大限再利用
- 1回のLLM呼び出しで両方を判定（効率的）
- 既存サブフォルダ一覧をプロンプトに含める

**Alternatives considered**:
- 2段階判定（ジャンル→サブフォルダ）: LLM呼び出し2倍、却下
- ルールベース分類: 柔軟性不足、却下

### Decision 2: サブフォルダ候補の提供方法

**Decision**: 各Vaultの既存サブフォルダ一覧をプロンプトに動的注入

**Rationale**:
- 既存フォルダ優先の要件を満たす
- 新規フォルダ提案も可能（LLMが「新規: xxx」形式で提案）

**Format**:
```json
{
  "genre": "エンジニア",
  "subfolder": "Docker",  // 既存フォルダ名 or "新規: コンテナ技術"
  "confidence": 0.85,
  "reason": "Docker関連の技術メモ"
}
```

### Decision 3: ファイル移動の安全性

**Decision**:
1. ドライランモード（デフォルト）で提案を表示
2. `--execute` フラグで実際に移動
3. 移動ログをJSON形式で保存

**Rationale**:
- Constitution「自動化処理は人間の確認を前提とする」に準拠
- ロールバック可能な設計

### Decision 4: 内部リンク対応

**Decision**: Obsidianのリンク形式 `[[ファイル名]]` はそのまま維持

**Rationale**:
- Obsidianは相対パスではなくファイル名でリンク解決
- 同一Vault内の移動ではリンク更新不要
- Vault間移動の場合のみ警告表示

## 3. 実装アプローチ

### 新規スクリプト: `hierarchy_organizer.py`

```
機能:
1. Vault内の既存サブフォルダ一覧を取得
2. ルート直下のファイルを列挙
3. 各ファイルをLLMで分類（ジャンル＋サブフォルダ）
4. 結果をCSV/JSONで出力（ドライラン）
5. --execute で実際に移動
```

### 既存スクリプトの拡張: `ollama_genre_classifier.py`

```
変更点:
- SYSTEM_PROMPTにサブフォルダ判定を追加
- 出力JSONにsubfolderフィールドを追加
- Vault別サブフォルダ一覧の動的生成
```

## 4. Constitution適合性

| 原則 | 適合状況 |
|------|----------|
| I. Vault Independence | ✅ 各Vault独立で処理 |
| II. Obsidian Markdown Compliance | ✅ リンク形式維持 |
| III. Normalization First | ✅ 正規化済みファイルのみ対象 |
| IV. Genre-Based Organization | ✅ ジャンル＋サブフォルダ分類 |
| V. Automation with Oversight | ✅ ドライランデフォルト |

## 5. 残課題

- [ ] 各Vault用のサブフォルダテンプレート定義（推奨フォルダ一覧）
- [ ] 新規フォルダ作成時の命名規則
- [ ] 処理の進捗表示・中断再開機能
