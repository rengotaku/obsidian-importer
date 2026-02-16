# Research: 050-fix-content-compression

**Date**: 2026-02-09

## 1. プロンプト改善のベストプラクティス

### Decision
プロンプトに「情報量の目安」と「省略禁止ルール」を明示的に追加する。

### Rationale
- LLM は明示的な指示がないと「要約」を優先し、情報を過度に圧縮する傾向がある
- 具体的な文字数目安を与えることで、出力量をコントロールできる
- 「省略禁止」の明示的な指示は、コード・手順の完全性を保証する

### Alternatives Considered
1. **few-shot examples の追加**: 効果的だがプロンプトが長くなりすぎる
2. **LLM パラメータ調整**: temperature, max_tokens 調整だけでは情報量は改善しない
3. **後処理での補完**: 一度失われた情報は後から補完できない

---

## 2. 圧縮率検証の実装パターン

### Decision
独立した関数 `validate_compression()` を作成し、各 node から呼び出す。

### Rationale
- デコレータパターンより明示的で、結果を node 内で活用しやすい
- `CompressionResult` dataclass で結果を構造化し、ログや判定に利用可能
- 共通処理として `utils/` に配置し、新規 node でも再利用可能

### Alternatives Considered
1. **デコレータパターン**: 暗黙的で結果の取り扱いが難しい
2. **Kedro Hook**: パイプライン全体に影響し、細かい制御が困難
3. **各 node に直接実装**: コードの重複、保守性の低下

---

## 3. PartitionedDataset の出力先分岐

### Decision
`format_markdown` node 内で条件分岐し、2つの異なる dict を返す。パイプライン定義で2つの PartitionedDataset に出力。

### Rationale
- Kedro の PartitionedDataset は単一の出力先を前提とする
- node の戻り値を分割することで、複数の出力先に対応可能
- `review_reason` フラグで出力先を決定するのが最もシンプル

### Implementation Pattern
```python
def format_markdown(...) -> tuple[dict[str, str], dict[str, str]]:
    """Returns (normal_output, review_output)"""
    normal = {}
    review = {}
    for key, item in items.items():
        if item.get("review_reason"):
            review[key] = format_item(item)
        else:
            normal[key] = format_item(item)
    return normal, review
```

### Alternatives Considered
1. **後処理で移動**: ファイル I/O が増え、冪等性が複雑になる
2. **カスタム Dataset**: 実装コストが高い
3. **パイプライン分岐**: 複雑度が増す

---

## 4. 既存コードの圧縮率チェック箇所

### 発見
`extract_knowledge` node に既に圧縮率チェックのコードが存在（lines 154-166）:

```python
# Check content compression ratio (detect abnormal shrinkage)
original_len = len(item["content"])
output_len = len(summary_content)
if original_len > 0:
    ratio = output_len / original_len * 100
    min_ratio = params.get("transform", {}).get("min_content_ratio", 5.0)
    if ratio < min_ratio:
        logger.warning(...)
        skipped_empty += 1
        continue
```

### Decision
既存の圧縮率チェックを `compression_validator.py` に移行し、以下を変更:
1. 段階的しきい値（元サイズ依存）に変更
2. `continue` せず `review_reason` を付与して処理を継続
3. 共通関数として抽出し、他の node でも利用可能に

---

## Summary

| 研究課題 | 決定 | 理由 |
|---------|------|------|
| プロンプト改善 | 情報量目安 + 省略禁止ルール追加 | LLM の過度な要約を防止 |
| 圧縮率検証 | 独立関数 + CompressionResult | 明示的、再利用可能 |
| 出力先分岐 | node で分割、2つの PartitionedDataset | シンプル、Kedro 標準パターン |
| 既存コード | compression_validator に移行 | 一元化、段階的しきい値 |
