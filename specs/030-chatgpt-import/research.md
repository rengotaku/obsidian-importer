# Research: ChatGPT エクスポートインポート

**Created**: 2026-01-22
**Status**: Complete

## R1: ChatGPT mapping ツリー構造の走査方法

### Question

ChatGPT の `mapping` ツリー構造をどのように走査して時系列順のメッセージリストを取得するか？

### Research Findings

ChatGPT エクスポートの構造を分析した結果:

```json
{
  "mapping": {
    "node_id_1": {
      "id": "node_id_1",
      "message": {...},
      "parent": null,
      "children": ["node_id_2"]
    },
    "node_id_2": {
      "id": "node_id_2",
      "message": {...},
      "parent": "node_id_1",
      "children": ["node_id_3"]
    }
  },
  "current_node": "node_id_3"
}
```

- `mapping` はノード ID をキーとした辞書
- 各ノードに `parent` と `children` がある
- `current_node` が会話の最終ノード
- ユーザーの編集で分岐（複数 children）が発生する可能性あり

### Decision

`current_node` から `parent` を辿って逆順でメッセージを収集する。

### Rationale

- `current_node` が「現在の会話状態」を表す
- 分岐がある場合でも、`current_node` からのパスが正しい会話履歴
- children を辿ると分岐で迷う可能性がある

### Algorithm

```python
def traverse_messages(mapping: dict, current_node: str) -> list[dict]:
    """mapping ツリーを current_node から逆順に走査"""
    messages = []
    node_id = current_node
    while node_id:
        node = mapping.get(node_id, {})
        msg = node.get('message')
        if msg and msg.get('author', {}).get('role') != 'system':
            messages.append(msg)
        node_id = node.get('parent')
    return list(reversed(messages))  # 時系列順に
```

---

## R2: ZIP 展開戦略

### Question

100MB を超える ZIP ファイルをどのように効率的に処理するか？

### Research Findings

- Python `zipfile` モジュールはストリーミング読み込みをサポート
- `ZipFile.read(name)` で個別ファイルをメモリに読み込み
- 全体を展開せずに必要なファイルのみ読み込み可能

### Decision

Python 標準ライブラリ `zipfile` を使用し、`conversations.json` のみを読み込む。

### Rationale

- 外部依存なし
- 画像・音声ファイルは初期リリースでは不要
- メモリ効率: 必要なファイルのみ読み込み

### Implementation

```python
import zipfile
import json

def read_conversations_from_zip(zip_path: Path) -> list[dict]:
    with zipfile.ZipFile(zip_path, 'r') as zf:
        with zf.open('conversations.json') as f:
            return json.load(f)
```

---

## R3: provider 切り替え設計

### Question

Claude と ChatGPT の両方をサポートするためにどのような設計が適切か？

### Alternatives Considered

1. **別コマンド**: `make import-claude` / `make import-chatgpt`
   - 長所: シンプル
   - 短所: コード重複、Makefile 肥大化

2. **ファイル拡張子で自動判定**: .json → Claude, .zip → ChatGPT
   - 長所: ユーザー操作が簡単
   - 短所: 曖昧さが残る（ZIP 内に JSON がある）

3. **`--provider` オプション**: 明示的に指定
   - 長所: 明確、拡張性あり
   - 短所: ユーザーが指定する必要

### Decision

オプション 3: `--provider` オプションを採用。

### Rationale

- 明確で曖昧さがない
- 将来的に Gemini, GPT-4 API 等も追加可能
- デフォルトは `claude` で既存動作を維持

### Implementation

```python
# cli.py
@click.option('--provider', default='claude',
              type=click.Choice(['claude', 'chatgpt']),
              help='LLM provider (default: claude)')
def import_command(input_path, provider, ...):
    phase = ImportPhase(provider=provider)
    ...
```

---

## R4: メッセージロール変換

### Question

ChatGPT の `author.role` を既存の ProcessingItem 形式にどう変換するか？

### Research Findings

ChatGPT のロール:
- `user`: ユーザーメッセージ
- `assistant`: AI レスポンス
- `system`: システムプロンプト（非表示）
- `tool`: ツール呼び出し結果

Claude の sender:
- `human`: ユーザー
- `assistant`: AI

### Decision

| ChatGPT | 変換後 | 処理 |
|---------|--------|------|
| user | human | Markdown 出力時に変換 |
| assistant | assistant | そのまま |
| system | - | 除外（出力しない） |
| tool | - | 除外（出力しない） |

### Rationale

- `system` は内部的なプロンプトで、ユーザーに表示する価値がない
- `tool` は機能呼び出しの中間結果で、最終レスポンスに含まれる

---

## R5: タイムスタンプ変換

### Question

ChatGPT の Unix timestamp を既存形式に変換する方法は？

### Research Findings

ChatGPT:
```json
"create_time": 1767407153.345896
```

Claude:
```json
"created_at": "2026-01-02T12:05:53.345896+00:00"
```

出力 frontmatter:
```yaml
created: 2026-01-02
```

### Decision

Unix timestamp → datetime → YYYY-MM-DD 形式

### Implementation

```python
from datetime import datetime, timezone

def convert_timestamp(ts: float | None) -> str:
    if ts is None:
        return datetime.now().strftime("%Y-%m-%d")
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")
```

---

## R6: マルチモーダルコンテンツ処理

### Question

画像・音声を含むメッセージをどう処理するか？

### Research Findings

ChatGPT のマルチモーダルメッセージ:
```json
{
  "content": {
    "content_type": "multimodal_text",
    "parts": [
      {
        "content_type": "image_asset_pointer",
        "asset_pointer": "sediment://file_xxxxx",
        "size_bytes": 292065
      },
      "テキスト部分"
    ]
  }
}
```

### Decision

Phase 1 (MVP): 画像・音声はプレースホルダーとして記録

```markdown
[Image: file_xxxxx (292KB)]

テキスト部分
```

### Rationale

- 初期リリースではテキスト抽出が優先
- 画像処理は将来的に検討（Obsidian への添付）

---

## Summary

| Research Item | Decision |
|--------------|----------|
| R1: mapping 走査 | `current_node` → `parent` 逆順走査 |
| R2: ZIP 展開 | `zipfile` 標準ライブラリ、`conversations.json` のみ |
| R3: provider 切り替え | `--provider` オプション（default: claude） |
| R4: ロール変換 | user→human, assistant→assistant, system/tool→除外 |
| R5: タイムスタンプ | Unix → YYYY-MM-DD |
| R6: マルチモーダル | プレースホルダー記録（Phase 1 MVP） |
