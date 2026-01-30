# Quickstart: Extract Stage Discovery 委譲

**Feature**: 031-extract-discovery-delegation
**Date**: 2026-01-23

## 概要

この変更後、ChatGPT と Claude の両方のインポートが正しく動作します。

## 使用方法

### ChatGPT インポート

```bash
make import INPUT=/path/to/chatgpt_export.zip PROVIDER=openai
```

### Claude インポート

```bash
make import INPUT=/path/to/claude_export/ PROVIDER=claude
```

### provider オプション

`--provider` は必須です。省略するとエラーになります。

```bash
# エラー: provider が指定されていません
make import INPUT=/path/to/export
```

## 変更点

### ユーザー向け変更

- なし（CLI インターフェースは変更なし）

### 内部変更

1. **ClaudeExtractor**: `discover_items()` メソッドを追加
2. **ImportPhase**: Extract stage の `discover_items()` を呼び出すように変更
3. **ChatGPTExtractor**: 既存の `discover_items()` をそのまま使用

## 検証方法

```bash
# テスト実行
make test

# ChatGPT インポートテスト
make import INPUT=chatgpt_export.zip PROVIDER=openai LIMIT=5

# Claude インポートテスト
make import INPUT=claude_export/ PROVIDER=claude LIMIT=5
```

## トラブルシューティング

### "メッセージが含まれていません" が表示される

この問題はこの変更で修正されます。変更前は ChatGPT データが正しく処理されていませんでした。

### provider エラー

```
Error: provider is required. Use --provider claude or --provider openai
```

`--provider` オプションを指定してください。
