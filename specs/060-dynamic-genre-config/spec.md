# Feature Specification: ジャンル定義の動的設定

**Feature Branch**: `060-dynamic-genre-config`
**Created**: 2026-02-22
**Status**: Draft
**Input**: LLMのgenreの恒久的な更新

## 背景

現在の実装では、ジャンル定義（ai, devops, engineer 等）と説明文がコード内にハードコードされている。ユーザーがジャンルを追加・変更するにはコード修正が必要であり、拡張性に欠ける。また、「other」に分類されたコンテンツが蓄積し、適切なジャンルへの振り分けが行われない問題がある。

## Clarifications

### Session 2026-02-22

- Q: other 改善サイクルの自動化レベル → A: 自動提案（other が一定数以上の場合、LLM が新ジャンル候補と description を提案）
- Q: 自動提案のトリガー条件 → A: 5件以上
- Q: 新ジャンル提案の実行タイミング → A: `make run` 完了後（import パイプライン終了時）
- Q: 新ジャンル提案の出力先 → A: 専用レポートファイル `data/07_model_output/genre_suggestions.md`
- Q: 提案されたジャンルの適用方法 → A: 手動編集（ユーザーが提案を参照し YAML を手動編集）

## User Scenarios & Testing

### User Story 1 - ジャンル定義の設定変更 (Priority: P1)

ユーザーとして、パラメータファイル（YAML）を編集するだけで、LLM が使用するジャンル定義を変更したい。これにより、コード変更なしで新しいジャンルを追加したり、既存ジャンルの説明を修正できる。

**Why this priority**: ジャンル定義の一元管理が本機能の核心であり、これなしには他の機能が成り立たない。

**Independent Test**: パラメータファイルに新しいジャンルを追加し、パイプライン実行後に LLM がそのジャンルを使用することを確認できる。

**Acceptance Scenarios**:

1. **Given** `genre_vault_mapping` に新しいジャンル「finance」を追加した, **When** organize パイプラインを実行する, **Then** LLM が「finance」をジャンル候補として認識し、適切なコンテンツを「finance」に分類する
2. **Given** 既存ジャンル「ai」の description を変更した, **When** organize パイプラインを実行する, **Then** LLM が変更後の description に基づいて分類を行う

---

### User Story 2 - Vault マッピングとジャンル定義の統合管理 (Priority: P1)

ユーザーとして、ジャンル定義（description）と Vault マッピングを同じ場所で管理したい。これにより、設定の重複を防ぎ、一貫性を保てる。

**Why this priority**: 設定が分散すると整合性の維持が困難になり、運用負荷が増加する。

**Independent Test**: 1つのジャンル設定を変更し、LLM 分類と Vault 出力の両方に反映されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `genre_vault_mapping` でジャンル「tech」を vault「エンジニア」、description「テクノロジー全般」と定義した, **When** organize パイプラインを実行する, **Then** LLM は「tech」を使って分類し、出力は「エンジニア」Vault に配置される
2. **Given** ジャンル「ai」を `genre_vault_mapping` から削除した, **When** organize パイプラインを実行する, **Then** LLM は「ai」を選択肢として提示せず、「other」またはより適切なジャンルに分類する

---

### User Story 3 - other 分類の改善サイクル (Priority: P1)

ユーザーとして、「other」に分類されたコンテンツが5件以上ある場合、新しいジャンル候補の提案を受けたい。これにより、other 率を継続的に減らし、分類精度を向上できる。

**Why this priority**: other 率の低減は分類品質の核心であり、ジャンル定義の動的設定と並ぶ主要機能。

**Independent Test**: other 分類が5件以上ある状態で `make run` を実行し、`genre_suggestions.md` に新ジャンル候補が出力されることを確認できる。

**Acceptance Scenarios**:

1. **Given** other に分類されたコンテンツが5件以上ある, **When** `make run` が完了する, **Then** `data/07_model_output/genre_suggestions.md` に新ジャンル候補（ジャンル名、description、対象コンテンツ例）が出力される
2. **Given** other に分類されたコンテンツが4件以下, **When** `make run` が完了する, **Then** 新ジャンル提案は行われない（ファイル未生成または「提案なし」と記載）
3. **Given** `genre_suggestions.md` に新ジャンル候補がある, **When** ユーザーが `parameters_organize.yml` に手動でジャンルを追加し再実行する, **Then** 次回以降、該当コンテンツは新ジャンルに分類される

