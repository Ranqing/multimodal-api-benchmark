from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_SCHEMA = [
    "run_id",
    "platform",
    "profile",
    "protocol",
    "endpoint",
    "model",
    "task_type",
    "input_mode",
    "stream",
    "concurrency",
    "status_code",
    "error_type",
    "ttfb_ms",
    "ttft_ms",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "tokens_per_second",
    "cost",
    "capability_score",
    "stability_score",
    "total_score",
]


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    return normalize_config(config)


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    runner = config.setdefault("runner", {})
    runner["repeatCount"] = int(runner.get("repeatCount") or runner.get("repeat_count") or 1)
    runner["timeoutSeconds"] = int(runner.get("timeoutSeconds") or runner.get("timeout_seconds") or 120)
    runner["concurrencyLevels"] = _parse_concurrency(runner.get("concurrencyLevels") or runner.get("concurrency_levels") or [1])
    runner["streaming"] = bool(runner.get("streaming", False))
    config["api_profiles"] = [_normalize_profile(item) for item in config.get("api_profiles", [])]
    config["tasks"] = [_normalize_task(item) for item in config.get("tasks", [])]
    config["output_schema"] = config.get("output_schema") or DEFAULT_OUTPUT_SCHEMA
    if not config["api_profiles"]:
        raise ValueError("config has no api_profiles")
    if not config["tasks"]:
        raise ValueError("config has no tasks")
    return config


def _normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(profile)
    if "model" not in normalized and "selectedModel" in normalized:
        normalized["model"] = normalized["selectedModel"]
    if "endpoint" not in normalized:
        raise ValueError(f"profile {normalized.get('id')} missing endpoint")
    if "model" not in normalized:
        raise ValueError(f"profile {normalized.get('id')} missing model")
    normalized["platform_id"] = normalized.get("platform_id") or _platform_id(normalized.get("platform", ""))
    normalized["method"] = normalized.get("method") or "POST"
    return normalized


def _normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(task)
    if "id" not in normalized:
        raise ValueError(f"task missing id: {task}")
    normalized["title"] = normalized.get("title") or normalized["id"]
    normalized["metrics"] = normalized.get("metrics") or []
    return normalized


def _parse_concurrency(value: Any) -> list[int]:
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        values = value
    else:
        values = [value]
    levels = []
    for item in values:
        number = int(item)
        if number > 0:
            levels.append(number)
    return levels or [1]


def _platform_id(name: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in str(name)).strip("_")
