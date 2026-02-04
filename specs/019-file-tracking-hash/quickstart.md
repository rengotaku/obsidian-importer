# Quickstart: ファイル追跡ハッシュID

**Date**: 2026-01-17
**Branch**: `019-file-tracking-hash`

## Overview

ファイル処理時に一意のハッシュIDを生成し、ログに記録することでファイル名変更後も追跡可能にする。

## 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `models.py` | `ProcessingResult` に `file_id` フィールド追加 |
| `processing/single.py` | ハッシュID生成関数追加、処理結果に `file_id` 設定 |
| `state/manager.py` | `update_state` で `file_id` をログに含める |
| `tests/test_file_id.py` | 新規テスト |

## 実装手順

### Step 1: models.py 修正

```python
class ProcessingResult(TypedDict):
    # ... 既存フィールド ...
    file_id: str | None  # 追加
```

### Step 2: single.py にハッシュID生成追加

```python
import hashlib

def generate_file_id(content: str, filepath: Path) -> str:
    """ファイルコンテンツと初回パスからハッシュIDを生成"""
    relative_path = str(filepath.relative_to(PROJECT_ROOT))
    hash_input = f"{content}\n---\n{relative_path}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
```

### Step 3: manager.py 修正

```python
def update_state(state: dict, result: "ProcessingResult") -> dict:
    state["processed"].append({
        "file": result["file"],
        "file_id": result.get("file_id"),  # 追加
        "status": "success" if result["success"] else "error",
        "destination": result["destination"],
        "timestamp": result["timestamp"]
    })
    # ... errors にも同様に file_id 追加 ...
```

## テスト実行

```bash
make test
```

## 検証方法

```bash
# 処理実行後、processed.json を確認
cat .staging/@plan/*/processed.json | jq '.[].file_id'
```

## 期待される出力

```json
{
  "file": "test.md",
  "file_id": "abc123def456",
  "status": "success",
  "destination": "Vaults/エンジニア/test.md",
  "timestamp": "2026-01-17T10:30:00"
}
```
