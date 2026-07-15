# Content Intelligence

This is the **business brain** of ACIS: the rules that decide *what* the system
produces, *why*, and *how it gets better*. Engines implement these rules; this
document is the single source of truth for them. When an engine's behaviour and
this document disagree, this document wins (and the engine is a bug).

The north star: **knowledge content with high save- and share-potential**,
always fact-based, always sourced, on-brand, for Instagram and TikTok — produced
autonomously.

---

## 1. How topics are found

Discovery is a funnel from broad signals to a small set of well-formed topics.

1. **Signal aggregation.** The Trend Intelligence Engine pulls from multiple
   independent `TrendSourcePort`s: search interest (e.g. Google Trends), social
   velocity (TikTok/Instagram hashtags & sounds), news, community discussion
   (Reddit), and reference demand (Wikipedia pageviews). Each signal becomes a
   `Trend` with a source-native `score`.
2. **Niche filter.** Drop signals that cannot become evergreen knowledge content
   (transient drama, pure product hype). Map survivors to a `TopicCategory`
   (science, history, space, psychology, …).
3. **Clustering.** Related keywords are merged into one `Topic`; the LLM proposes
   a working `title` and an `angle` (the specific framing, e.g. *myth vs.
   reality*, *the number nobody expects*, *how X actually works*).
4. **Evergreen weighting.** Prefer topics with lasting value over pure spikes. A
   topic's momentum matters, but a permanently-interesting topic with moderate
   momentum beats a flash-in-the-pan spike.

**Two signal classes, combined:**
- *Reactive* — riding a current spike (timeliness, reach).
- *Evergreen* — consistently searched/saved knowledge (durability, library
  value). The mix is configurable; the default leans evergreen because saves and
  shares reward lasting utility.

---

## 2. Source screening (before scoring) and prioritisation

Per [ADR-0005](docs/architecture/adr/0005-pipeline-ordering-screen-score-research.md),
a **cheap source screen runs before any virality scoring**. A topic that cannot
be backed by enough credible sources is discarded immediately — no matter how
viral it looks.

**Screening** (`ResearchEngine.screen`) answers one question: *are there at least
`quality.min_sources_per_topic` credible, independent sources for this topic?* It
checks availability, not truth. Output: `SourceAvailability`.

**Source priority tiers** (higher tier = higher `reliability`, preferred for both
screening and citation):

| Tier | Examples | Reliability |
| --- | --- | --- |
| 1 — Primary/official | Peer-reviewed papers, official statistics (UN, Eurostat, World Bank), space agencies, standards bodies | 0.9–1.0 |
| 2 — Reference/expert | Encyclopedic (Wikipedia/Wikidata with citations), established science outlets, university explainers | 0.7–0.9 |
| 3 — Quality journalism | Reputable outlets with editorial standards | 0.5–0.7 |
| 4 — Weak/unranked | Blogs, forums, social posts | ≤ 0.4 (never sole support) |

Rules:
- A claim needs **≥ 2 independent sources**, and at least one should be Tier 1–2.
- Independence matters: three outlets citing the same wire story count as one.
- Recency matters for "current developments"; correctness always outranks recency.

---

## 3. How topics are scored (virality)

Only screened topics reach the Virality Engine. The score is **transparent and
weighted**, never a black box — every `ViralityScore` carries its `components`
and a `rationale`.

```
virality = Σ (weightᵢ · componentᵢ)      # normalised to [0..1]
```

Default components (weights live in config, tunable without code changes):

| Component | Meaning | Signal source |
| --- | --- | --- |
| `category_fit` | Does the category reliably over-index on saves/shares? | Learning Engine priors |
| `novelty` | Counter-intuitive / surprising ("most people get this wrong") | LLM estimate |
| `shareability` | Identity, utility, or emotion that makes people send it on | LLM + heuristics |
| `save_worthiness` | Reference value — is it worth keeping? | LLM + category prior |
| `trend_momentum` | Current attention strength | Trend signal |
| `historical_fit` | How past content on this theme performed | Learning Engine |

**Diversity guard:** the ranking must not collapse onto a single winning
category. A configurable diversity constraint / exploration budget keeps the
system discovering (see §8).

The top-ranked topic proceeds to deep research; the rest are persisted with their
scores for later reconsideration and for the Learning Engine.

---

## 4. How facts are validated

Deep research (`ResearchEngine.research`) runs for the **winning topic only** and
produces a structured `KnowledgeBase`: typed `facts` (each with a 0-100
confidence, source references, and visual potential), plus `statistics`,
`timeline`, `definitions`, weighted `sources`, `hook_candidates`, `visual_ideas`,
`uncertainties`, and `open_questions`.

Validation pipeline:
1. **Retrieve** from prioritised sources (§2).
2. **Extract candidate facts**, each tied to the source it came from.
3. **Cross-verify:** keep a fact only if corroborated by ≥ 2 independent sources;
   attach every supporting `Source` with its `reliability`.
