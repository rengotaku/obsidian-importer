# Data Model: データレイヤー分離

**Feature**: 064-data-layer-separation
**Date**: 2026-03-03

## ディレクトリ構造

### Before (現状)

```
data/
├── 01_raw/                    # ZIP ファイル
├── 02_intermediate/           # パース済み JSON
├── 03_primary/                # LLM 処理済み JSON
└── 07_model_output/           # ⚠️ JSON と MD が混在
    ├── classified/            # JSON (中間)
    ├── cleaned/               # JSON (中間)
    ├── normalized/            # JSON (中間)
    ├── topic_extracted/       # JSON (中間)
    ├── vault_determined/      # JSON (中間)
    ├── organized/             # JSON + MD (混在)
    ├── notes/                 # MD (最終)
    └── review/                # MD (最終)
```

### After (変更後)

```
data/
├── 01_raw/                    # ZIP ファイル
├── 02_intermediate/           # パース済み JSON
├── 03_primary/                # LLM 処理済み JSON
├── 05_model_input/            # ✅ 新規: JSON 中間データ
│   ├── classified/            # ジャンル分類済み
│   ├── cleaned/               # クリーニング済み
│   ├── normalized/            # 正規化済み
│   ├── topic_extracted/       # トピック抽出済み
│   ├── vault_determined/      # Vault 決定済み
│   └── organized/             # 整理済み (JSON のみ)
└── 07_model_output/           # ✅ MD のみ
    ├── notes/                 # 通常出力
    ├── review/                # レビュー対象
    └── organized/             # ジャンル分類済み出力
```

## データセットマッピング

### 05_model_input (JSON)

| データセット名 | パス | 説明 |
|---------------|------|------|
| classified_items | 05_model_input/classified/ | ジャンル分類結果 |
| existing_classified_items | 05_model_input/classified/ | 読み取り専用参照 |
| topic_extracted_items | 05_model_input/topic_extracted/ | トピック抽出結果 |
| normalized_items | 05_model_input/normalized/ | 正規化済みデータ |
| cleaned_items | 05_model_input/cleaned/ | クリーニング済みデータ |
| vault_determined_items | 05_model_input/vault_determined/ | Vault 決定済みデータ |
| organized_items | 05_model_input/organized/ | 整理済みデータ (JSON) |

### 07_model_output (MD)

| データセット名 | パス | 説明 |
|---------------|------|------|
| markdown_notes | 07_model_output/notes/ | 通常の Markdown 出力 |
| review_notes | 07_model_output/review/ | レビュー対象出力 |
| organized_notes | 07_model_output/organized/ | ジャンル別 Markdown |
| organized_files | 07_model_output/organized/ | ジャンル別ファイル |

## JSON スキーマ

### classified_items

```json
{
  "file_id": "string (SHA256)",
  "metadata": {
    "file_id": "string",
    "created": "string (ISO date)",
    "source": "string (claude|openai|github)"
  },
  "genre": "string (ジャンル名)",
  "confidence": "number (0-1)"
}
```

### normalized_items

```json
{
  "file_id": "string (SHA256)",
  "metadata": {
    "file_id": "string",
    "created": "string (ISO date)",
    "title": "string"
  },
  "content": "string (Markdown)",
  "tags": ["string"]
}
```

## 移行マッピング

| 移行元 | 移行先 |
|--------|--------|
| 07_model_output/classified/*.json | 05_model_input/classified/*.json |
| 07_model_output/cleaned/*.json | 05_model_input/cleaned/*.json |
| 07_model_output/normalized/*.json | 05_model_input/normalized/*.json |
| 07_model_output/topic_extracted/*.json | 05_model_input/topic_extracted/*.json |
| 07_model_output/vault_determined/*.json | 05_model_input/vault_determined/*.json |
| 07_model_output/organized/*.json | 05_model_input/organized/*.json |

**注意**: `07_model_output/organized/*.md` は移行しない（そのまま維持）
