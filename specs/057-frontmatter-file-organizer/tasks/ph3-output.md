# Phase 3 Output

## 作業概要
- User Story 2 - ファイル振り分け実行の実装完了
- FAIL テスト 14 件を PASS させた
- ファイル移動機能を実装し、全 382 テストが成功

## 修正ファイル一覧
- `scripts/organize_files.py` - 以下の関数を追加実装
  - `get_destination_path()`: frontmatter の genre/topic から振り分け先パスを計算
  - `move_file()`: ファイル移動処理（ディレクトリ自動作成、既存ファイルスキップ）
  - `organize_files()`: バッチファイル処理と処理サマリー生成
  - `execute_mode()`: 実行モード CLI ハンドラー（サマリー表示）
  - `shutil` モジュールをインポート

- `specs/057-frontmatter-file-organizer/tasks.md` - T042-T047 を完了マーク

## 実装詳細

### get_destination_path()
- genre が空 or なし → `unclassified` フォルダ直下に配置
- genre あり、topic なし → genre フォルダ直下に配置
- genre あり、topic あり → `genre_ja/topic_safe/filename` パス生成
- topic の特殊文字（`/\:*?"<>|`）をアンダースコアに置換

### move_file()
- source 存在確認（なければ "error" 返却）
- dest 既存チェック（あれば "skipped" 返却）
- dest 親ディレクトリ自動作成（`mkdir(parents=True)`）
- `shutil.move()` でファイル移動
- 成功時 "success" 返却

### organize_files()
- `scan_files()` でファイル一覧取得
- 各ファイルに対して振り分け先パス計算 → 移動処理
- ProcessingSummary 形式の dict 返却
  - `total`, `success`, `skipped`, `error` カウント
  - `by_genre`: ジャンル別成功件数

### execute_mode()
- CLI 引数から入出力パス解決
- `organize_files()` 呼び出し
- 処理サマリー表示（日本語）

## テスト結果

### 全テスト PASS
```
Ran 382 tests in 5.526s
OK
```

### Phase 3 で追加されたテスト（14 件）
| テストクラス | テスト数 | 内容 |
|-------------|---------|------|
| TestGetDestinationPath | 6 | パス計算ロジック（genre/topic 組み合わせ） |
| TestMoveFile | 4 | ファイル移動処理（成功/スキップ/エラー） |
| TestOrganizeFiles | 4 | バッチ処理とサマリー生成 |

## 注意点

### 次 Phase (Phase 4) で必要な情報
- 現在のパス解決は `args.input` or `config["default_input"]` の優先順位
- Phase 4 では `~` 展開を含むカスタムパス指定機能を追加
- `resolve_paths()` 関数を新規実装予定

### 実装のミス・課題
- なし（全テスト PASS、期待動作を満たす）

## 次のステップ

Phase 4 タスク:
- T051: Phase 3 output 読み込み
- T052-T055: カスタムパス指定テスト実装 (RED)
- T058-T062: `resolve_paths()` 実装、Makefile 更新 (GREEN)
