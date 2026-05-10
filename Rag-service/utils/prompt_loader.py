from pathlib import Path


PROMPTS_PATH = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(name: str) -> str:
    prompt_path = PROMPTS_PATH / name
    return prompt_path.read_text(encoding="utf-8")
