from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
CODEGEN_ROUTING_SYSTEM_PROMPT = "codegen-routing-system-prompt.txt"


@lru_cache
def load_prompt(prompt_name: str) -> str:
    # Prompt 统一从文件读取，方便后续直接替换为原 Java 项目的原始文案。
    prompt_path = PROMPT_DIR / prompt_name
    return prompt_path.read_text(encoding="utf-8").strip()
