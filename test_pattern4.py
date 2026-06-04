import re
pattern4 = re.compile(r"(?im)\bgenerated\s+with\b.{0,40}\b(claude|anthropic|gpt|chatgpt|openai|copilot|gemini|bard|codex|cursor|aider|devin|windsurf|llama|mistral|grok|qwen|deepseek|kimi|perplexity|codeium|tabnine|sourcegraph|cody|\bai\b)\b")
print(bool(pattern4.search("This bug was generated with a script written by Devin.")))
print(bool(pattern4.search("The data was generated with help from Claude.")))
