# Research: 重複処理の解消

## R1: `_discover_raw_items()` vs `steps` の責務分担方針

### Decision

**BaseExtractor テンプレートを正しく設計し、構造的に重複が不可能な設計にする。**

- `_discover_raw_items()`: 入力ソースから ProcessingItem を yield する。content を設定済みで返す（パース・変換完了）。
- `steps`: discover 済み item のバリデーション・メタデータ付与のみ。入力読み込みや変換は行わない。
- `_chunk_if_needed()`: テンプレートに `_build_chunk_messages()` hook を追加し、子クラスの override を不要にする。

### Rationale

R5 の継承構造分析により、以下の問題が判明:

1. **ChatGPT の N² 重複**: discover が全処理を行い、Steps も全処理を行う
2. **`_chunk_if_needed()` の不完全なテンプレート**: `chat_messages` 再構築を子クラスに強制
3. **`stage_type` の冗長 override**: BaseExtractor が EXTRACT を返すのに全子クラスが再定義
4. **GitHub の `discover_items()` override**: テンプレートメソッドのバイパス

これらは「テンプレートが不完全」という共通の根本原因を持つ。pass-through ガードは症状の隠蔽であり、テンプレートの正しい設計こそが本質的な解決。

### 設計方針

```
BaseExtractor (テンプレート完成形)
├── stage_type              → EXTRACT 固定（子クラスの override 不要）
├── discover_items()        → template: _discover_raw_items → _chunk_if_needed
├── _discover_raw_items()   → abstract: プロバイダーが実装（content 設定済み item を yield）
├── _chunk_if_needed()      → concrete: _build_chunk_messages() hook で chunk content 構築
├── _build_conversation_for_chunking() → abstract: チャンク判定用
├── _build_chunk_messages() → hook (default: None): チャンク分割時の messages 再構築
└── steps                   → abstract: バリデーション・メタデータ付与のみ
```

**テンプレートが保証すること:**
- discover → chunk → run(steps) の順序が固定
- `_chunk_if_needed()` が `_build_chunk_messages()` を呼び、子クラスは hook のみ実装
- Steps は入力読み込み・変換を行わない（discover が完了済み）

### Alternatives Considered (Rejected)

1. **Steps に pass-through ガード追加**（旧 R1/R2 方針）
   - Rejected: 症状の隠蔽。テンプレートが不完全なまま子クラスの責務が曖昧になる。
   - ChatGPT の 4 Step すべてにガードを入れる必要があり、脆弱。

2. **パターン B に統一**（discover は content=None、Steps で全処理）
   - Rejected: チャンキングに content が必要。discover で content を設定する設計は維持。

3. **フレームワークで重複検出**（BaseStage.run() でチェック）
   - Rejected: 暗黙的すぎる。テンプレートで構造的に保証すべき。

---

## R2: ChatGPTExtractor の具体的修正方針

### Decision

**ChatGPTExtractor の Steps から重複処理（ZIP 読み込み・パース・フォーマット変換）を削除する。Steps はバリデーション・メタデータ付与のみに責務を限定する。**

### Rationale

テンプレート化（R1）により、`_discover_raw_items()` が content 設定済みの ProcessingItem を yield する契約が確立される。Steps は discover 後の item に対してバリデーションのみ行う。

### 修正内容

| Step | 現状 | 修正後 |
|------|------|--------|
| ReadZipStep | ZIP 読み込み → conversations.json 抽出 | **削除**（discover が担当） |
| ParseConversationsStep | JSON 配列パース → 1:N 展開 | **削除**（discover が担当） |
| ConvertFormatStep | ChatGPT tree → Claude flat 変換 | **削除**（discover が担当） |
| ValidateMinMessagesStep | メッセージ数チェック | **維持**（バリデーション責務） |

ChatGPT の steps は `[ValidateMinMessagesStep]` のみになる。

### band-aid 修正について

現在のブランチに pass-through ガードが存在するが、これは **revert する**。ガードではなく、Steps 自体を削除することで構造的に重複不可能にする。

### 追加修正

- `stage.py` の `_max_records_per_file` 変更の revert: 5000 → 1000（本 issue と無関係な変更）

---

## R3: GitHubExtractor の `discover_items()` override 問題

### Decision

**GitHubExtractor の `discover_items()` override を削除し、BaseExtractor のテンプレートメソッドを使用する。**

### Rationale

GitHubExtractor は `discover_items()` を override しており、BaseExtractor のテンプレートメソッド（`_discover_raw_items()` → `_chunk_if_needed()`）をバイパスしている。

現在の override:
- `discover_items()`: clone → discover → list を返す（Iterator ではなく list）
- `_discover_raw_items()`: 同じ clone → discover 処理（使われていない）

