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
| 1 | (TBD) | Technical | Small | organized | |
| 2 | (TBD) | Technical | Medium | organized | |
| 3 | (TBD) | Technical | Large | review | |
| 4 | (TBD) | Business | Small | organized | |
| 5 | (TBD) | Business | Medium | organized | |
| 6 | (TBD) | Daily | Small | organized | |
| 7 | (TBD) | Table | Medium | review | |
| 8 | (TBD) | Table | Large | review | |
| 9 | (TBD) | Code | Small | organized | |
| 10 | (TBD) | Code | Medium | review | |

**Total**: 10 files required (currently 3)

## Validation Requirements

1. **Compression Threshold**: All files must meet compression ratio threshold (no `review_reason` field)
2. **Table Preservation**: Files containing tables must have valid Markdown table syntax
3. **Frontmatter**: All files must have valid YAML frontmatter with required fields

## Related Tests

- `tests/test_e2e_golden.py`: E2E validation tests using these golden files
