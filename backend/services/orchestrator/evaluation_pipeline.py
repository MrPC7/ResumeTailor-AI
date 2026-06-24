"""Pipeline orchestrator — coordinates multi-agent evaluation workflow."""
from __future__ import annotations

import logging
from typing import Any

from services.agents.base import Agent

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when the evaluation pipeline fails."""


class EvaluationPipeline:
    """Runs a sequence of agents, threading a shared context through each.

    The pipeline is intentionally simple: agents execute in declared order
    and each receives the accumulated context from all previous agents.
    """

    def __init__(self, agents: list[Agent]) -> None:
        if not agents:
            raise ValueError("Pipeline requires at least one agent.")
        self._agents = list(agents)

    async def run(self, initial_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute all agents sequentially, merging results into context.

        Parameters
        ----------
        initial_context:
            Seed data for the first agent (e.g. parsed resume, raw JD text).

        Returns
        -------
        Final accumulated context after all agents have run.
        """
        context: dict[str, Any] = dict(initial_context or {})

        for agent in self._agents:
            logger.info("Pipeline: running agent '%s'", agent.name)
            try:
                result = await agent.run(context)
                context.update(result)
            except Exception as exc:
                raise PipelineError(
                    f"Agent '{agent.name}' failed: {exc}"
                ) from exc

        return context
