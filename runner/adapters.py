from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass
from string import Template
from typing import Any


@dataclass(frozen=True)
class RequestSpec:
    method: str
    url: str
    headers: dict[str, str]
    body: dict[str, Any]
    input_mode: str


class AdapterError(RuntimeError):
    pass


class BaseAdapter:
    protocol = "base"

    def build(self, profile: dict[str, Any], task: dict[str, Any], runner: dict[str, Any], api_key: str) -> RequestSpec:
        raise NotImplementedError

    def _base_headers(self, profile: dict[str, Any]) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        headers.update({str(key): str(value) for key, value in (profile.get("headers") or {}).items()})
        return headers

    def _common_text(self, task: dict[str, Any]) -> str:
        if task.get("prompt"):
            return str(task["prompt"])
        title = task.get("title") or task.get("id") or "multimodal task"
        metrics = ", ".join(task.get("metrics") or [])
        return (
            f"Run benchmark task: {title}. "
            f"Answer concisely. Include observable evidence. Metrics: {metrics or 'accuracy, latency'}."
        )

    def _image_url(self, task: dict[str, Any], runner: dict[str, Any]) -> str | None:
        if task.get("image_url"):
            return str(task["image_url"])
        by_task = runner.get("sampleImageUrls") or runner.get("sample_image_urls") or {}
        return by_task.get(task.get("id")) or runner.get("sampleImageUrl") or runner.get("sample_image_url")

    def _video_url(self, task: dict[str, Any], runner: dict[str, Any]) -> str | None:
        if task.get("video_url"):
            return str(task["video_url"])
        by_task = runner.get("sampleVideoUrls") or runner.get("sample_video_urls") or {}
        return by_task.get(task.get("id")) or runner.get("sampleVideoUrl") or runner.get("sample_video_url")

    def _input_mode(self, task: dict[str, Any], runner: dict[str, Any]) -> str:
        task_id = str(task.get("id") or "")
        if "video" in task_id and self._video_url(task, runner):
            return "video_url"
        if any(part in task_id for part in ("image", "ocr", "chart", "vqa", "spatial")) and self._image_url(task, runner):
            return "image_url"
        return "text"


class AnthropicMessagesAdapter(BaseAdapter):
    protocol = "anthropic_messages"

    def build(self, profile: dict[str, Any], task: dict[str, Any], runner: dict[str, Any], api_key: str) -> RequestSpec:
        headers = self._base_headers(profile)
        headers["x-api-key"] = api_key
        headers.setdefault("anthropic-version", "2023-06-01")
        content: list[dict[str, Any]] = []
        image_url = self._image_url(task, runner)
        if image_url:
            content.append({"type": "image", "source": {"type": "url", "url": image_url}})
        content.append({"type": "text", "text": self._common_text(task)})
        body = {
            "model": profile["model"],
            "max_tokens": int(runner.get("maxTokens") or runner.get("max_tokens") or 1024),
            "temperature": float(runner.get("temperature", 0.2)),
            "stream": bool(runner.get("streaming", False)),
            "messages": [{"role": "user", "content": content}],
        }
        return RequestSpec(profile.get("method", "POST"), profile["endpoint"], headers, body, self._input_mode(task, runner))


class OpenAIResponsesAdapter(BaseAdapter):
    protocol = "openai_responses"

    def build(self, profile: dict[str, Any], task: dict[str, Any], runner: dict[str, Any], api_key: str) -> RequestSpec:
        headers = self._base_headers(profile)
        headers["Authorization"] = f"Bearer {api_key}"
        content: list[dict[str, Any]] = [{"type": "input_text", "text": self._common_text(task)}]
        image_url = self._image_url(task, runner)
        if image_url:
            content.append({"type": "input_image", "image_url": image_url, "detail": "high"})
        body = {
            "model": profile["model"],
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": int(runner.get("maxTokens") or runner.get("max_output_tokens") or 1024),
            "temperature": float(runner.get("temperature", 0.2)),
            "stream": bool(runner.get("streaming", False)),
        }
        if body["stream"]:
            body["stream_options"] = {"include_usage": True}
        return RequestSpec(profile.get("method", "POST"), profile["endpoint"], headers, body, self._input_mode(task, runner))


