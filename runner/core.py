from __future__ import annotations

import csv
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .adapters import AdapterError, adapter_for, api_key_for
from .config import DEFAULT_OUTPUT_SCHEMA


@dataclass(frozen=True)
class RunOptions:
    dry_run: bool = False
    env_overrides: dict[str, str] | None = None
    profile_ids: set[str] | None = None
    task_ids: set[str] | None = None
    samples: dict[str, Any] | None = None
    supplier_ids: tuple[str, ...] | None = ("deepwl",)
    all_profiles: bool = False


def run_benchmark(config: dict[str, Any], options: RunOptions) -> list[dict[str, Any]]:
    profiles = _select_profiles(config["api_profiles"], options)
    tasks = _filter(config["tasks"], options.task_ids)
    runner = config["runner"]
    rows: list[dict[str, Any]] = []
    for concurrency in runner["concurrencyLevels"]:
        jobs = [
            (profile, task, repeat_index, concurrency)
            for profile in profiles
            for task in tasks
            for repeat_index in range(runner["repeatCount"])
        ]
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(_run_one, config, runner, profile, task, repeat_index, concurrency, options) for profile, task, repeat_index, concurrency in jobs]
            for future in as_completed(futures):
                rows.append(future.result())
    return rows


def write_csv(path: str | Path, rows: Iterable[dict[str, Any]], schema: list[str] | None = None) -> None:
    fieldnames = schema or DEFAULT_OUTPUT_SCHEMA
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _run_one(
    config: dict[str, Any],
    runner: dict[str, Any],
    profile: dict[str, Any],
    task: dict[str, Any],
    repeat_index: int,
    concurrency: int,
    options: RunOptions,
) -> dict[str, Any]:
    started = time.perf_counter()
    run_id = str(uuid.uuid4())
    base = {
        "run_id": run_id,
        "platform": profile.get("platform", ""),
        "profile": profile.get("name") or profile.get("id", ""),
        "protocol": profile.get("protocol", ""),
        "endpoint": profile.get("endpoint", ""),
        "model": profile.get("model", ""),
        "task_type": task.get("id", ""),
        "stream": bool(runner.get("streaming", False)),
        "concurrency": concurrency,
        "status_code": "",
        "error_type": "",
        "ttfb_ms": "",
        "ttft_ms": "",
        "latency_ms": "",
        "input_tokens": "",
        "output_tokens": "",
        "tokens_per_second": "",
        "cost": "",
        "capability_score": "",
        "stability_score": "",
        "total_score": "",
        "repeat_index": repeat_index,
    }
    try:
        task = _merge_sample(task, options.samples)
        api_key = "dry-run-key" if options.dry_run else api_key_for(profile, options.env_overrides)
        spec = adapter_for(profile["protocol"]).build(profile, task, runner, api_key)
        base["input_mode"] = spec.input_mode
        estimated_input_tokens = _estimate_tokens(json.dumps(spec.body, ensure_ascii=False))
        base["input_tokens"] = estimated_input_tokens
        base["request"] = {"method": spec.method, "url": spec.url, "headers": _redact(spec.headers), "body": spec.body}
        if options.dry_run:
            base.update({"status_code": "DRY_RUN", "latency_ms": 0, "ttfb_ms": 0, "ttft_ms": 0})
            return base
        result = _send(spec.method, spec.url, spec.headers, spec.body, int(runner["timeoutSeconds"]), bool(spec.body.get("stream")))
        if not result.get("input_tokens"):
            result.pop("input_tokens", None)
        base.update(result)
        base["latency_ms"] = round((time.perf_counter() - started) * 1000)
        if result.get("output_text"):
            output_tokens = _estimate_tokens(result["output_text"])
            base["output_tokens"] = output_tokens
            latency_seconds = max(float(base["latency_ms"]) / 1000, 0.001)
            base["tokens_per_second"] = round(output_tokens / latency_seconds, 2)
        base["stability_score"] = 100 if int(base["status_code"]) < 500 else 0
        return base
    except (AdapterError, HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        base["error_type"] = exc.__class__.__name__
        base["latency_ms"] = round((time.perf_counter() - started) * 1000)
        if isinstance(exc, HTTPError):
            base["status_code"] = exc.code
            try:
                base["error_body"] = exc.read(2048).decode("utf-8", errors="replace")
            except OSError:
                pass
        else:
            base["status_code"] = "ERROR"
            base["error_message"] = str(exc)
        base["stability_score"] = 0
        return base


def _send(method: str, url: str, headers: dict[str, str], body: dict[str, Any], timeout: int, stream: bool) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    req = Request(url, data=payload, headers=headers, method=method)
    started = time.perf_counter()
    with urlopen(req, timeout=timeout) as response:
        ttfb_ms = round((time.perf_counter() - started) * 1000)
        first_body_at = None
        chunks: list[bytes] = []
        if stream:
            while True:
                chunk = response.readline()
                if not chunk:
                    break
                if first_body_at is None and chunk.strip():
                    first_body_at = time.perf_counter()
                chunks.append(chunk)
        else:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                if first_body_at is None:
                    first_body_at = time.perf_counter()
                chunks.append(chunk)
        raw = b"".join(chunks)
    ttft_ms = round(((first_body_at or time.perf_counter()) - started) * 1000)
    text = raw.decode("utf-8", errors="replace")
    if stream:
        parsed = parse_sse(text)
        return {
            "status_code": response.status,
            "ttfb_ms": ttfb_ms,
            "ttft_ms": ttft_ms,
            "output_text": parsed["output_text"],
            "output_tokens": parsed.get("output_tokens", ""),
            "input_tokens": parsed.get("input_tokens", ""),
            "response_event_count": len(parsed["events"]),
            "response_events": parsed["events"],
            "raw_response": text,
        }
    parsed_json = _loads_json(text)
    return {
        "status_code": response.status,
        "ttfb_ms": ttfb_ms,
        "ttft_ms": ttft_ms,
        "output_text": _extract_output_text(parsed_json) or text,
        "output_tokens": _extract_usage(parsed_json).get("output_tokens", ""),
        "raw_response": text,
        "parsed_response": parsed_json,
    }


def load_samples(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8") as handle:
        samples = json.load(handle)
    if not isinstance(samples, dict):
        raise ValueError("samples JSON must be an object")
    tasks = samples.get("tasks", {})
    if not isinstance(tasks, dict):
        raise ValueError("samples.tasks must be an object")
    return samples


def parse_sse(text: str) -> dict[str, Any]:
    events: list[Any] = []
    output_parts: list[str] = []
    usage: dict[str, Any] = {}
    for block in re_split_sse_blocks(text):
        data_lines = []
        for line in block.splitlines():
            if line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if not data_lines:
            continue
        data = "\n".join(data_lines)
        if data == "[DONE]":
            events.append("[DONE]")
            continue
        event = _loads_json(data)
        events.append(event)
        output_parts.extend(_extract_text_deltas(event))
        usage.update(_extract_usage(event))
    return {
        "events": events,
        "output_text": "".join(output_parts),
        "input_tokens": usage.get("input_tokens", ""),
        "output_tokens": usage.get("output_tokens", ""),
    }


def re_split_sse_blocks(text: str) -> list[str]:
    return [block for block in text.replace("\r\n", "\n").split("\n\n") if block.strip()]


def _select_profiles(profiles: list[dict[str, Any]], options: RunOptions) -> list[dict[str, Any]]:
    selected = _filter(profiles, options.profile_ids)
    if options.all_profiles:
        return selected
    suppliers = set(options.supplier_ids or ())
    if not suppliers:
        return selected
    return [profile for profile in selected if _supplier_id(profile) in suppliers]


def _supplier_id(profile: dict[str, Any]) -> str:
    value = profile.get("platform_id") or profile.get("platformId") or profile.get("platform") or ""
    return "".join(char.lower() if char.isalnum() else "_" for char in str(value)).strip("_")


def _merge_sample(task: dict[str, Any], samples: dict[str, Any] | None) -> dict[str, Any]:
    sample = ((samples or {}).get("tasks") or {}).get(task.get("id")) or {}
    if not isinstance(sample, dict):
        raise ValueError(f"sample for task {task.get('id')} must be an object")
    merged = dict(task)
    for key in ("prompt", "image_url", "video_url"):
        if sample.get(key):
            merged[key] = sample[key]
    return merged


def _filter(items: list[dict[str, Any]], ids: set[str] | None) -> list[dict[str, Any]]:
    if not ids:
        return items
    return [item for item in items if item.get("id") in ids]


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def _redact(headers: dict[str, str]) -> dict[str, str]:
    redacted = dict(headers)
    for key in list(redacted):
        if key.lower() in {"authorization", "x-api-key", "api-key"}:
            redacted[key] = "***"
    return redacted


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _loads_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _extract_usage(value: Any) -> dict[str, Any]:
    usage = _find_usage(value)
    if not isinstance(usage, dict):
        return {}
    return {
        "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens") or "",
        "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens") or "",
    }