問題点:
- `_discover_raw_items()` とほぼ同一のコードが重複
- BaseExtractor の `_chunk_if_needed()` が呼ばれない（チャンキング無効）
- テンプレートメソッドパターンの違反

修正:
- `discover_items()` override を削除
- `_discover_raw_items()` のみを使用（Iterator を返す）
- `_build_conversation_for_chunking()` が既に実装済みのためチャンキングも正常動作

### Alternatives Considered

1. **override を維持し、list 返却を修正**
   - Rejected: コード重複が残る。テンプレートメソッドを使うべき。

---

## R4: テスト戦略

### Decision

**既存テストの回帰確認 + ChatGPT 重複防止の新規テスト追加。**

### Test Plan

| テスト | 対象 | 検証内容 |
|-------|------|---------|
| 既存: `test_claude_extractor_refactoring.py` | Claude | 回帰なし |
| 既存: `test_github_extractor.py` | GitHub | 回帰なし |
| 新規: ChatGPT discover → run 統合テスト | ChatGPT | N items → N output（N² にならない） |
| 新規: ChatGPT Steps pass-through テスト | Steps | content 有の item が再処理されない |
| 新規: GitHubExtractor テンプレートメソッドテスト | GitHub | discover_items() が BaseExtractor 経由で動作 |

### Rationale

- unittest を使用（プロジェクト標準）
- fixture は最小限（1-3 会話の小さな ZIP/JSON）
- LLM 呼び出しなし（Extract ステージのみ）

---

## R5: Extractor 継承構造の分析と統一方針

### 現状のメソッド構成マトリクス

#### BaseExtractor テンプレート

| メソッド | 種類 | 役割 |
|---------|------|------|
| `stage_type` | concrete | `EXTRACT` 固定 |
| `discover_items()` | **template method** | `_discover_raw_items()` → `_chunk_if_needed()` |
| `_chunk_if_needed()` | concrete | チャンキング判定・分割 |
| `_discover_raw_items()` | **abstract** | プロバイダーが実装 |
| `_build_conversation_for_chunking()` | **abstract** | プロバイダーが実装 |
| `steps` | (BaseStage abstract) | プロバイダーが実装 |

#### 各クラスの override 状況

| メソッド | BaseExtractor | Claude | ChatGPT | GitHub | File |
|---------|:---:|:---:|:---:|:---:|:---:|
| **継承元** | BaseStage | BaseExtractor | BaseExtractor | BaseExtractor | **BaseStage** |
| `stage_type` | concrete | **override** ⚠️ | **override** ⚠️ | **override** ⚠️ | **override** |
| `discover_items()` | template | - | - | **override** ⚠️ | N/A |
| `_discover_raw_items()` | abstract | impl ✅ | impl ✅ | impl ✅ | N/A |
| `_build_conversation_for_chunking()` | abstract | impl ✅ | impl ✅ | impl (→None) ✅ | N/A |
| `_chunk_if_needed()` | concrete | **override** ⚠️ | **override** ⚠️ | - | N/A |
| `steps` | (abstract) | impl ✅ | impl ✅ | impl ✅ | impl ✅ |
| `__init__` | concrete | **override** | - | **override** | **override** |

#### 問題一覧（⚠️）

| # | 問題 | 影響 |
|---|------|------|
| 1 | **`stage_type` が全子クラスで再定義** | BaseExtractor が `EXTRACT` を返すのに、Claude/ChatGPT/GitHub が同値で override。冗長 |
| 2 | **Claude `_chunk_if_needed()` override** (L363-427) | BaseExtractor の concrete を override。`chat_messages` 再構築のため |
| 3 | **ChatGPT `_chunk_if_needed()` override** (L646-716) | 同上。Claude とほぼ同一コード。差分は dict 構造のみ |
| 4 | **GitHub `discover_items()` override** (L266-331) | テンプレートメソッドを完全バイパス。`_discover_raw_items()` とコード重複 |
| 5 | **FileExtractor は別系統** | BaseStage 直接継承。discover/chunking 機能なし |

#### `_chunk_if_needed()` override の差分分析

Claude と ChatGPT の override はほぼ同一。差分は `chat_messages` の dict 構造のみ:

```python
# Claude (L398-400)
chunk_conv["chat_messages"] = [
    {"text": msg.content, "sender": msg.role}
    for msg in chunk.messages
]

# ChatGPT (L689-695)
chunk_conv["chat_messages"] = [
    {"uuid": "", "text": msg.content, "sender": msg.role,
     "created_at": chunk_conv.get("created_at", "")}
    for msg in chunk.messages
]
```

BaseExtractor の `_chunk_if_needed()` は `item.content` をそのまま保持するだけで `chat_messages` をチャンク分割後の内容に再構築しない → 子クラスが override する必要がある。

### Decision

**041 で全面的にテンプレート化する。**

