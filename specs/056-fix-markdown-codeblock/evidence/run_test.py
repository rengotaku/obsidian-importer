# \!/usr/bin/env python3
"""Test LLM response."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "src")

from obsidian_etl.utils.knowledge_extractor import KNOWLEDGE_PROMPT_PATH, load_prompt
from obsidian_etl.utils.ollama import call_ollama

EVIDENCE_DIR = Path("specs/056-fix-markdown-codeblock/evidence")


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    system_prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)

    # Test user message
    test_user_message = (
        "ファイル名: Pythonファイル操作\n"
        "プロバイダー: claude\n"
        "会話サマリー: なし\n"
        "会話作成日: 2024-01-01\n"
        "\n"
        "--- 会話内容 ---\n"
        "\n"
        "Human: Pythonでファイルを読み込んで内容を表示するコードを教えて\n"
        "\n"
        "Assistant: Pythonでファイルを読み込む方法を説明します。\n"
        "\n"
        "```python\n"
        "with open('example.txt', 'r', encoding='utf-8') as f:\n"
        "    content = f.read()\n"
        "    print(content)\n"
        "```\n"
        "\n"
        "このコードはUTF-8エンコーディングでファイルを開きます。\n"
    )

    # Save request
    request_data = {
        "system_prompt": system_prompt,
        "user_message": test_user_message,
        "timestamp": timestamp,
    }
    request_file = EVIDENCE_DIR / f"request_{timestamp}.json"
    request_file.write_text(json.dumps(request_data, ensure_ascii=False, indent=2))
    print(f"Request saved: {request_file}")

    # Call LLM
    print("Calling LLM...")
    response, error = call_ollama(
        system_prompt=system_prompt,
        user_message=test_user_message,
        model="gpt-oss:20b",
        num_predict=16384,
        timeout=300,
    )

    # Save response
    response_data = {
        "response": response,
        "error": error,
        "timestamp": timestamp,
    }
    response_file = EVIDENCE_DIR / f"response_{timestamp}.json"
    response_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2))
    print(f"Response saved: {response_file}")

    # Also save raw response as text for easy viewing
    raw_file = EVIDENCE_DIR / f"response_{timestamp}_raw.txt"
    raw_file.write_text(response if response else f"ERROR: {error}")
    print(f"Raw response saved: {raw_file}")

    # Analyze response
    print("\n=== Response Analysis ===")
    print(f"Length: {len(response)} chars")

    # Count code blocks
    lines = response.split("\n") if response else []
    opens = sum(1 for l in lines if l.strip().startswith("```") and l.strip() != "```")
    closes = sum(1 for l in lines if l.strip() == "```")
    print(f"Code block opens: {opens}, closes: {closes}")

    if response:
        print("\n=== Last 10 lines ===")
        for i, line in enumerate(lines[-10:], max(1, len(lines) - 9)):
            print(f"{i:4d}: {line[:80]}")


if __name__ == "__main__":
    main()


def test_with_long_content():
    """Test with longer content that might hit token limits."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    system_prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)
    
    # Longer test content (simulating a real conversation)
    test_user_message = (
        "ファイル名: キャラクターポーズ追加と修正\n"
        "プロバイダー: claude\n"
        "会話サマリー: なし\n"
        "会話作成日: 2024-01-01\n"
        "\n"
        "--- 会話内容 ---\n"
        "\n"
        "Human: 各キャラクターにポーズを追加してください。\n"
        "\n"
        "Assistant: 了解しました。各キャラクターに合ったポーズを追加します。\n"
        "\n"
        "```python\n"
        "characters = [\n"
    )
    
    # Add many character definitions to make it long
    for i in range(50):
        test_user_message += f'''  {{
    "age": "<lora:age_slider_v4:4>",
    "hair_style": "blonde hair,shaggy hair,long hair",
    "body_shape": "huge breasts",
    "tag": "character_{i}",
    "fashion": "black suit",
    "face": "gloss lipstick",
    "pose": "standing,arms crossed",
    "expression": "serious",
    "negative_prompt": base_negative_prompt,
  }},
'''
    
    test_user_message += (
        "]\n"
        "```\n"
        "\n"
        "追加したポーズ：\n"
        "- standing系: arms crossed, hand on hip, casual pose\n"
        "- sitting系: crossed legs, relaxed pose\n"
        "\n"
        "Human: ありがとうございます。\n"
    )
    
    print(f"Test content length: {len(test_user_message)} chars")
    
    # Save request
    request_data = {
        "system_prompt": system_prompt,
        "user_message": test_user_message,
        "timestamp": timestamp,
        "test_type": "long_content",
    }
    request_file = EVIDENCE_DIR / f"request_long_{timestamp}.json"
    request_file.write_text(json.dumps(request_data, ensure_ascii=False, indent=2))
    print(f"Request saved: {request_file}")
    
    # Call LLM
    print("Calling LLM with long content...")
    response, error = call_ollama(
        system_prompt=system_prompt,
        user_message=test_user_message,
        model="gpt-oss:20b",
        num_predict=16384,
        timeout=300,
    )
    
    # Save response
    response_data = {
        "response": response,
        "error": error,
        "timestamp": timestamp,
    }
    response_file = EVIDENCE_DIR / f"response_long_{timestamp}.json"
    response_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2))
    print(f"Response saved: {response_file}")
    
    # Save raw response
    raw_file = EVIDENCE_DIR / f"response_long_{timestamp}_raw.txt"
    raw_file.write_text(response if response else f"ERROR: {error}")
    print(f"Raw response saved: {raw_file}")
    
    # Analyze
    print("\n=== Response Analysis ===")
    print(f"Length: {len(response)} chars")
    
    lines = response.split('\n') if response else []
    opens = sum(1 for l in lines if l.strip().startswith('```') and l.strip() != '```')
    closes = sum(1 for l in lines if l.strip() == '```')
    print(f"Code block opens: {opens}, closes: {closes}")
    print(f"Difference: {opens - closes}")
    
    # Check if ends with unclosed code block
    if response:
        last_lines = lines[-5:]
        print("\n=== Last 5 lines ===")
        for i, line in enumerate(last_lines, len(lines) - 4):
            print(f"{i:4d}: {line[:80]}")
        
        # Check for truncation signs
        last_line = lines[-1] if lines else ""
        if last_line.strip().startswith('```') and last_line.strip() != '```':
            print("\n!!! WARNING: Response ends with opening code block (likely truncated) !!!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "long":
        test_with_long_content()
    else:
        main()


def test_unlimited_tokens():
    """Test with unlimited tokens (num_predict=-1)."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    system_prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)
    
    # Same long content as before
    test_user_message = (
        "ファイル名: キャラクターポーズ追加と修正\n"
        "プロバイダー: claude\n"
        "会話サマリー: なし\n"
        "会話作成日: 2024-01-01\n"
        "\n"
        "--- 会話内容 ---\n"
        "\n"
        "Human: 各キャラクターにポーズを追加してください。\n"
        "\n"
        "Assistant: 了解しました。各キャラクターに合ったポーズを追加します。\n"
        "\n"
        "```python\n"
        "characters = [\n"
    )
    
    for i in range(50):
        test_user_message += f'''  {{
    "age": "<lora:age_slider_v4:4>",
    "hair_style": "blonde hair,shaggy hair,long hair",
    "body_shape": "huge breasts",
    "tag": "character_{i}",
    "fashion": "black suit",
    "face": "gloss lipstick",
    "pose": "standing,arms crossed",
    "expression": "serious",
    "negative_prompt": base_negative_prompt,
  }},
'''
    
    test_user_message += (
        "]\n"
        "```\n"
        "\n"
        "追加したポーズ：\n"
        "- standing系: arms crossed, hand on hip, casual pose\n"
        "- sitting系: crossed legs, relaxed pose\n"
        "\n"
        "Human: ありがとうございます。\n"
    )
    
    print(f"Test content length: {len(test_user_message)} chars")
    print("Using num_predict=-1 (UNLIMITED)")
    
    # Save request
    request_data = {
        "system_prompt": system_prompt,
        "user_message": test_user_message,
        "timestamp": timestamp,
        "test_type": "unlimited_tokens",
        "num_predict": -1,
    }
    request_file = EVIDENCE_DIR / f"request_unlimited_{timestamp}.json"
    request_file.write_text(json.dumps(request_data, ensure_ascii=False, indent=2))
    print(f"Request saved: {request_file}")
    
    # Call LLM with UNLIMITED tokens
    print("Calling LLM with unlimited tokens...")
    response, error = call_ollama(
        system_prompt=system_prompt,
        user_message=test_user_message,
        model="gpt-oss:20b",
        num_predict=-1,  # UNLIMITED
        timeout=600,     # Longer timeout for unlimited output
    )
    
    # Save response
    response_data = {
        "response": response,
        "error": error,
        "timestamp": timestamp,
        "num_predict": -1,
    }
    response_file = EVIDENCE_DIR / f"response_unlimited_{timestamp}.json"
    response_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2))
    print(f"Response saved: {response_file}")
    
    # Save raw response
    raw_file = EVIDENCE_DIR / f"response_unlimited_{timestamp}_raw.txt"
    raw_file.write_text(response if response else f"ERROR: {error}")
    print(f"Raw response saved: {raw_file}")
    
    # Analyze
    print("\n=== Response Analysis ===")
    print(f"Length: {len(response)} chars")
    
    lines = response.split('\n') if response else []
    opens = sum(1 for l in lines if l.strip().startswith('```') and l.strip() != '```')
    closes = sum(1 for l in lines if l.strip() == '```')
    print(f"Code block opens: {opens}, closes: {closes}")
    print(f"Difference: {opens - closes}")
    
    # Check first and last lines
    if response:
        print(f"\nFirst line: {lines[0][:50]}")
        print(f"Last line: {lines[-1][:50]}")
        
        # Check for proper markdown fence
        starts_with_fence = response.strip().startswith('```markdown')
        ends_with_fence = response.strip().endswith('```')
        print(f"\nStarts with ```markdown: {starts_with_fence}")
        print(f"Ends with ```: {ends_with_fence}")
        
        if starts_with_fence and ends_with_fence:
            print("\n*** OUTER FENCE IS PROPERLY CLOSED ***")
        else:
            print("\n!!! WARNING: OUTER FENCE NOT PROPERLY CLOSED !!!")
        
        print("\n=== Last 10 lines ===")
        for i, line in enumerate(lines[-10:], max(1, len(lines) - 9)):
            print(f"{i:4d}: {line[:80]}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "long":
            test_with_long_content()
        elif sys.argv[1] == "unlimited":
            test_unlimited_tokens()
    else:
        main()


def test_gemma_model():
    """Test with gemma3:12b model."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    system_prompt = load_prompt(KNOWLEDGE_PROMPT_PATH)
    
    # Same long content
    test_user_message = (
        "ファイル名: キャラクターポーズ追加と修正\n"
        "プロバイダー: claude\n"
        "会話サマリー: なし\n"
        "会話作成日: 2024-01-01\n"
        "\n"
        "--- 会話内容 ---\n"
        "\n"
        "Human: 各キャラクターにポーズを追加してください。\n"
        "\n"
        "Assistant: 了解しました。各キャラクターに合ったポーズを追加します。\n"
        "\n"
        "```python\n"
        "characters = [\n"
    )
    
    for i in range(50):
        test_user_message += f'''  {{
    "age": "<lora:age_slider_v4:4>",
    "hair_style": "blonde hair,shaggy hair,long hair",
    "body_shape": "huge breasts",
    "tag": "character_{i}",
    "fashion": "black suit",
    "face": "gloss lipstick",
    "pose": "standing,arms crossed",
    "expression": "serious",
    "negative_prompt": base_negative_prompt,
  }},
'''
    
    test_user_message += (
        "]\n"
        "```\n"
        "\n"
        "追加したポーズ：\n"
        "- standing系: arms crossed, hand on hip, casual pose\n"
        "- sitting系: crossed legs, relaxed pose\n"
        "\n"
        "Human: ありがとうございます。\n"
    )
    
    print(f"Test content length: {len(test_user_message)} chars")
    print("Using model: gemma3:12b with num_predict=-1")
    
    request_data = {
        "system_prompt": system_prompt,
        "user_message": test_user_message,
        "timestamp": timestamp,
        "test_type": "gemma_model",
        "model": "gemma3:12b",
        "num_predict": -1,
    }
    request_file = EVIDENCE_DIR / f"request_gemma_{timestamp}.json"
    request_file.write_text(json.dumps(request_data, ensure_ascii=False, indent=2))
    print(f"Request saved: {request_file}")
    
    print("Calling LLM (gemma3:12b)...")
    response, error = call_ollama(
        system_prompt=system_prompt,
        user_message=test_user_message,
        model="gemma3:12b",
        num_predict=-1,
        timeout=600,
    )
    
    response_data = {
        "response": response,
        "error": error,
        "timestamp": timestamp,
    }
    response_file = EVIDENCE_DIR / f"response_gemma_{timestamp}.json"
    response_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2))
    print(f"Response saved: {response_file}")
    
    raw_file = EVIDENCE_DIR / f"response_gemma_{timestamp}_raw.txt"
    raw_file.write_text(response if response else f"ERROR: {error}")
    print(f"Raw response saved: {raw_file}")
    
    print("\n=== Response Analysis ===")
    print(f"Length: {len(response)} chars")
    
    lines = response.split('\n') if response else []
    opens = sum(1 for l in lines if l.strip().startswith('```') and l.strip() != '```')
    closes = sum(1 for l in lines if l.strip() == '```')
    print(f"Code block opens: {opens}, closes: {closes}")
    print(f"Difference: {opens - closes}")
    
    if response:
        starts_with_fence = response.strip().startswith('```markdown')
        ends_with_fence = response.strip().endswith('```')
        print(f"\nStarts with ```markdown: {starts_with_fence}")
        print(f"Ends with ```: {ends_with_fence}")
        
        if starts_with_fence and ends_with_fence:
            print("\n*** OUTER FENCE IS PROPERLY CLOSED ***")
        else:
            print("\n!!! WARNING: OUTER FENCE NOT PROPERLY CLOSED !!!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "long":
            test_with_long_content()
        elif sys.argv[1] == "unlimited":
            test_unlimited_tokens()
        elif sys.argv[1] == "gemma":
            test_gemma_model()
    else:
        main()


def test_no_fence_prompt():
    """Test with modified prompt that doesn't require ```markdown wrapper."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Modified prompt WITHOUT the ```markdown wrapper requirement
    modified_prompt = """あなたは会話ログから知識を抽出するAIアシスタントです。

## タスク

与えられた会話ログを分析し、以下の情報を抽出してマークダウン形式で出力してください。

## 出力形式

必ず以下のマークダウン形式のみで回答してください。説明文は不要です。
コードブロックで囲まずに、直接マークダウンを出力してください。

# タイトル（40文字以内）

## 要約
会話の要点を1-2文で説明（200文字以内）

## タグ
関連タグ（カンマ区切り、3-5個）

## 内容
構造化されたまとめ（Markdown形式、コード含む）

## 抽出ルール

### タイトル（# 見出し）
- 会話の内容を端的に表すタイトル
- 40文字以内

### 要約（## 要約）
- 会話の要点を1-2文で簡潔に説明
- 200文字以内

### タグ（## タグ）
- 会話の内容を表すタグを3-5個
- カンマ区切りで1行で記述

### 内容（## 内容）
- 会話内容に適した構造でまとめを作成
- コードブロックは言語指定を含める（例: ```python）
- 壁のテキスト禁止、構造化必須
"""
    
    test_user_message = (
        "ファイル名: キャラクターポーズ追加と修正\n"
        "プロバイダー: claude\n"
        "会話サマリー: なし\n"
        "会話作成日: 2024-01-01\n"
        "\n"
        "--- 会話内容 ---\n"
        "\n"
        "Human: 各キャラクターにポーズを追加してください。\n"
        "\n"
        "Assistant: 了解しました。各キャラクターに合ったポーズを追加します。\n"
        "\n"
        "```python\n"
        "characters = [\n"
    )
    
    for i in range(50):
        test_user_message += f'''  {{
    "age": "<lora:age_slider_v4:4>",
    "hair_style": "blonde hair,shaggy hair,long hair",
    "body_shape": "huge breasts",
    "tag": "character_{i}",
    "fashion": "black suit",
    "face": "gloss lipstick",
    "pose": "standing,arms crossed",
    "expression": "serious",
    "negative_prompt": base_negative_prompt,
  }},
'''
    
    test_user_message += (
        "]\n"
        "```\n"
        "\n"
        "追加したポーズ：\n"
        "- standing系: arms crossed, hand on hip, casual pose\n"
        "- sitting系: crossed legs, relaxed pose\n"
        "\n"
        "Human: ありがとうございます。\n"
    )
    
    print(f"Test content length: {len(test_user_message)} chars")
    print("Using MODIFIED PROMPT without ```markdown wrapper")
    print("Model: gpt-oss:20b, num_predict=-1")
    
    request_data = {
        "system_prompt": modified_prompt,
        "user_message": test_user_message,
        "timestamp": timestamp,
        "test_type": "no_fence_prompt",
    }
    request_file = EVIDENCE_DIR / f"request_nofence_{timestamp}.json"
    request_file.write_text(json.dumps(request_data, ensure_ascii=False, indent=2))
    print(f"Request saved: {request_file}")
    
    print("Calling LLM...")
    response, error = call_ollama(
        system_prompt=modified_prompt,
        user_message=test_user_message,
        model="gpt-oss:20b",
        num_predict=-1,
        timeout=600,
    )
    
    response_data = {
        "response": response,
        "error": error,
        "timestamp": timestamp,
    }
    response_file = EVIDENCE_DIR / f"response_nofence_{timestamp}.json"
    response_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2))
    print(f"Response saved: {response_file}")
    
    raw_file = EVIDENCE_DIR / f"response_nofence_{timestamp}_raw.txt"
    raw_file.write_text(response if response else f"ERROR: {error}")
    print(f"Raw response saved: {raw_file}")
    
    print("\n=== Response Analysis ===")
    print(f"Length: {len(response)} chars")
    
    lines = response.split('\n') if response else []
    opens = sum(1 for l in lines if l.strip().startswith('```') and l.strip() != '```')
    closes = sum(1 for l in lines if l.strip() == '```')
    print(f"Code block opens: {opens}, closes: {closes}")
    print(f"Difference: {opens - closes}")
    
    if response:
        # Check if response starts with markdown fence (it shouldn't now)
        starts_with_fence = response.strip().startswith('```')
        print(f"\nStarts with ```: {starts_with_fence}")
        
        if starts_with_fence:
            print("!!! Model still wrapped output in code fence despite instruction !!!")
        else:
            print("*** Model output raw markdown as instructed ***")
        
        # Check for proper section headers
        has_title = '# ' in response
        has_summary = '## 要約' in response
        has_tags = '## タグ' in response
        has_content = '## 内容' in response
        print(f"\nHas # title: {has_title}")
        print(f"Has ## 要約: {has_summary}")
        print(f"Has ## タグ: {has_tags}")
        print(f"Has ## 内容: {has_content}")
        
        print("\n=== First 15 lines ===")
        for i, line in enumerate(lines[:15], 1):
            print(f"{i:4d}: {line[:80]}")
        
        print("\n=== Last 10 lines ===")
        for i, line in enumerate(lines[-10:], max(1, len(lines) - 9)):
            print(f"{i:4d}: {line[:80]}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "long":
            test_with_long_content()
        elif sys.argv[1] == "unlimited":
            test_unlimited_tokens()
        elif sys.argv[1] == "gemma":
            test_gemma_model()
        elif sys.argv[1] == "nofence":
            test_no_fence_prompt()
    else:
        main()


def test_plain_fence_prompt():
    """Test with prompt using plain ``` instead of ```markdown."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Modified prompt with plain ``` wrapper (no markdown language)
    modified_prompt = """あなたは会話ログから知識を抽出するAIアシスタントです。

## タスク

与えられた会話ログを分析し、以下の情報を抽出してマークダウン形式で出力してください。

## 出力形式

必ず以下の形式で回答してください。説明文は不要です。
出力は必ず ``` で開始し、``` で終了してください。

```
# タイトル（40文字以内）

## 要約
会話の要点を1-2文で説明（200文字以内）

## タグ
関連タグ（カンマ区切り、3-5個）

## 内容
構造化されたまとめ（Markdown形式、コード含む）
```

## 注意
- 出力の最初と最後は必ず ``` で囲んでください
- コードブロック内のコードには言語指定を含めてください（例: ```python）
"""
    
    test_user_message = (
        "ファイル名: キャラクターポーズ追加と修正\n"
        "プロバイダー: claude\n"
        "会話サマリー: なし\n"
        "会話作成日: 2024-01-01\n"
        "\n"
        "--- 会話内容 ---\n"
        "\n"
        "Human: 各キャラクターにポーズを追加してください。\n"
        "\n"
        "Assistant: 了解しました。各キャラクターに合ったポーズを追加します。\n"
        "\n"
        "```python\n"
        "characters = [\n"
    )
    
    for i in range(50):
        test_user_message += f'''  {{
    "tag": "character_{i}",
    "pose": "standing,arms crossed",
  }},
'''
    
    test_user_message += (
        "]\n"
        "```\n"
        "\n"
        "追加したポーズ：\n"
        "- standing系: arms crossed, hand on hip\n"
        "\n"
        "Human: ありがとうございます。\n"
    )
    
    print(f"Test content length: {len(test_user_message)} chars")
    print("Using prompt with PLAIN ``` wrapper (no markdown language)")
    
    request_data = {
        "system_prompt": modified_prompt,
        "user_message": test_user_message,
        "timestamp": timestamp,
        "test_type": "plain_fence",
    }
    request_file = EVIDENCE_DIR / f"request_plainfence_{timestamp}.json"
    request_file.write_text(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    print("Calling LLM...")
    response, error = call_ollama(
        system_prompt=modified_prompt,
        user_message=test_user_message,
        model="gpt-oss:20b",
        num_predict=-1,
        timeout=600,
    )
    
    raw_file = EVIDENCE_DIR / f"response_plainfence_{timestamp}_raw.txt"
    raw_file.write_text(response if response else f"ERROR: {error}")
    print(f"Raw response saved: {raw_file}")
    
    print("\n=== Response Analysis ===")
    print(f"Length: {len(response)} chars")
    
    lines = response.split('\n') if response else []
    opens = sum(1 for l in lines if l.strip().startswith('```') and l.strip() != '```')
    closes = sum(1 for l in lines if l.strip() == '```')
    print(f"Code block opens (with lang): {opens}")
    print(f"Code block closes (plain ```): {closes}")
    
    if response:
        first_line = lines[0].strip() if lines else ""
        last_line = lines[-1].strip() if lines else ""
        
        print(f"\nFirst line: '{first_line}'")
        print(f"Last line: '{last_line}'")
        
        starts_correctly = first_line == '```'
        ends_correctly = last_line == '```'
        
        print(f"\nStarts with plain ```: {starts_correctly}")
        print(f"Ends with plain ```: {ends_correctly}")
        
        if starts_correctly and ends_correctly:
            print("\n*** OUTER FENCE IS PROPERLY CLOSED ***")
        else:
            print("\n!!! WARNING: OUTER FENCE NOT PROPERLY CLOSED !!!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "long":
            test_with_long_content()
        elif arg == "unlimited":
            test_unlimited_tokens()
        elif arg == "gemma":
            test_gemma_model()
        elif arg == "nofence":
            test_no_fence_prompt()
        elif arg == "plainfence":
            test_plain_fence_prompt()
    else:
        main()
