# Benchmark runner

Stdlib Python runner for config exported by dashboard. Default run scope is DeepWL profiles only.

## Run dry validation

```bash
python3 -m runner --config multimodal-api-benchmark-config.json --samples samples.json --dry-run --out dry-run.csv --jsonl dry-run.jsonl
```

## Run real requests

```bash
export DEEPWL_API_KEY="..."
python3 -m runner --config multimodal-api-benchmark-config.json --samples samples.json --out results.csv --jsonl results.jsonl
```

Keys use normalized platform/profile env names:

- `DEEPWL_API_KEY`
- `ANT_DIGITAL_DTMAAS_API_KEY`
- `DEEPWL_CLAUDE_MESSAGES_API_KEY`

Override mapping:

```bash
python3 -m runner --config config.json --api-key-env deepwl=MY_DEEPWL_KEY
```

## Samples

```json
{
  "tasks": {
    "vqa": {
      "prompt": "Describe this image in one sentence.",
      "image_url": "https://example.test/sample.png"
    },
    "video-qa": {
      "prompt": "Summarize this video.",
      "video_url": "https://example.test/sample.mp4"
    }
  }
}
```

Missing `image_url` / `video_url` falls back to text-only request for that task.

## Profile selection

By default, only `deepwl` profiles run. Use `--profile` and `--task` to narrow. Use `--all-profiles` only when supplier adapters/templates are ready.

## Add supplier

Preferred: add protocol adapter in `runner/adapters.py`, register in `ADAPTERS`.

No-code path: use `template_json` protocol in config:

```json
{
  "id": "supplier-profile",
  "platform": "Supplier",
  "protocol": "template_json",
  "endpoint": "https://supplier.example/v1/run",
  "method": "POST",
  "auth_header": "Authorization",
  "auth_value_template": "Bearer ${api_key}",
  "model": "model-id",
  "request_template": {
    "model": "${model}",
    "prompt": "${prompt}",
    "image_url": "${image_url}",
    "max_tokens": "${max_tokens}",
    "stream": "${streaming}"
  }
}
```

DTMaaS profiles currently map to `template_json`; exact `request_template` needs supplier docs.
