from __future__ import annotations

from dataclasses import dataclass

from services.prompt_builder.templates import PROMPT_REGISTRY
from services.prompt_builder.types import PromptType


@dataclass(frozen=True)
class BuiltPrompt:
    system: str
    user: str

    def to_single_prompt(self) -> str:
        """Combine system and user into one string for single-prompt LLM clients."""
        return f"{self.system}\n\n{self.user}"


class PromptBuilder:
    def build(self, prompt_type: PromptType, **kwargs: str) -> BuiltPrompt:
        template = PROMPT_REGISTRY.get(prompt_type)
        if template is None:
            raise ValueError(f"No prompt template registered for type: {prompt_type!r}")

        try:
            user = template.user_template.format(**kwargs)
        except KeyError as exc:
            raise ValueError(
                f"Missing required variable {exc} for prompt type {prompt_type!r}."
            ) from exc

        return BuiltPrompt(system=template.system, user=user)
