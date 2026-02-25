---
name: kedro-pipeline-lateral-fix
description: "After fixing a Kedro pipeline node input, check other pipelines for the same pattern"
---

# Kedro Pipeline Lateral Fix

## Problem

Kedro パイプラインで `params:section` → `parameters` の修正を1つのパイプラインで行ったが、他のパイプラインに同じパターンが残っていた。

## Solution

パイプライン修正後、他パイプラインを即座に検索:

```bash
Grep: pattern="params:" path="src/**/pipeline.py"
```

## Checklist

- [ ] 修正したパイプラインと同じ入力パターンを検索
- [ ] `src/**/pipelines/*/pipeline.py` を全て確認
- [ ] 同じノード入力パターン（`params:xxx`）を全て修正

## When to Use

- Kedro ノードの入力定義を修正した直後
- `params:section` 関連のエラーを修正した時
