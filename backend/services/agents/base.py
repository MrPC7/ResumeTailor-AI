"""Base agent protocol and shared types for the multi-agent workflow."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from services.llm import LLMClient


@runtime_checkable
class Agent(Protocol):
    """Minimal interface that every agent must satisfy."""

    @property
    def name(self) -> str:
        """Human-readable agent identifier."""
        ...

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's task given a shared pipeline context.

        Parameters
        ----------
        context:
            Mutable pipeline state accumulated by previous agents.

        Returns
        -------
        dict with keys/values this agent contributes to the pipeline.
        """
        ...


class BaseAgent:
    """Convenience base class providing common constructor wiring.

    Agents are *not* required to extend this — satisfying the ``Agent``
    protocol is sufficient — but it reduces boilerplate for LLM-backed
    agents that share the standard client + retry pattern.
    """

    def __init__(self, client: LLMClient, max_retries: int = 2) -> None:
        self._client = client
        self._max_retries = max(1, max_retries)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
