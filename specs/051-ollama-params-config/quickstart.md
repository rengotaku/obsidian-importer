# Quickstart: Ollama パラメーター関数別設定

**Feature**: 051-ollama-params-config
**Date**: 2026-02-15

## 概要

関数ごとに異なるOllamaパラメーターを設定できるようになりました。これにより:

- `extract_knowledge`: 長文出力に対応した設定
- `translate_summary`: 中程度の出力に対応した設定
- `extract_topic`: 短い出力（1-3単語）に最適化した設定

## 基本設定

`conf/base/parameters.yml`:

```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1
```

## 関数別設定

```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1

  functions:
    extract_knowledge:
      num_predict: 16384    # 長文出力用
      timeout: 300          # 長いタイムアウト

    translate_summary:
      num_predict: 1024     # 中程度出力

    extract_topic:
      model: "llama3.2:3b"  # 軽量モデル
      num_predict: 64       # 短い出力
      timeout: 30           # 短いタイムアウト
```

## 使用例

### デフォルト設定のみ

最小構成。すべての関数がデフォルト値を使用:

```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
```

### 特定の関数のみオーバーライド

`extract_topic` のみ設定を変更:

```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"

  functions:
    extract_topic:
      num_predict: 64
```

### CLI でのオーバーライド

```bash
# 全関数のデフォルトモデルを変更
kedro run --params='{"ollama": {"defaults": {"model": "oss-gpt:20b"}}}'

# extract_knowledge の num_predict を変更
kedro run --params='{"ollama": {"functions": {"extract_knowledge": {"num_predict": 32768}}}}'
```

## パラメーター一覧

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `"gemma3:12b"` | 使用するモデル名 |
| `base_url` | string | `"http://localhost:11434"` | Ollama サーバー URL |
| `timeout` | int | `120` | タイムアウト秒数 (1-600) |
| `temperature` | float | `0.2` | サンプリング温度 (0.0-2.0) |
| `num_predict` | int | `-1` | 最大出力トークン数 (-1 = 無制限) |

## 推奨設定

### 知識抽出 (`extract_knowledge`)

詳細なMarkdown出力を生成するため、十分な出力トークン数が必要:

```yaml
extract_knowledge:
  num_predict: 16384  # 約4000文字相当
  timeout: 300        # 5分
```

### 要約翻訳 (`translate_summary`)

英語要約を日本語に翻訳。元の要約より長くなることは稀:

```yaml
translate_summary:
  num_predict: 1024  # 約250文字相当
```

### トピック抽出 (`extract_topic`)

1-3単語のトピック名を抽出。軽量モデルで十分:

```yaml
extract_topic:
  model: "llama3.2:3b"  # 高速な軽量モデル
  num_predict: 64       # 約15文字相当
  timeout: 30           # 30秒
```

## トラブルシューティング

### 出力が途切れる

`num_predict` を増やす:

```yaml
ollama:
  functions:
    extract_knowledge:
      num_predict: 32768  # デフォルトの2倍
```

### タイムアウトエラー

`timeout` を延長:

```yaml
ollama:
  functions:
    extract_knowledge:
      timeout: 600  # 10分
```

### モデルが見つからない

Ollamaにモデルがインストールされているか確認:

```bash
ollama list
ollama pull gemma3:12b
```

## 移行ガイド

### 既存設定からの移行

**Before**:
```yaml
import:
  ollama:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
```

**After**:
```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1
```

既存の `import.ollama` と `organize.ollama` は引き続きサポートされますが、新しい `ollama.defaults` 構造への移行を推奨します。
