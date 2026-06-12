# Prompts have been centralised to services/prompt_builder.
# This shim is kept for import compatibility only.
from services.prompt_builder import PromptType, prompt_builder


def build_extraction_prompt(raw_text: str) -> str:
    return prompt_builder.build(PromptType.RESUME_EXTRACTION, raw_text=raw_text).to_single_prompt()

