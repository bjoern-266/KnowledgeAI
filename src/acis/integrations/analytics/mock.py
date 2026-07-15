"""Mock analytics source.

Returns deterministic, plausible performance metrics per post id so the
Analytics and Learning engines can be developed and tested offline.
"""

from __future__ import annotations

import random

from acis.core.config import IntegrationMode
from acis.integrations.base import IntegrationAdapter


class MockAnalytics(IntegrationAdapter):
    integration = "analytics"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def fetch_metrics(self, external_id: str) -> dict[str, float]:
        rng = random.Random(external_id)
        impressions = rng.randint(1000, 50000)
        saves = int(impressions * rng.uniform(0.01, 0.08))
        shares = int(impressions * rng.uniform(0.005, 0.05))
        likes = int(impressions * rng.uniform(0.02, 0.12))
        self.log.debug("mock.fetch_metrics", external_id=external_id, impressions=impressions)
        return {
            "impressions": float(impressions),
            "likes": float(likes),
            "saves": float(saves),
            "shares": float(shares),
            "save_rate": round(saves / impressions, 4),
            "share_rate": round(shares / impressions, 4),
        }
