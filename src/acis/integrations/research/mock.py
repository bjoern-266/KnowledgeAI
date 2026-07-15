"""Deterministic mock research source.

Simulates a retrieval backend: for any query it returns a small, stable set of
documents whose ``snippets`` are single-claim sentences. Some claims are shared
across documents (so the Research Engine can corroborate them) and some appear
in only one (so single-source facts can be flagged uncertain). This lets the
whole research flow run offline and deterministically.

The claims are intentionally generic placeholders keyed to the query term - in
live mode a real adapter returns real documents. The point is to exercise fact
typing, confidence, cross-verification, hooks and visual ideas, not to assert
real-world facts.
"""

from __future__ import annotations

from datetime import timedelta

from acis.core.config import IntegrationMode
from acis.domain.enums import SourceType
from acis.domain.models import RetrievedDocument, _now
from acis.integrations.base import IntegrationAdapter


def _claims(term: str) -> dict[str, str]:
    return {
        "historical": f"{term} was first documented in 1912.",
        "statistic": f"About 68% of studies report a measurable effect related to {term}.",
        "definition": f"{term} is defined as a well-studied phenomenon in its field.",
        "myth": f"Contrary to popular belief, {term} is not caused by everyday habits.",
        "record": f"{term} holds the record for the largest value ever measured in its class.",
        "projection": (
            f"Some researchers suggest {term} could double by 2050, though evidence "
            "remains limited."
        ),
    }


class MockResearchSource(IntegrationAdapter):
    integration = "research"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def search(self, query: str, *, limit: int = 10) -> list[RetrievedDocument]:
        term = query.strip() or "the topic"
        c = _claims(term)
        recent = _now() - timedelta(days=365)
        older = _now() - timedelta(days=365 * 8)

        docs = [
            RetrievedDocument(
                url=f"https://journal.example/{abs(hash(term)) % 10000}",
                title=f"{term}: a review",
                publisher="Journal of Records",
                institution="Nature",
                reliability=0.95,
                source_type=SourceType.PRIMARY,
                scientific=True,
                published_at=recent,
                snippets=[c["historical"], c["statistic"], c["definition"], c["myth"], c["record"]],
            ),
            RetrievedDocument(
                url=f"https://encyclopedia.example/{abs(hash(term)) % 9999}",
                title=f"{term}",
                publisher="Encyclopaedia",
                institution="Encyclopaedia",
                reliability=0.80,
                source_type=SourceType.SECONDARY,
                scientific=False,
                published_at=recent,
                snippets=[c["historical"], c["statistic"], c["definition"], c["myth"]],
            ),
            RetrievedDocument(
                url=f"https://news.example/{abs(hash(term)) % 8888}",
                title=f"What to know about {term}",
                publisher="ScienceDaily",
                institution="ScienceDaily",
                reliability=0.65,
                source_type=SourceType.SECONDARY,
                scientific=False,
                published_at=older,
                snippets=[c["historical"], c["projection"]],
            ),
        ]
        self.log.debug("mock.search", query=term, returned=min(limit, len(docs)))
        return docs[:limit]