class OpenAIChatAdapter(BaseAdapter):
    protocol = "openai_chat"

    def build(self, profile: dict[str, Any], task: dict[str, Any], runner: dict[str, Any], api_key: str) -> RequestSpec:
        headers = self._base_headers(profile)
        headers["Authorization"] = f"Bearer {api_key}"
        content: list[dict[str, Any]] = []
        image_url = self._image_url(task, runner)
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url, "detail": "high"}})
        content.append({"type": "text", "text": self._common_text(task)})
        body = {
            "model": profile["model"],
            "messages": [{"role": "user", "content": content}],
            "max_tokens": int(runner.get("maxTokens") or runner.get("max_tokens") or 1024),
            "temperature": float(runner.get("temperature", 0.2)),
            "stream": bool(runner.get("streaming", False)),
        }
        return RequestSpec(profile.get("method", "POST"), profile["endpoint"], headers, body, self._input_mode(task, runner))


class TemplateJsonAdapter(BaseAdapter):
    protocol = "template_json"

    def build(self, profile: dict[str, Any], task: dict[str, Any], runner: dict[str, Any], api_key: str) -> RequestSpec:
        template = profile.get("request_template")
        if not template:
            raise AdapterError(
                f"profile {profile.get('id')} uses {profile.get('protocol')} but has no request_template"
            )
        headers = self._base_headers(profile)
        auth_header = profile.get("auth_header") or "Authorization"
        auth_value = profile.get("auth_value_template") or "Bearer ${api_key}"
        headers[str(auth_header)] = Template(str(auth_value)).safe_substitute(api_key=api_key)
        variables = {
            "api_key": api_key,
            "model": profile["model"],
            "prompt": self._common_text(task),
            "image_url": self._image_url(task, runner) or "",
            "video_url": self._video_url(task, runner) or "",
            "max_tokens": str(runner.get("maxTokens") or runner.get("max_tokens") or 1024),
            "temperature": str(runner.get("temperature", 0.2)),
            "streaming": json.dumps(bool(runner.get("streaming", False))),
        }
        body = _substitute_template(copy.deepcopy(template), variables)
        return RequestSpec(profile.get("method", "POST"), profile["endpoint"], headers, body, self._input_mode(task, runner))


ADAPTERS: dict[str, BaseAdapter] = {
    AnthropicMessagesAdapter.protocol: AnthropicMessagesAdapter(),
    OpenAIResponsesAdapter.protocol: OpenAIResponsesAdapter(),
    OpenAIChatAdapter.protocol: OpenAIChatAdapter(),
    TemplateJsonAdapter.protocol: TemplateJsonAdapter(),
    "antdigital_modelservice": TemplateJsonAdapter(),
}


def adapter_for(protocol: str) -> BaseAdapter:
    try:
        return ADAPTERS[protocol]
    except KeyError as exc:
        available = ", ".join(sorted(ADAPTERS))
        raise AdapterError(f"unsupported protocol {protocol!r}; available: {available}") from exc


def api_key_for(profile: dict[str, Any], env_overrides: dict[str, str] | None = None) -> str:
    platform = str(profile.get("platform_id") or profile.get("platformId") or profile.get("platform") or "").strip()
    profile_id = str(profile.get("id") or "").strip()
    candidates = []
    if env_overrides:
        for key in [profile_id, platform]:
            candidates.extend(env_overrides.get(item) for item in _override_keys(key))
    candidates.extend([
        os.getenv(_env_name(profile_id, "API_KEY")),
        os.getenv(_env_name(platform, "API_KEY")),
        os.getenv("MULTIMODAL_API_KEY"),
    ])
    for value in candidates:
        if value:
            return value
    raise AdapterError(
        f"missing API key for profile {profile_id}; set {_env_name(profile_id, 'API_KEY')} or {_env_name(platform, 'API_KEY')}"
    )


def _env_name(value: str, suffix: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()
    return f"{safe}_{suffix}" if safe else suffix


def _override_keys(value: str) -> list[str]:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return [value, value.lower(), normalized]


def _substitute_template(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        text = Template(value).safe_substitute(variables)
        if text == "true":
            return True
        if text == "false":
            return False
        if re.fullmatch(r"-?\d+", text):
            return int(text)
        if re.fullmatch(r"-?\d+\.\d+", text):
            return float(text)
        return text
    if isinstance(value, list):
        return [_substitute_template(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: _substitute_template(item, variables) for key, item in value.items()}
    return value
