import re
pattern1 = re.compile(r"(?im)^\s*co-authored-by:.*\b(claude|anthropic|gpt|chatgpt|openai|copilot|gemini|bard|codex|cursor|aider|devin|windsurf|llama|mistral|grok|qwen|deepseek|kimi|perplexity|codeium|tabnine|sourcegraph|cody|\bai\b|assistant)\b")

cases = [
    "Co-authored-by: Jean-Claude Van Damme <jean.claude@example.com>",
    "Co-authored-by: Gemini Smith <gemini@example.com>",
    "Co-authored-by: Bard Johnson <bard@example.com>",
    "Co-authored-by: Devin Townsend <devin@example.com>",
]

for c in cases:
    print(c, bool(pattern1.search(c)))
