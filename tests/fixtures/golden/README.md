# Golden Files

This directory contains golden files for E2E quality testing of the knowledge extraction pipeline.

## Selection Criteria

Golden files are selected based on:
- **Conversation Type**: Technical, Business, Daily, Table data, Code content
- **File Size**: Small (<2KB), Medium (2-5KB), Large (>5KB)
- **Source**: organized/ (success) and review/ (needs improvement)

## File List

| No | File | Type | Size | Source | Notes |
|----|------|------|------|--------|-------|
| 1 | Automatic1111 positive prompt 設定.md | Technical | Small (2.4KB) | organized | Stable Diffusion settings |
| 2 | API GatewayとLoad Balancerの違い.md | Technical | Medium (3.9KB) | organized | AWS architecture, has tables |
| 3 | Claude CLI 設定確認問題.md | Technical | Large (14.7KB) | review | CLI troubleshooting, code blocks |
| 4 | 8ヶ月の赤ちゃん飛行機搭乗時の睡眠対策.md | Business | Small (1.8KB) | organized | Baby travel tips |
| 5 | 9ヶ月の赤ちゃんとの飛行機搭乗のコツ.md | Business | Medium (3.5KB) | organized | Parenting advice |
| 6 | 3Dプリンターでオリジナルグッズを作る.md | Daily | Small (1.9KB) | organized | 3D printing hobby |
| 7 | 9ヶ月赤ちゃんのおやつとバナナプリン.md | Table | Medium (3.1KB) | organized | Baby food recipes, has tables |
| 8 | 千葉のSwitch2販売実績.md | Table | Large (12.4KB) | review | Sales data analysis, has tables |
| 9 | Bash Alias 設定トラブルシューティング.md | Code | Small (2.4KB) | organized | Shell scripting, code blocks |
| 10 | 0b75ea4aa423.md | Code | Medium (5.6KB) | review | NISA investment guide, code examples |

**Total**: 10 files (meeting requirements)

## Validation Requirements

1. **Compression Threshold**: All files must meet compression ratio threshold (no `review_reason` field)
2. **Table Preservation**: Files containing tables must have valid Markdown table syntax
3. **Frontmatter**: All files must have valid YAML frontmatter with required fields

## Related Tests

- `tests/test_e2e_golden.py`: E2E validation tests using these golden files
