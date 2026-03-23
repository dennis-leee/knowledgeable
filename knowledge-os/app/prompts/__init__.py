"""Prompts package."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load prompt template from file."""
    prompt_file = PROMPTS_DIR / f"{name}.txt"
    if prompt_file.exists():
        return prompt_file.read_text()
    return ""


__all__ = ["load_prompt", "PROMPTS_DIR"]