| 対応 | 041 スコープ | 理由 |
|------|:---:|------|
| `_chunk_if_needed()` テンプレート化 | ✅ | `_build_chunk_messages()` hook 追加。Claude/ChatGPT の override 削除 |
| `stage_type` 冗長 override 削除 | ✅ | BaseExtractor が EXTRACT を返すため不要。低リスク |
| GitHub `discover_items()` override 削除 | ✅ | コード重複 + テンプレート違反 |
| ChatGPT Steps 重複処理削除 | ✅ | ReadZip/ParseConversations/ConvertFormat を削除。バリデーションのみ残す |
| FileExtractor の BaseExtractor 移行 | ❌ | organize Phase の構造変更が必要。別 feature |

---

## R6: 入力インターフェース統一（INPUT_TYPE + 複数 INPUT）

### Decision

**CLI に `--input-type`（デフォルト: `path`）を導入し、`--input` を複数回指定可能にする。** プロバイダー依存の入力解決を CLI レイヤーで統一する。

### 現状の問題

```python
# import_cmd.py の現状: provider ごとに分岐
if provider == "github":
    source_path = input_path          # URL 文字列のまま
else:
    input_path = Path(input_path)     # Path に変換
    if not input_path.exists(): ...   # 存在チェック
```

- GitHub だけ特殊処理（URL 文字列をそのまま渡す）
- プロバイダーが入力形式を暗黙的に決定している
- 複数入力に対応していない（1 回の実行で 1 ソースのみ）

### 設計

#### CLI インターフェース

```bash
# ローカルパス（INPUT_TYPE=path がデフォルト）
make import INPUT=path/to/dir PROVIDER=claude

# URL 入力（INPUT_TYPE=url を明示指定）
make import INPUT=https://github.com/user/repo/tree/master/_posts INPUT_TYPE=url PROVIDER=github

# 複数 INPUT（カンマ区切り）
make import INPUT=export1.zip,export2.zip PROVIDER=openai
```

#### argparse 変更

```python
parser.add_argument(
    "--input",
    action="append",     # 複数回指定可能
    help="Input source (repeatable). Path or URL depending on --input-type.",
)
parser.add_argument(
    "--input-type",
    default="path",
    choices=["path", "url"],
    help="Input source type (default: path). 'url' for remote sources.",
)
```

#### 入力解決フロー

```
CLI args → InputResolver
├── input_type == "path":
│   ├── Validate: Path exists
│   ├── Detect: file (ZIP/JSON) or directory
│   └── Copy to extract/input/
├── input_type == "url":
│   ├── Validate: URL format
│   ├── Save URL to extract/input/url.txt
│   └── Let Extractor handle (clone, download, etc.)
└── Multiple inputs:
    └── Iterate and apply above logic per input
```

#### Makefile 変更

```makefile
import:
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl import \
		$(foreach inp,$(subst $(COMMA), ,$(INPUT)),--input "$(inp)") \
		$(if $(INPUT_TYPE),--input-type $(INPUT_TYPE),) \
		$(if $(PROVIDER),--provider $(PROVIDER),) \
		...
```

### Rationale

1. **プロバイダー非依存**: 入力がパスか URL かは `--input-type` で明示。GitHub 以外にも将来 URL 入力が必要なプロバイダーを追加可能
2. **複数入力**: ChatGPT エクスポートは分割ダウンロードされることがある。複数 ZIP を 1 セッションで処理可能にする
3. **GitHub の特殊処理を解消**: `provider == "github"` の分岐を `input_type == "url"` に置き換え
4. **後方互換は不要**: `--input-type` は明示指定。GitHub 利用時は `INPUT_TYPE=url` を必須とする

### Alternatives Considered

1. **INPUT に URL を検出して自動判定**（`http://` で始まるなら URL）
   - Rejected: 暗黙的で、ローカルパスに `http` を含むエッジケースがある。明示的な `--input-type` が安全

2. **プロバイダーごとに固定**（claude=path, github=url）
   - Rejected: 現状と同じ問題。将来 URL 経由の Claude データ取得などが追加できない

3. **`--url` 別引数を追加**（`--input` はパス専用、`--url` は URL 専用）
   - Rejected: 複数入力時にパスと URL を混在指定する場合に煩雑。`--input` + `--input-type` の方がシンプル

### 影響範囲

| File | 変更内容 |
|------|---------|
| `src/etl/cli/commands/import_cmd.py` | `--input` を `action="append"`、`--input-type` 追加、入力解決ロジック統一 |
| `src/etl/phases/import_phase.py` | 複数入力パスの受け渡し対応 |
| `Makefile` | `INPUT_TYPE` 変数、複数 INPUT のカンマ区切りサポート |
| `CLAUDE.md` | CLI ドキュメント更新 |
