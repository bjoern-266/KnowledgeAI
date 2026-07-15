"""ACIS - Autonomous Content Intelligence System.

A fully modular, self-driving pipeline that discovers trends, researches
facts, produces branded knowledge content for Instagram & TikTok, and learns
from performance - without manual intervention.

The package is organised into clearly separated layers:

* ``acis.core``         - cross-cutting infrastructure (config, logging,
                          errors, base classes, scheduler, pipeline).
* ``acis.domain``       - shared data contracts (models) exchanged between
                          modules. This is the only coupling allowed between
                          otherwise independent modules.
* ``acis.data``         - persistence (repository pattern; memory + sqlite).
* ``acis.integrations`` - the ONLY layer permitted to talk to external APIs.
                          Every integration ships a mock and a live adapter.
* ``acis.engines``      - the business modules (trend, virality, research,
                          content, ...). Only interfaces exist in the
                          foundation; implementations follow per-module review.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
