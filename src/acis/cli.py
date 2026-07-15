"""ACIS command-line entry point.

Commands:
    acis config            Show the resolved configuration (secrets redacted).
    acis health            Report the health of every integration adapter.
    acis run-once          Execute one full pipeline cycle (mock-safe).
    acis start             Run the scheduler loop (Ctrl-C to stop).

Everything is mock-safe by default: with no credentials the run completes
end-to-end against simulated backends.
"""

from __future__ import annotations

import argparse
import json
import sys

from acis.core.context import AppContext
from acis.core.errors import ACISError

_SECRET_HINTS = ("key", "secret", "token", "password")


def _redact(obj: object) -> object:
    """Recursively mask values whose key looks like a credential."""
    if isinstance(obj, dict):
        return {
            k: ("***" if any(h in k.lower() for h in _SECRET_HINTS) and v else _redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(item) for item in obj]
    return obj


def _cmd_config(ctx: AppContext) -> int:
    data = _redact(ctx.settings.model_dump(mode="json"))
    print(json.dumps(data, indent=2, default=str))
    return 0


def _cmd_health(ctx: AppContext) -> int:
    ctx.startup()
    try:
        ok = True
        for adapter in ctx.integrations.adapters():
            status = adapter.health_check()
            ok = ok and status.healthy
            mark = "OK " if status.healthy else "DOWN"
            print(f"[{mark}] {adapter.name:<22} {status.detail}")
        return 0 if ok else 1
    finally:
        ctx.shutdown()


def _cmd_run_once(ctx: AppContext, *, publish: bool) -> int:
    from acis.reference import build_reference_pipeline

    with ctx:
        pipeline = build_reference_pipeline(ctx)
        result = pipeline.run_once(publish=publish)
        print("Topic     :", result.topic.title, f"({result.topic.category.value})")
        print("Sources   :", result.dossier.source_count)
        print("Slides    :", len(result.content.slides))
        print("Design    :", result.design.design_id, f"({len(result.design.assets)} assets)")
        print("Video     :", result.video.asset.uri)
        verdict = "PASSED" if result.quality.passed else "REJECTED"
        print("Quality   :", f"{result.quality.overall:.2f}", verdict)
        for receipt in result.receipts:
            print(f"Publish   : {receipt.platform.value} -> {receipt.status.value} {receipt.url}")
        if result.metrics:
            print("Metrics   :", json.dumps(result.metrics))
    return 0


def _cmd_start(ctx: AppContext) -> int:
    import time

    from acis.reference import build_reference_pipeline

    with ctx:
        pipeline = build_reference_pipeline(ctx)
        jobs = ctx.settings.scheduler.jobs
        pipeline_job = jobs.get("content_pipeline")
        interval = pipeline_job.interval_seconds if pipeline_job else 3600
        ctx.scheduler.register(
            "content_pipeline",
            lambda: pipeline.run_once(),
            interval_seconds=interval,
        )
        ctx.scheduler.start()
        ctx.log.info("cli.start", interval=interval)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            ctx.log.info("cli.interrupted")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="acis", description="Autonomous Content Intelligence System"
    )
    parser.add_argument("--env", default=None, help="Environment (development|staging|production)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("config", help="Print the resolved configuration")
    sub.add_parser("health", help="Check integration health")

    run = sub.add_parser("run-once", help="Run one pipeline cycle")
    run.add_argument("--no-publish", action="store_true", help="Skip the publish step")

    sub.add_parser("start", help="Run the scheduler loop")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ctx = AppContext.create(env=args.env)
        if args.command == "config":
            return _cmd_config(ctx)
        if args.command == "health":
            return _cmd_health(ctx)
        if args.command == "run-once":
            return _cmd_run_once(ctx, publish=not args.no_publish)
        if args.command == "start":
            return _cmd_start(ctx)
    except ACISError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
