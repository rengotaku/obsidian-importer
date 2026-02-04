# Research: LLM Multi-Stage Processing

**Feature**: 007-llm-multi-stage
**Date**: 2026-01-13
**Status**: Complete

## Research Questions

### RQ1: 最適な段階分割数は？

**Decision**: 4段階（Dust判定 → ジャンル分類 → 正規化 → タイトル/タグ生成）

**Rationale**:
- 各段階の出力JSONが小さく単純になる（2-5フィールド）
- 段階間の依存関係が明確（正規化後のコンテンツからタイトル生成）
- dustファイルは1段階で終了し、LLM呼び出しを節約

**Alternatives Considered**:
| 分割数 | メリット | デメリット | 却下理由 |
|--------|---------|-----------|----------|
| 2段階 | LLM呼び出し少 | 各段階のJSONが複雑 | エラー率改善効果が薄い |
| 3段階 | バランス良い | 正規化とタイトル生成の分離なし | タイトル品質が向上しない |
| 5段階以上 | 各段階が極めて単純 | 処理時間増大、段階間調整複雑 | オーバーエンジニアリング |

---

### RQ2: 処理順序はどうあるべきか？

**Decision**: Pre-processing → Dust → ジャンル → 正規化 → タイトル/タグ → Post-processing

**Rationale**:
1. **英語判定はPre-processing**: 正規化で翻訳されると判定不能
2. **正規化はタイトル生成の前**: きれいなコンテンツからより適切なタイトル・タグを生成
3. **ジャンル情報は正規化に活用**: ジャンルに応じた整形が可能

**Alternatives Considered**:
| 順序パターン | 却下理由 |
|-------------|----------|
| タイトル → 正規化 | 冗長な表現がタイトルに影響 |
| 正規化 → ジャンル | ジャンル情報を正規化に活用できない |
| 英語判定を正規化後 | 翻訳されると判定不能 |

---

### RQ3: 各段階のJSON出力形式は？

**Decision**: 各段階で最小限のフィールドのみ

**Stage 1 (Dust判定)**:
```json
{
  "is_dust": false,
  "dust_reason": null,
  "confidence": 0.95
}
```

**Stage 2 (ジャンル分類)**:
```json
{
  "genre": "エンジニア",
  "confidence": 0.85,
  "related_keywords": ["Python", "CLI", "automation"]
}
```

**Stage 3 (正規化)**:
```json
{
  "normalized_content": "## 見出し\n\n本文...",
  "improvements_made": ["冗長表現を簡潔化", "見出しレベル調整"]
}
```

**Stage 4 (タイトル/タグ)**:
```json
{
  "title": "Pythonでの自動化スクリプト作成",
  "tags": ["python", "automation", "cli"]
}
```

**Rationale**:
- 各段階のJSONが2-4フィールドのみ
- パース失敗時の原因特定が容易
- 段階ごとにリトライ可能

---

### RQ4: リトライ戦略は？

**Decision**: 段階別リトライ、最大3回、失敗時はデフォルト値で継続

**Rationale**:
- ローカルLLMは一時的な不安定性がある
- 同じプロンプトでも再試行で成功することが多い
- 全段階失敗よりデフォルト値で継続する方がユーザー体験が良い

**リトライ後のデフォルト値**:
| Stage | デフォルト値 |
|-------|-------------|
| Stage 1 | `is_dust: false`（価値ありと仮定） |
| Stage 2 | `genre: "その他"`, `confidence: 0.5` |
| Stage 3 | 元のコンテンツをそのまま使用 |
| Stage 4 | ファイル名から生成、タグ空 |

---

### RQ5: Pre-processingで除外すべきパターンは？

**Decision**: 以下のルールベース判定でLLM呼び出しを回避

| パターン | 判定基準 | 結果 |
|---------|---------|------|
| 空ファイル | `len(content.strip()) == 0` | 即dust |
| 極短文 | 50文字未満 | 即dust |
| テンプレート残骸 | `[TODO]`, `Lorem ipsum`, `PLACEHOLDER` | 即dust |
| 英語文書 | 既存 `is_complete_english_document()` | フラグ設定 |

**Rationale**:
- 明らかなdustにLLMを使う必要がない
- 処理時間の節約（0回のLLM呼び出しで完了）

---

### RQ6: 既存コードとの互換性は？

**Decision**: 最終出力形式は現行と同一の `NormalizationResult` を維持

**Rationale**:
- 呼び出し元（`process_single_file`, `process_all_files`）の変更を最小化
- ログ形式、状態管理の変更不要
- 段階的なリファクタリングが可能

**互換性維持ポイント**:
- `normalize_file()` の戻り値型は変更なし
- CLIオプションは変更なし
- ログ形式は変更なし（内部で段階別ログを追加可能）

---

## Best Practices Identified

### ローカルLLMプロンプト設計

1. **短く明確な指示**: 長いプロンプトより短い単一タスクの方が遵守率が高い
2. **出力形式の明示**: JSONスキーマを具体例で示す
3. **禁止事項より許可事項**: 「〜するな」より「〜のみ出力」

### JSONパース堅牢化

1. **コードブロック抽出優先**: ```json ... ``` を最優先で抽出
2. **括弧バランス追跡**: フォールバックとして最初の完全なJSONを抽出
3. **エラーコンテキスト**: パース失敗時に周辺文字列を記録

### 段階分割パターン

1. **早期終了条件**: dustなら後続処理をスキップ
2. **依存関係の明示**: 前段階の出力を次段階の入力に含める
3. **独立検証**: 各段階の出力を個別に検証

---

## Conclusion

Technical Contextに不明点なし。Phase 1に進む準備完了。