---

### User Story 4 - バリデーションとエラーハンドリング (Priority: P2)

ユーザーとして、設定ミスがあった場合に明確なエラーメッセージを受け取りたい。これにより、問題を迅速に特定し修正できる。

**Why this priority**: 設定エラーの早期検出は運用上重要だが、基本機能の後に実装可能。

**Independent Test**: 不正な設定ファイルでパイプラインを実行し、適切なエラーメッセージが表示されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `genre_vault_mapping` のジャンルに description がない, **When** organize パイプラインを実行する, **Then** 警告メッセージが出力され、ジャンル名のみで分類を試みる
2. **Given** `genre_vault_mapping` が空または未定義, **When** organize パイプラインを実行する, **Then** デフォルトのジャンル定義（other のみ）でフォールバックし、警告を出力する

---

### Edge Cases

- ジャンル定義が多すぎる場合（50 以上）→ LLM プロンプトが長くなりすぎないよう、上位 N 件に制限するか警告
- description に特殊文字や改行が含まれる場合 → 適切にエスケープ
- vault 値が空の場合 → エラーとして処理、パイプライン停止
- other が5件以上だが、共通パターンが見つからない場合 → 「パターン不明」として報告、具体的な提案は行わない
- 提案されたジャンルが既存ジャンルと重複する場合 → 既存ジャンルの description 拡張を提案

## Requirements

### Functional Requirements

- **FR-001**: システムは `genre_vault_mapping` からジャンル定義（キー、vault、description）を読み込む
- **FR-002**: システムは読み込んだジャンル定義を元に LLM プロンプトを動的に生成する
- **FR-003**: システムは LLM の出力を `genre_vault_mapping` のキーに対してバリデーションする
- **FR-004**: システムは設定に存在しないジャンルが LLM から返された場合、「other」にフォールバックする
- **FR-005**: システムはジャンル設定の変更時にコード修正を必要としない
- **FR-006**: システムは `make run` 完了時に other 分類が5件以上ある場合、LLM を使って新ジャンル候補を分析・提案する
- **FR-007**: システムは新ジャンル提案を `data/07_model_output/genre_suggestions.md` に出力する
- **FR-008**: 新ジャンル提案には、ジャンル名、description 案、対象コンテンツのタイトル例を含める

### Key Entities

- **GenreDefinition**: ジャンルの定義情報
  - キー（genre 名）: 小文字英字、LLM 出力のバリデーションに使用
  - vault: 出力先 Vault 名
  - description: LLM への分類ヒント（日本語/英語混在可）

- **OrganizeParameters**: organize パイプラインのパラメータ
  - genre_vault_mapping: GenreDefinition のコレクション
  - conflict_handling: 競合処理モード
  - vault_base_path: Vault のベースパス

- **GenreSuggestion**: 新ジャンル提案
  - suggested_genre: 提案されるジャンル名
  - suggested_description: 提案される description
  - sample_titles: 該当コンテンツのタイトル例（最大5件）
  - content_count: 該当コンテンツ数

## Success Criteria

### Measurable Outcomes

- **SC-001**: ユーザーはパラメータファイルの編集のみで新しいジャンルを追加でき、パイプライン再実行で反映される
- **SC-002**: ジャンル分類の精度が維持される（既存テストが継続して PASS）
- **SC-003**: パイプライン実行時間に大きな影響がない（従来比 ±10% 以内）
- **SC-004**: 設定エラー時に明確なエラーメッセージが表示される
- **SC-005**: other が5件以上の場合、新ジャンル提案が `genre_suggestions.md` に出力される
- **SC-006**: 提案に従ってジャンルを追加した場合、other 率が減少する

## 前提条件

- `conf/local/parameters_organize.yml` がユーザー固有の設定ファイルとして存在
- `conf/base/parameters_organize.local.yml.example` がテンプレートとして提供される
- Kedro のパラメータ読み込み機構を使用

## スコープ外

- 既存の `genre_vault_mapping` の構造を完全に破壊する変更（後方互換性を維持）
- GUI ベースの設定編集機能
- 提案の自動適用（ユーザーが手動で YAML 編集）
