# Phase 4 Output

## 作業概要
- Phase 4 - User Story 3 入出力パス指定 の実装完了
- FAIL テスト 4 件を PASS させた
- `resolve_paths()` 関数を実装し、カスタムパス指定と ~ 展開に対応

## 修正ファイル一覧
- `scripts/organize_files.py` - `resolve_paths()` 関数の追加、`preview_mode()` と `execute_mode()` の更新

## 実装詳細

### resolve_paths() 関数
- **署名**: `resolve_paths(config: dict, input_path: str | None, output_path: str | None) -> tuple[Path, Path]`
- **機能**:
  - `input_path` が `None` の場合、`config['default_input']` を使用
  - `output_path` が `None` の場合、`config['default_output']` を使用
  - パスに `~` が含まれる場合、`Path.expanduser()` でホームディレクトリに展開
  - `(input_path, output_path)` を `Path` オブジェクトのタプルとして返す

### preview_mode() と execute_mode() の更新
- 従来の直接パス解決を `resolve_paths()` 呼び出しに置き換え
- カスタムパス (`args.input`, `args.output`) と config デフォルトの統一的な処理
- `~` 展開が自動的に行われる

## テスト結果

### 全テスト PASS
```
Ran 386 tests in 5.448s
OK
```

### Phase 4 固有テスト (4件)
- `test_resolve_paths_defaults` - デフォルトパス使用 ✅
- `test_resolve_paths_custom_input` - カスタム input パス優先 ✅
- `test_resolve_paths_custom_output` - カスタム output パス優先 ✅
- `test_resolve_paths_expand_tilde` - ~ のホームディレクトリ展開 ✅

## Makefile 検証

### organize-preview ターゲット
```bash
make organize-preview INPUT=/tmp/input OUTPUT=/tmp/output
```
- カスタムパス指定が正常に動作することを確認 ✅

### ~ 展開
```bash
make organize-preview INPUT=~/test_input OUTPUT=~/test_output
```
- ~ が正しく展開されることを確認 ✅

## 注意点
- Makefile ターゲット (`organize-preview`, `organize`) は Phase 1 で実装済みのため、今回の変更は不要
- `conf/base/genre_mapping.yml` が存在しない場合、`.sample` からコピーする必要あり

## 次 Phase への引き継ぎ
- Phase 5 (Polish & Cross-Cutting Concerns) へ進む準備完了
- 全ユーザーストーリー (US1, US2, US3) が動作することを確認済み
- テストカバレッジは十分（386 テスト全 PASS）

## 実装のミス・課題
- なし（全テスト PASS、Makefile 検証も成功）
