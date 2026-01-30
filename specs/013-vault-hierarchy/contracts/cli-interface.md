# CLI Interface Contract: hierarchy_organizer.py

**Date**: 2026-01-15
**Feature**: 013-vault-hierarchy

## Command Synopsis

```bash
python .claude/scripts/hierarchy_organizer.py [OPTIONS] [VAULT]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| VAULT | No | 対象Vault名（省略時: 全Vault） |

## Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--dry-run` | `-n` | flag | true | プレビューのみ（移動しない） |
| `--execute` | `-x` | flag | false | 実際にファイルを移動 |
| `--output` | `-o` | path | stdout | 結果出力先（CSV/JSON） |
| `--format` | `-f` | enum | csv | 出力形式（csv/json） |
| `--limit` | `-l` | int | 0 | 処理ファイル数上限（0=無制限） |
| `--confidence` | `-c` | float | 0.5 | 分類確信度の閾値 |
| `--new-folders` | | flag | false | 新規フォルダ作成を許可 |
| `--verbose` | `-v` | flag | false | 詳細ログ出力 |

## Usage Examples

### 1. ドライラン（プレビュー）

```bash
# エンジニアVaultのみプレビュー
python .claude/scripts/hierarchy_organizer.py エンジニア

# 全Vaultプレビュー、CSV出力
python .claude/scripts/hierarchy_organizer.py -o preview.csv
```

### 2. 実行

```bash
# エンジニアVaultを階層化
python .claude/scripts/hierarchy_organizer.py -x エンジニア

# 10件だけテスト実行
python .claude/scripts/hierarchy_organizer.py -x -l 10 エンジニア
```

### 3. 新規フォルダ許可

```bash
# LLMが提案する新規フォルダも作成
python .claude/scripts/hierarchy_organizer.py -x --new-folders エンジニア
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | 正常終了 |
| 1 | 引数エラー |
| 2 | Vault不存在 |
| 3 | LLM接続エラー |
| 4 | ファイル操作エラー |

## Output Format

### CSV (--format csv)

```csv
ファイル名,現在位置,提案先,確信度,理由,新規フォルダ,ステータス
Dockerの基本,エンジニア/,エンジニア/Docker/,0.92,Docker関連,No,pending
```

### JSON (--format json)

```json
{
  "session_id": "20260115_143052",
  "vault": "エンジニア",
  "mode": "dry-run",
  "results": [
    {
      "file": "Dockerの基本.md",
      "source": "エンジニア/",
      "dest": "エンジニア/Docker/",
      "confidence": 0.92,
      "reason": "Docker関連技術メモ",
      "is_new_folder": false,
      "status": "pending"
    }
  ],
  "summary": {
    "total": 50,
    "to_move": 48,
    "to_skip": 2,
    "new_folders": 0
  }
}
```

## Integration with Existing Scripts

### ollama_genre_classifier.py との連携

`hierarchy_organizer.py` は内部で `ollama_genre_classifier.py` のLLM呼び出しロジックを再利用。

変更点:
- `SYSTEM_PROMPT` にサブフォルダ判定を追加
- 出力JSONに `subfolder` フィールドを追加

### Makefileターゲット

```makefile
# 追加ターゲット
hierarchy-preview:
	$(PYTHON) .claude/scripts/hierarchy_organizer.py

hierarchy-execute:
	$(PYTHON) .claude/scripts/hierarchy_organizer.py -x

hierarchy-engineer:
	$(PYTHON) .claude/scripts/hierarchy_organizer.py -x エンジニア
```