def _find_usage(value: Any) -> Any:
    if isinstance(value, dict):
        if isinstance(value.get("usage"), dict):
            return value["usage"]
        for item in value.values():
            found = _find_usage(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _find_usage(item)
            if found:
                return found
    return None


def _extract_output_text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    if isinstance(value.get("output_text"), str):
        return value["output_text"]
    parts: list[str] = []
    for item in value.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    for content in value.get("content") or []:
        if isinstance(content, dict) and isinstance(content.get("text"), str):
            parts.append(content["text"])
    return "".join(parts)


def _extract_text_deltas(value: Any) -> list[str]:
    parts: list[str] = []
    if isinstance(value, dict):
        event_type = str(value.get("type") or "")
        if event_type.endswith(".delta") and isinstance(value.get("delta"), str):
            parts.append(value["delta"])
        delta = value.get("delta")
        if isinstance(delta, dict):
            if isinstance(delta.get("text"), str):
                parts.append(delta["text"])
            if isinstance(delta.get("output_text"), str):
                parts.append(delta["output_text"])
        if event_type in {"content_block_delta", "response.output_text.delta"} and isinstance(value.get("text"), str):
            parts.append(value["text"])
        for item in value.values():
            parts.extend(_extract_text_deltas(item))
    elif isinstance(value, list):
        for item in value:
            parts.extend(_extract_text_deltas(item))
    return parts
