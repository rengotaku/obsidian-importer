# Research: ファイル追跡ハッシュID

**Date**: 2026-01-17
**Branch**: `019-file-tracking-hash`

## Research Questions

### Q1: ハッシュアルゴリズムの選択

**Decision**: SHA-256（標準ライブラリ hashlib）

**Rationale**:
- Python標準ライブラリで追加依存なし
- 衝突耐性が十分（2^128の衝突確率）
- 処理速度が実用的（数KB〜数十KBのテキストファイルで < 1ms）

**Alternatives Considered**:
| アルゴリズム | 却下理由 |
|-------------|---------|
| MD5 | 衝突脆弱性、セキュリティ用途には不適 |
| SHA-1 | 衝突攻撃が実証済み |
| BLAKE3 | 追加依存が必要 |

### Q2: ハッシュ入力の構成

**Decision**: コンテンツ + 初回パス（相対パス）

**Rationale**:
- ファイルごとに一意性を保証（同一コンテンツでも異なるID）
- パス変更後も追跡可能（初回パスで固定）
- 相対パスを使用し、プロジェクト移動に耐性

**Implementation**:
```python
hash_input = f"{content}\n---\n{relative_path}"
file_id = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
```

**Alternatives Considered**:
| 方式 | 却下理由 |
|------|---------|
| コンテンツのみ | 同一コンテンツで重複ID発生 |
| UUID | コンテンツとの関連がない |
| コンテンツ + 現在パス | パス変更でID変化、追跡不可 |

### Q3: ID長の決定

**Decision**: 12文字（SHA-256の先頭48ビット）

**Rationale**:
- 衝突確率: 1万ファイルで約 1.8×10^-9（十分低い）
- 可読性: ログ表示時に扱いやすい長さ
- 例: `abc123def456`

**Alternatives Considered**:
| 長さ | 判断 |
|------|------|
| 8文字 | 衝突確率がやや高い（1万ファイルで ~2×10^-6） |
| 16文字 | 過剰、可読性低下 |
| 全長64文字 | ログが冗長 |

### Q4: 既存コードへの統合ポイント

**Decision**: 3箇所の最小限変更

1. **models.py**: `ProcessingResult` に `file_id: str | None` 追加
2. **processing/single.py**: `process_single_file` でハッシュID生成
3. **state/manager.py**: `update_state` で `file_id` をログに含める

**Rationale**:
- 既存アーキテクチャを尊重
- 後方互換性維持（`file_id` はオプショナル）
- テスト影響を最小化

## Summary

| 決定事項 | 選択 |
|---------|------|
| ハッシュアルゴリズム | SHA-256 |
| ハッシュ入力 | コンテンツ + 初回相対パス |
| ID長 | 12文字 |
| 統合ポイント | models.py, single.py, manager.py |