4. **Anti-hallucination rule:** a fact must trace to a *retrieved* source. The
   LLM may summarise or phrase, but may not be the origin of a claim.
5. **Conflict handling:** when sources disagree, prefer higher tiers; if a claim
   remains contested, either frame it explicitly as contested or drop it.
6. **Highlight integrity:** every accent-styled number/`highlight` used later in
   the content must map to a verified dossier fact.

The Quality Engine re-checks these invariants before publishing (`fact_check`,
`source_check`), so validation is enforced twice: at creation and at the gate.

---

## 5. How duplication is avoided

The system must not repeat itself or flood one theme.

- **Topic-history check** at discovery: a normalised fingerprint of each
  published/queued topic (category + key entities + angle) is stored. New topics
  that are too similar (embedding/keyword similarity above a threshold) are
  suppressed or must offer a distinctly new angle.
- **Cooldowns:** per-topic and per-category cooldown windows prevent
  back-to-back repetition of the same subject area.
- **Angle differentiation:** the same subject may return only with a genuinely
  different `angle` (e.g. a new statistic, a myth-buster vs. an explainer).
- **Asset/caption reuse detection** guards against near-identical output even
  when the topic label differs.

All fingerprints live in the repository so deduplication survives restarts.

---

## 6. Format decision — Instagram carousel, TikTok, or both

Every topic is evaluated for platform fit; the default target is **both**, but
the engine may choose one when a format clearly doesn't suit the material.

Heuristics:

| Signal | Leans carousel (IG) | Leans video (TikTok) |
| --- | --- | --- |
| Information density | High — many discrete facts, stats, rankings | Lower — one strong idea |
| Save intent | Strong (reference/list material) | Moderate |
| Narrative/temporal flow | Weak | Strong (story, reveal, process) |
| Visual motion value | Low | High |
| Optimal length | 6–10 slides | 15–30 s |

Decision rule:
- **Both** when the topic is information-dense *and* has a hookable narrative
  (the common case for knowledge content) — build the carousel first, then
  derive the TikTok from the same research/design.
- **Carousel-only** for dense list/stat/ranking content with little motion value.
- **TikTok-only** for single-idea, high-motion, story-driven items.

The carousel is the **primary artifact**; the TikTok Video Engine derives from
it so one research effort yields both, guaranteeing brand and fact consistency.

---

## 7. The quality gate (hard stop)

Nothing publishes unless the Quality Engine's `overall` score ≥
`quality.min_score`. Gates: `fact_check`, `source_check`, `spelling_check`,
`design_check`, aggregated into `overall_score`. The rule is enforced in the
**pipeline orchestrator**, not in any single engine, so it cannot be bypassed.
See the [Quality Engine design](docs/architecture/modules/quality-engine.md).

---

## 8. KPIs and the learning loop

Knowledge content is optimised primarily for **saves and shares**, not vanity
likes. The Analytics Engine collects, the Learning Engine turns metrics into
guidance that feeds §1–§3 of the next cycle.

**Primary KPIs**
- **Save rate** = saves / impressions — the strongest signal of reference value.
- **Share rate** = shares / impressions — the strongest signal of virality.
- **Watch-through / average watch time** (TikTok) — hook and pacing quality.

**Secondary KPIs**
- Reach / impressions, follows-per-post, completion rate, replays, comments
  (qualitative signal), profile visits.

**How KPIs flow back**
- Save/share rates update **category and angle priors** used by `category_fit`,
  `save_worthiness`, and `historical_fit` in virality scoring (§3).
- Watch-through informs **content structure and hook** choices (Content Engine)
  and **video pacing** (TikTok Video Engine).
- Best-performing **posting windows** feed the Publishing Engine's scheduling.

**Learning discipline**
- **Shrinkage/priors** before acting on small samples (don't overreact to one
  post).
- **Exploration budget:** a fixed fraction of runs deliberately explores
  new categories/angles to avoid feedback collapse (always chasing the last
  winner).
- Start simple (exponential-moving-average priors) and graduate to a
  bandit/regression as data volume grows — see the
  [Learning Engine design](docs/architecture/modules/learning-engine.md).

---

## Configuration touchpoints

These knobs (in `config/*.yaml`, overridable by env) govern the behaviour above:

| Setting | Controls |
| --- | --- |
| `quality.min_sources_per_topic` | Screening threshold (§2) |
| `quality.min_score` | Publish gate (§7) |
| `content.platforms`, `content.instagram_carousel_slides` | Format defaults (§6) |
| `content.topics` | Allowed categories (§1) |
| `branding.*` | On-brand design constraints (§6, §7) |

Virality weights, cooldown windows, similarity thresholds, and the exploration
budget will be added as explicit config keys when the respective engines are
implemented, so the whole content strategy stays tunable without code changes.
