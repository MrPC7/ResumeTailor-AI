# Prompts have been centralised to services/prompt_builder.
# This shim is kept for import compatibility only.
from services.prompt_builder import PromptType, prompt_builder


def build_jd_analysis_prompt(job_description: str) -> str:
    return prompt_builder.build(PromptType.JD_ANALYSIS, job_description=job_description).to_single_prompt()

