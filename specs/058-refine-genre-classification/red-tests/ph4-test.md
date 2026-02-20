# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - FR-008 ジャンル分布ログ出力
- FAIL テスト数: 5
- テストファイル: tests/pipelines/organize/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_nodes.py | test_log_genre_distribution_logs_counts | 各ジャンルの件数がログ出力される |
| test_nodes.py | test_log_genre_distribution_logs_percentages | 各ジャンルの割合（%）がログ出力される |
| test_nodes.py | test_log_genre_distribution_empty_input | 空入力でもエラーにならない |
| test_nodes.py | test_log_genre_distribution_single_genre | 全て同一ジャンルの場合 100.0% と表示 |
| test_nodes.py | test_log_genre_distribution_returns_input | 入力をそのまま返す（パススルー） |

## 実装ヒント
- `log_genre_distribution(partitioned_input, params)` 関数を `src/obsidian_etl/pipelines/organize/nodes.py` に追加
- partitioned_input は PartitionedDataset 形式（dict of callables）
- 各 callable を呼び出して item dict を取得し、`genre` フィールドを集計
- `collections.Counter` で件数カウント、総数で割って割合を計算
- `logger.info()` でジャンル名、件数、割合を出力
- 入力の partitioned_input をそのまま返す（パイプライン接続用）
- 既存の `logger = logging.getLogger(__name__)` を使用

## FAIL 出力例
```
ERROR: tests.pipelines.organize.test_nodes (unittest.loader._FailedTest.tests.pipelines.organize.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.pipelines.organize.test_nodes
ImportError: cannot import name 'log_genre_distribution' from 'obsidian_etl.pipelines.organize.nodes'
```
