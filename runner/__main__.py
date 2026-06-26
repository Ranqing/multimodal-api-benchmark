from __future__ import annotations

import argparse
import sys

from .adapters import ADAPTERS
from .config import load_config
from .core import RunOptions, load_samples, run_benchmark, write_csv, write_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run multimodal API benchmarks from exported dashboard config.")
    parser.add_argument("--config", required=False, help="Path to runner_config.json exported from dashboard.")
    parser.add_argument("--out", default="benchmark-results.csv", help="CSV output path.")
    parser.add_argument("--jsonl", help="Optional JSONL output path.")
    parser.add_argument("--dry-run", action="store_true", help="Build requests without sending them.")
    parser.add_argument("--profile", action="append", help="Profile id to include. Repeatable.")
    parser.add_argument("--task", action="append", help="Task id to include. Repeatable.")
    parser.add_argument("--api-key-env", action="append", default=[], help="Map id to env var, e.g. deepwl=DEEPWL_API_KEY.")
    parser.add_argument("--samples", help="Task sample JSON with prompt/image_url/video_url per task.")
    parser.add_argument("--sample-image-url", help="Image URL used by image-capable tasks.")
    parser.add_argument("--sample-video-url", help="Video URL used by video-capable tasks.")
    parser.add_argument("--supplier", action="append", help="Supplier id to include. Defaults to deepwl. Repeatable.")
    parser.add_argument("--all-profiles", action="store_true", help="Run every profile from config instead of DeepWL-only default.")
    parser.add_argument("--list-adapters", action="store_true", help="Print supported protocol adapters.")
    args = parser.parse_args(argv)

    if args.list_adapters:
        for name in sorted(ADAPTERS):
            print(name)
        return 0
    if not args.config:
        parser.error("--config required unless --list-adapters is used")

    config = load_config(args.config)
    if args.sample_image_url:
        config["runner"]["sampleImageUrl"] = args.sample_image_url
    if args.sample_video_url:
        config["runner"]["sampleVideoUrl"] = args.sample_video_url
    samples = load_samples(args.samples)
    rows = run_benchmark(
        config,
        RunOptions(
            dry_run=args.dry_run,
            env_overrides=_parse_env_overrides(args.api_key_env),
            profile_ids=set(args.profile or []) or None,
            task_ids=set(args.task or []) or None,
            samples=samples,
            supplier_ids=tuple(args.supplier or ["deepwl"]),
            all_profiles=args.all_profiles,
        ),
    )
    write_csv(args.out, rows, config.get("output_schema"))
    if args.jsonl:
        write_jsonl(args.jsonl, rows)
    print(f"wrote {len(rows)} rows to {args.out}")
    if args.jsonl:
        print(f"wrote JSONL to {args.jsonl}")
    return 0


def _parse_env_overrides(values: list[str]) -> dict[str, str]:
    result = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"invalid --api-key-env {value!r}; expected id=ENV_NAME")
        key, env_name = value.split("=", 1)
        import os

        result[key] = os.getenv(env_name, "")
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
