# Research: ジャンル定義の動的設定

**Date**: 2026-02-22
**Branch**: `060-dynamic-genre-config`

## 1. 設定形式の設計

### Decision: ネスト形式の YAML 構造

**選択**: 各ジャンルを辞書形式で定義（vault + description）

```yaml
genre_vault_mapping:
  ai:
    vault: "エンジニア"
    description: "AI/機械学習/LLM/生成AI"
```

**Rationale**:
- 一元管理: ジャンル定義と Vault マッピングを同じ場所で管理
- 拡張性: 将来的に他のフィールド（priority, aliases など）を追加可能
- 可読性: コメントより構造化されたデータが扱いやすい

**Alternatives considered**:
1. 別ファイル分離（genre_definitions.yml + genre_vault_mapping.yml）→ 管理負荷増
2. フラット形式（ai_vault, ai_description）→ スケールしない
3. 既存コメントを YAML パーサーで抽出 → 非標準、脆弱

## 2. プロンプト動的生成

### Decision: パラメータから直接生成

**選択**: `_build_genre_prompt(genre_definitions)` 関数でプロンプト文字列を動的構築

```python
def _build_genre_prompt(genre_definitions: dict) -> str:
    lines = []
    for genre, config in genre_definitions.items():
        desc = config.get("description", genre)
        lines.append(f"- {genre}: {desc}")
    return "\n".join(lines)
```

**Rationale**:
- シンプル: 文字列操作のみ、外部依存なし
- テスト容易: 純粋関数として単体テスト可能
- パフォーマンス: 毎回生成しても無視できるコスト

**Alternatives considered**:
1. Jinja2 テンプレート → 過剰な依存追加
2. 設定ファイルにプロンプト全文 → 柔軟性低下
3. LLM にジャンル定義を別途送信 → 複雑化

## 3. other 分析のトリガー

### Decision: パイプライン終了時に条件付き実行

**選択**: import パイプライン完了後、other が5件以上なら分析ノードを実行

**Rationale**:
- 自然なタイミング: 分類完了後にまとめて分析
- 効率的: 条件を満たさない場合は LLM 呼び出しなし
- ユーザー体験: `make run` 完了時に提案が得られる

**Alternatives considered**:
1. 別コマンド（`make analyze-genres`）→ 手動実行が必要
2. リアルタイム分析（各ファイル処理時）→ 非効率
3. 定期バッチ → 過剰な仕組み

## 4. 新ジャンル提案の出力形式

### Decision: Markdown レポートファイル

**選択**: `data/07_model_output/genre_suggestions.md` に出力

```markdown
# ジャンル提案レポート

**生成日時**: 2026-02-22 12:34:56
**other 分類数**: 8件

## 提案 1: finance

**Description**: 投資/資産運用/金融商品

**該当コンテンツ**:
- 株式投資の基本
- NISA vs iDeCo 比較
- ...

---
```

**Rationale**:
- 可読性: Markdown で人間が読みやすい
- 永続性: ファイルとして保存、後で参照可能
- シンプル: 特別なフォーマットなし

**Alternatives considered**:
1. JSON 出力 → 機械可読だが人間には不便
2. YAML 出力 → そのままコピペできるが冗長
3. コンソール出力のみ → 流れてしまう

## 5. 後方互換性

### Decision: 旧形式はサポートしない

**選択**: 新形式（ネスト）のみサポート。旧形式（フラット）は移行ガイドを提供。

**Rationale**:
- 旧形式はすでに使用されていない（Issue#28 で削除済み）
- 移行コストは低い（設定ファイル1つ）
- コードの複雑さを避ける

**Alternatives considered**:
1. 両形式サポート → コード複雑化
2. 自動マイグレーション → 過剰な機能

## 6. エラーハンドリング

### Decision: 警告 + フォールバック

**選択**:
- description 欠落 → 警告出力、ジャンル名のみで動作
- vault 欠落 → エラー、パイプライン停止
- genre_vault_mapping 未定義 → other のみでフォールバック

**Rationale**:
- description は任意（なくても動作可能）
- vault は必須（出力先が不明では動作不可）
- 完全な設定欠落は警告だが動作継続（デグレード）

## 未解決事項

なし（すべて解決済み）
