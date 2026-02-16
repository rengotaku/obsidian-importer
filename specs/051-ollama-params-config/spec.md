# Feature Specification: Ollama パラメーター関数別設定

**Feature Branch**: `051-ollama-params-config`
**Created**: 2026-02-15
**Status**: Draft
**Input**: specs/050-fix-content-compression/spec-ollama-params.md

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 関数別パラメーター設定 (Priority: P1)

開発者として、LLM呼び出し関数ごとに異なるパラメーター（モデル、タイムアウト、出力トークン数など）を設定したい。これにより、各処理の特性に応じた最適なLLM設定が可能になる。

**Why this priority**: 各関数の出力長が大きく異なるため（知識抽出は数千文字、トピック抽出は1-3単語）、一律設定では出力途切れや無駄なリソース消費が発生する。

**Independent Test**: `parameters.yml` に関数別設定を記述し、パイプライン実行時に各関数が対応するパラメーターを使用することを確認できる。

**Acceptance Scenarios**:

1. **Given** `parameters.yml` に `ollama.extract_knowledge` セクションが設定されている, **When** `extract_knowledge` 関数が実行される, **Then** 該当セクションのパラメーターが使用される
2. **Given** `parameters.yml` に `ollama.translate_summary` セクションが設定されている, **When** `translate_summary` 関数が実行される, **Then** 該当セクションのパラメーターが使用される
3. **Given** `parameters.yml` に `ollama.extract_topic` セクションが設定されている, **When** `extract_topic` 関数が実行される, **Then** 該当セクションのパラメーターが使用される

---

### User Story 2 - デフォルト値の適用 (Priority: P2)

開発者として、一部のパラメーターのみを設定し、未指定のパラメーターにはデフォルト値が適用されるようにしたい。これにより、必要最小限の設定で運用できる。

**Why this priority**: 全パラメーターを毎回指定するのは煩雑。デフォルト値があれば設定の手間が減る。

**Independent Test**: `parameters.yml` で一部パラメーターのみ設定し、未指定項目にデフォルト値が適用されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `ollama.extract_topic` に `model` のみ設定されている, **When** `extract_topic` 関数が実行される, **Then** `timeout`, `temperature`, `num_predict` にはデフォルト値が適用される
2. **Given** `ollama` セクションが空である, **When** いずれかの関数が実行される, **Then** 全パラメーターにデフォルト値が適用される

---

### User Story 3 - extract_topic の統一実装 (Priority: P3)

開発者として、`extract_topic` 関数も他の関数と同様に `call_ollama` を使用するようにしたい。これにより、実装が統一され、パラメーター管理が一元化される。

**Why this priority**: 現在 `extract_topic` は `requests.post` で直接APIを呼び出しており、他の関数と実装が異なる。統一することで保守性が向上する。

**Independent Test**: `extract_topic` 関数が `call_ollama` を使用し、`parameters.yml` のパラメーターが適用されることを確認できる。

**Acceptance Scenarios**:

1. **Given** `extract_topic` 関数が実行される, **When** LLM呼び出しが行われる, **Then** `call_ollama` 関数経由でAPIが呼び出される
2. **Given** `ollama.extract_topic.num_predict` が `64` に設定されている, **When** `extract_topic` 関数が実行される, **Then** 出力トークン数が64に制限される

---

### Edge Cases

- **関数名の誤記**: `parameters.yml` に存在しない関数名（例: `ollama.extract_knowledgee`）が設定された場合、無視してデフォルト値を使用する
- **無効なパラメーター値**: `timeout` に負の値や `temperature` に範囲外の値が設定された場合、デフォルト値にフォールバックする
- **Ollama接続エラー**: 指定された `base_url` に接続できない場合、適切なエラーメッセージを返す

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `parameters.yml` の `ollama.{関数名}` セクションから関数別パラメーターを読み込めなければならない
- **FR-002**: システムは各関数で以下のパラメーターを設定可能にしなければならない: `model`, `base_url`, `timeout`, `temperature`, `num_predict`
- **FR-003**: システムは未指定パラメーターに対してデフォルト値を適用しなければならない
- **FR-004**: `extract_topic` 関数は `call_ollama` を使用してLLM呼び出しを行わなければならない
- **FR-005**: システムはパラメーター取得用のヘルパー関数を提供しなければならない

### デフォルト値

| パラメーター | デフォルト値 |
|------------|-------------|
| `model` | `gemma3:12b` |
| `base_url` | `http://localhost:11434` |
| `timeout` | `120` |
| `temperature` | `0.2` |
| `num_predict` | `-1` |

### Key Entities

- **OllamaConfig**: 関数別のOllamaパラメーター設定を表す。関数名をキーとして、各パラメーター（model, base_url, timeout, temperature, num_predict）を持つ。
- **関数名**: `extract_knowledge`, `translate_summary`, `extract_topic` の3つの識別子

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 3つの関数（`extract_knowledge`, `translate_summary`, `extract_topic`）すべてで関数別パラメーターが適用される
- **SC-002**: `extract_knowledge` で長文出力（1000文字以上）が途切れずに生成される
- **SC-003**: `extract_topic` で `call_ollama` を使用した実装に統一される
- **SC-004**: 既存のパイプラインが設定変更なしで動作する（デフォルト値による後方互換性）

## Assumptions

- Ollama サーバーは `http://localhost:11434` でローカル稼働している
- 使用モデル（`gemma3:12b`, `oss-gpt:20b`）は事前にOllamaにインストール済み
- `parameters.yml` の構文は Kedro 標準に準拠する
