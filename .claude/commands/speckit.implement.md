---
description: Execute the implementation plan by delegating phases to subagents for processing tasks defined in tasks.md
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - Create/verify ignore files based on actual project setup (.gitignore, .dockerignore, etc.)
   - Check technology from plan.md and apply appropriate patterns

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

6. **Execute implementation phases**:

   ### 6.1 Phase Type Detection

   | Phase Type | 実行者 | 理由 |
   |------------|--------|------|
   | **Setup** (Phase 1) | メインエージェント | コンテキスト保持が必要 |
   | **TDD Phase** (テスト設計セクションあり) | tdd-generator → phase-executor | TDD フロー |
   | **通常 Phase** (Polish/Documentation等) | phase-executor のみ | 統合テスト・検証のみ |

   判定: Phase 名に "setup" → main, "### テスト設計" or "### テスト実装" あり → TDD, それ以外 → 通常

   ### 6.2 Phase 1 (Setup) - メインエージェント直接実行

   Phase 1 が Setup の場合、サブエージェントに委譲せずメインが直接実行:
   1. tasks.md から Phase 1 タスク抽出
   2. 各タスクを順次実行
   3. tasks.md 更新（`- [ ]` → `- [X]`）
   4. `{FEATURE_DIR}/tasks/ph1-output.md` 生成

   ### 6.3 TDD フロー（User Story / Foundational Phase）

   **Step 1: テスト実装 (RED)**
   - Task tool で `tdd-generator` を呼び出す（`model: opus`）
   - 入力/出力形式は `.claude/agents/tdd-generator.md` を参照
   - 完了後、テストが FAIL 状態であることを確認

   **Step 2: 実装 (GREEN) + 検証**
   - Task tool で `phase-executor` を呼び出す（`model: sonnet`）
   - 入力/出力形式は `.claude/agents/phase-executor.md` を参照
   - 完了後、全テストが PASS であることを確認

   **Step 3: カバレッジ検証**
   - `make coverage` で ≥80% を確認
   - 不足時は tdd-generator に追加テスト依頼

   ### 6.4 通常フロー（Polish/Documentation Phase）

   - Task tool で `phase-executor` を呼び出す（`model: sonnet`）
   - 入力/出力形式は `.claude/agents/phase-executor.md` を参照

   ### 6.5 Phase Transition

   Phase 完了後:
   1. Phase 完了サマリー表示
   2. 成果物リスト表示
   3. **Commit phase changes**:
      ```bash
      git add -A && git commit -m "feat(phase-{N}): {brief description}"
      ```
   4. `{FEATURE_DIR}/tasks/ph{N}-output.md` 生成
   5. **全タスク完了** → 次 Phase へ自動進行
   6. **一部失敗/エラー** → ユーザーに確認

7. **Progress tracking and error handling**:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT**: For completed tasks, make sure to mark the task off as [X] in the tasks file.

8. **Completion validation**:
   - Verify all phases completed
   - Run final validation: `grep -c "\- \[ \]" tasks.md` (Should be 0)
   - Check that implemented features match the original specification
   - Validate that tests pass
   - Generate completion report

## Notes

- This command requires `@phase-executor` and `@tdd-generator` subagents in `.claude/agents/`
- If tasks.md is incomplete, run `/speckit.tasks` first
- **Task tool model parameter**: tdd-generator → `opus`, phase-executor → `sonnet`
- For completed tasks, mark as `[X]` in tasks.md
