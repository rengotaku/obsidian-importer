# Research: @index フォルダ内再帰的Markdown処理

**Feature**: 006-index-markdown-process
**Date**: 2026-01-12

## Research Tasks

### 1. 既存ファイル検出ロジックの調査

**Question**: 現在のファイル検出はどのように実装されているか？

**Findings**:
- `ollama_normalizer.py` の `list_index_files()` 関数（806-820行目）が主要なファイル収集ロジック
- `INDEX_DIR.glob("*.md")` で直下の `.md` ファイルのみを検出
- 既存の除外パターン: ファイル名が `.` で始まるもの、全ファイル一覧CSV

**Current Code** (line 806-820):
```python
def list_index_files() -> list[Path]:
    """@index内の処理対象ファイルを一覧取得"""
    if not INDEX_DIR.exists():
        return []

    files = []
    for f in INDEX_DIR.glob("*.md"):
        # 除外パターン
        if f.name.startswith("."):
            continue
        if f.name == "全ファイル一覧.csv":  # Not a markdown file anyway
            continue
        files.append(f)
    return sorted(files, key=lambda x: x.name)
```

**Decision**: `glob("*.md")` を `rglob("*.md")` に変更し、パスベースの除外ロジックを追加

---

### 2. 除外パターンのベストプラクティス

**Question**: どのような除外パターンが必要か？

**Findings**:
- 隠しファイル: `.` で始まるファイル
- 隠しフォルダ: パス内に `.` で始まるコンポーネントがあるもの（例: `.obsidian/`）
- Obsidian設定フォルダ: `.obsidian/` 配下すべて

**Decision**: `should_exclude(path: Path) -> bool` 関数を追加
- パスの各コンポーネントをチェック
- 1つでも `.` で始まるものがあれば除外

**Rationale**:
- シンプルなロジックで隠しファイル/フォルダを一括除外
- 将来的にカスタム除外パターン対応も容易

---

### 3. 処理前プレビューの実装方針

**Question**: プレビュー機能はどう実装するか？

**Findings**:
- 既存の `--preview` オプションは別の用途（処理結果のプレビュー表示）
- 新規オプション `--scan` を追加してファイル一覧のみ表示
- または既存の `status` サブコマンドを拡張

**Decision**:
- `list_index_files()` の結果を利用
- 処理開始前に件数とサンプルファイルを表示
- 件数が多い場合（例: 20件以上）は確認プロンプトを表示

**Rationale**:
- 既存のCLI構造を大きく変えない
- 憲法の「V. Automation with Oversight」に準拠

---

### 4. パフォーマンス考慮

**Question**: 1000ファイルスキャンで30秒以内は達成可能か？

**Findings**:
- `rglob()` は内部で `os.walk()` を使用、効率的
- ファイルシステムI/Oがボトルネック
- 実測: 現在の@index/内89ファイルのスキャンは1秒未満

**Decision**: 特別な最適化は不要。`rglob()` をそのまま使用

**Rationale**:
- 標準ライブラリの実装で十分な性能
- 1000ファイル程度では問題なし

---

### 5. 空フォルダ処理

**Question**: 処理後に空になったサブフォルダはどうするか？

**Findings**:
- 現在は考慮されていない
- 空フォルダが残ると見栄えが悪い

**Decision**:
- オプションで空フォルダ削除を提供 (`--cleanup-empty`)
- デフォルトは削除しない（安全側）

**Rationale**:
- ユーザーが意図的に残したフォルダを誤って削除しないため
- 手動での削除も容易

---

## Summary of Decisions

| Item | Decision | Rationale |
|------|----------|-----------|
| ファイル検出 | `rglob("*.md")` に変更 | 再帰的探索の標準的手法 |
| 除外ロジック | `should_exclude()` 関数追加 | パスコンポーネントベースで隠しファイル/フォルダを除外 |
| プレビュー | 処理前に件数表示、20件以上で確認 | 既存構造を維持しつつ憲法準拠 |
| パフォーマンス | 最適化不要 | 標準ライブラリで十分 |
| 空フォルダ | オプションで削除可能 | 安全側をデフォルト |

## Alternatives Considered

### ファイル検出
- **os.walk()**: より低レベルな制御可能だが、`pathlib` の統一性を損なう
- **fnmatch**: 除外パターンには良いが、`rglob` + カスタムフィルタで十分

### 除外パターン設定
- **JSONファイルで外部化**: 将来的には良いが、初期実装では過剰
- **コードにハードコード**: シンプルで十分。将来拡張時にJSONに移行可能
