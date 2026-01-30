# Data Model: 重複処理の解消

## Entities

### ProcessingItem（既存・変更なし）

パイプラインを流れるデータ単位。全 Stage で共通。

| Field | Type | Description |
|-------|------|-------------|
| item_id | str | ユニーク ID（file_id ハッシュまたは conversation_uuid） |
| source_path | Path | 入力ファイルパス |
| current_step | str | 現在処理中の Step 名 |
| status | ItemStatus | PENDING / COMPLETED / FAILED / FILTERED |
| content | str \| None | アイテムのコンテンツ（JSON 文字列） |
| transformed_content | str \| None | 変換後コンテンツ |
| metadata | dict | メタデータ（プロバイダー固有情報含む） |
| error | str \| None | エラーメッセージ |

### ChatGPT ProcessingItem metadata（discover 後）

`_discover_raw_items()` が yield する ProcessingItem の metadata。

| Key | Type | Description |
|-----|------|-------------|
| conversation_uuid | str | ChatGPT 会話 ID |
| conversation_name | str | 会話タイトル |
| created_at | str | 作成日時 |
| source_provider | str | `"openai"` 固定 |
| source_type | str | `"conversation"` 固定 |
| message_count | int | メッセージ数 |
| format | str | `"claude"` - Claude 形式に変換済み |

### BaseExtractor 責務境界モデル

```
discover_items(input_path, chunk)    ← Template Method（BaseExtractor）
├── _discover_raw_items(input_path)  ← Provider 実装
│   └── yield ProcessingItem(content=..., metadata=...)
└── _chunk_if_needed(item)           ← BaseExtractor（共通）
    └── yield chunked items (1:N) or original (1:1)

run(ctx, items)                      ← BaseStage.run()
├── for item in items:
│   └── _process_item(ctx, item)
│       └── for step in steps:
│           └── step.process(item)   ← Pass-through if already processed
```

## State Transitions

### Extractor フロー（修正後）

```
[Input Source] → discover_items() → [ProcessingItem with content]
                                        ↓
                    run(ctx, items) → Steps (validation only) → [ProcessingItem]
```

### ChatGPT Steps（修正後）

`_discover_raw_items()` が ZIP 読み込み・パース・フォーマット変換を担当するため、Steps はバリデーションのみ。

| Step | 処理内容 |
|------|---------|
| ValidateMinMessagesStep | メッセージ数チェック（MIN_MESSAGES 未満をフィルタ） |

### InputSource（新規）

CLI から ImportPhase に渡される入力ソースの抽象化。

| Field | Type | Description |
|-------|------|-------------|
| value | str | パスまたは URL の文字列値 |
| input_type | InputType | `path` \| `url` |

```python
class InputType(Enum):
    PATH = "path"    # ローカルファイル/ディレクトリ
    URL = "url"      # リモート URL（GitHub 等）

@dataclass(frozen=True)
class InputSource:
    value: str
    input_type: InputType = InputType.PATH

    def as_path(self) -> Path:
        """PATH タイプの場合に Path オブジェクトを返す。"""
        if self.input_type != InputType.PATH:
            raise ValueError(f"Cannot convert {self.input_type} to Path")
        return Path(self.value)

    @property
    def is_url(self) -> bool:
        return self.input_type == InputType.URL
```

## Relationships

### 継承構造と override 状況

```
BaseStage (abstract)
├── stage_type (abstract)
├── steps (abstract)
├── run(ctx, items)         ← concrete: Step 実行ループ
└── _process_item(ctx, item) ← concrete: 1 item を全 Steps に通す

BaseExtractor(BaseStage)
├── stage_type              ← concrete: EXTRACT 固定
├── discover_items()        ← template method: _discover_raw_items → _chunk_if_needed
├── _discover_raw_items()   ← abstract: プロバイダー実装
├── _build_conversation_for_chunking() ← abstract: プロバイダー実装
└── _chunk_if_needed()      ← concrete: チャンク分割

### 修正後（041 target）

ClaudeExtractor(BaseExtractor)
├── _discover_raw_items()   ← impl: JSON/ZIP → conversations → ProcessingItem
├── _build_conversation_for_chunking() ← impl: SimpleConversation 生成
├── _build_chunk_messages() ← impl: {text, sender}
└── steps                   ← impl: [ParseJsonStep, ValidateStructureStep]

ChatGPTExtractor(BaseExtractor)
├── _discover_raw_items()   ← impl: ZIP → conversations → Claude形式 → ProcessingItem
├── _build_conversation_for_chunking() ← impl: ChatGPTConversation 生成
├── _build_chunk_messages() ← impl: {uuid, text, sender, created_at}
└── steps                   ← impl: [ValidateMinMessagesStep]  ← 重複 Steps 削除

GitHubExtractor(BaseExtractor)
├── _discover_raw_items()   ← impl: git clone → Markdown files → ProcessingItem
├── _build_conversation_for_chunking() ← impl: → None (chunking skip)
└── steps                   ← impl: [CloneRepoStep, ParseJekyllStep, ConvertFrontmatterStep]

FileExtractor(BaseStage)    ← ※ BaseExtractor ではなく BaseStage 直接継承（変更なし）
├── steps                   ← impl: [ReadMarkdownStep, ParseFrontmatterStep]
└── stage_type              ← impl: EXTRACT
```

### ⚠️ 問題箇所サマリ

| # | 箇所 | 問題 | 041 対応 |
|---|------|------|:---:|
| 1 | `stage_type` 全子クラス | BaseExtractor と同値の冗長 override | ✅ 削除 |
| 2 | Claude `_chunk_if_needed()` | テンプレートに `_build_chunk_messages()` hook がない | ✅ hook 追加 + override 削除 |
| 3 | ChatGPT `_chunk_if_needed()` | #2 と同じ。Claude とほぼ同一コード | ✅ hook 追加 + override 削除 |
| 4 | GitHub `discover_items()` | テンプレートバイパス + コード重複 | ✅ 削除 |
| 5 | ChatGPT Steps | discover と重複処理 (N² バグ) | ✅ 重複 Steps 削除 |
| 6 | FileExtractor 別系統 | discover/chunking 未対応 | ❌ 別 feature |

### CLI → Phase → Extractor フロー

```
CLI (import_cmd.py)
└── InputSource[] → ImportPhase → extractor.discover_items() → extractor.run(ctx, items)
                                                                        ↓
                                                              data-dump-NNNN.jsonl
                                                              (統一された item 配列)
```

### 入力解決フロー

```
User: make import INPUT=a.zip,b.zip PROVIDER=openai
                    ↓
CLI: --input a.zip --input b.zip --input-type path
                    ↓
InputSource[]: [InputSource("a.zip", PATH), InputSource("b.zip", PATH)]
                    ↓
import_cmd.execute():
  for source in input_sources:
    ├── PATH: validate exists → copy to extract/input/
    └── URL:  validate format → save to extract/input/url.txt
                    ↓
ImportPhase.run() → ExtractStage → Transform → Load
```
