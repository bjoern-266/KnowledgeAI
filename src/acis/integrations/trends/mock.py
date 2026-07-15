"""Deterministic mock trend source.

Generates plausible, stable trend signals across the configured knowledge
categories so the pipeline can run fully offline. Determinism (seeded by
region) keeps tests reproducible.
"""

from __future__ import annotations

import random

from acis.core.config import IntegrationMode
from acis.domain.enums import TopicCategory
from acis.integrations.base import IntegrationAdapter

_SEED_KEYWORDS: dict[TopicCategory, list[str]] = {
    TopicCategory.SCIENCE: ["quantum entanglement", "CRISPR", "dark matter"],
    TopicCategory.SPACE: ["James Webb images", "black hole jets", "Mars water"],
    TopicCategory.HISTORY: ["lost Roman roads", "Bronze Age collapse"],
    TopicCategory.AI: ["reasoning models", "AI energy use"],
    TopicCategory.PSYCHOLOGY: ["dopamine myths", "memory palaces"],
    TopicCategory.HEALTH: ["sleep and immunity", "protein timing"],
    TopicCategory.NATURE: ["octopus intelligence", "fungal networks"],
    TopicCategory.STATISTICS: ["global literacy", "energy mix 2025"],
}


class MockTrendSource(IntegrationAdapter):
    integration = "trends"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def fetch_trends(self, *, region: str = "global", limit: int = 20) -> list:
        from acis.domain.models import Trend

        rng = random.Random(f"{region}")
        pool: list[Trend] = []
        for category, keywords in _SEED_KEYWORDS.items():
            for keyword in keywords:
                pool.append(
                    Trend(
                        keyword=keyword,
                        source="mock",
                        score=round(rng.uniform(0.3, 1.0), 3),
                        region=region,
                        category=category,
                    )
                )
        pool.sort(key=lambda t: t.score, reverse=True)
        self.log.debug("mock.fetch_trends", region=region, returned=min(limit, len(pool)))
        return pool[:limit]
