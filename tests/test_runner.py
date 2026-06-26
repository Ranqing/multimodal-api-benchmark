import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runner.adapters import AnthropicMessagesAdapter, OpenAIResponsesAdapter, TemplateJsonAdapter, api_key_for
from runner.config import load_config, normalize_config
from runner.core import RunOptions, load_samples, parse_sse, run_benchmark, write_csv, write_jsonl


class RunnerTests(unittest.TestCase):
    def test_normalize_exported_shape(self):
        config = normalize_config(
            {
                "api_profiles": [
                    {
                        "id": "p1",
                        "platform": "DeepWL",
                        "name": "OpenAI Responses",
                        "protocol": "openai_responses",
                        "endpoint": "https://example.test/responses",
                        "model": "gpt-5.5",
                    }
                ],
                "tasks": [{"id": "vqa", "title": "VQA"}],
                "runner": {"repeatCount": 2, "concurrencyLevels": "1,2"},
            }
        )
        self.assertEqual(config["runner"]["concurrencyLevels"], [1, 2])
        self.assertEqual(config["api_profiles"][0]["platform_id"], "deepwl")

    def test_openai_adapter_adds_image_when_available(self):
        spec = OpenAIResponsesAdapter().build(
            {
                "protocol": "openai_responses",
                "endpoint": "https://example.test/responses",
                "method": "POST",
                "headers": {},
                "model": "gpt-5.5",
            },
            {"id": "vqa", "title": "VQA", "metrics": []},
            {"sampleImageUrl": "https://example.test/image.png", "streaming": True},
            "key",
        )
        content = spec.body["input"][0]["content"]
        self.assertEqual(spec.headers["Authorization"], "Bearer key")
        self.assertEqual(content[1]["type"], "input_image")
        self.assertEqual(spec.input_mode, "image_url")
        self.assertEqual(spec.body["stream_options"], {"include_usage": True})

    def test_openai_adapter_matches_deepwl_docs_shape(self):
        spec = OpenAIResponsesAdapter().build(
            {
                "protocol": "openai_responses",
                "endpoint": "https://zx1.deepwl.net/v1/responses",
                "method": "POST",
                "headers": {},
                "model": "gpt-5.5",
            },
            {"id": "vqa", "prompt": "提取这张截图中的异常指标。", "image_url": "https://example.test/dashboard.png"},
            {"maxTokens": 1024, "temperature": 0.2, "streaming": False},
            "key",
        )
        self.assertEqual(spec.headers["Authorization"], "Bearer key")
        self.assertEqual(spec.body["input"][0]["content"][0], {"type": "input_text", "text": "提取这张截图中的异常指标。"})
        self.assertEqual(spec.body["input"][0]["content"][1]["type"], "input_image")
        self.assertEqual(spec.body["input"][0]["content"][1]["detail"], "high")

    def test_claude_adapter_matches_deepwl_docs_shape(self):
        spec = AnthropicMessagesAdapter().build(
            {
                "protocol": "anthropic_messages",
                "endpoint": "https://zx1.deepwl.net/v1/messages",
                "method": "POST",
                "headers": {"anthropic-version": "2023-06-01"},
                "model": "claude-opus-4-8",
            },
            {"id": "vqa", "prompt": "这张架构图里有哪些风险点？", "image_url": "https://example.test/architecture.png"},
            {"maxTokens": 1024, "temperature": 0.2, "streaming": False},
            "key",
        )
        self.assertEqual(spec.headers["x-api-key"], "key")
        self.assertEqual(spec.headers["anthropic-version"], "2023-06-01")
        content = spec.body["messages"][0]["content"]
        self.assertEqual(content[0]["type"], "image")
        self.assertEqual(content[1], {"type": "text", "text": "这张架构图里有哪些风险点？"})

    def test_template_adapter_substitutes_values(self):
        spec = TemplateJsonAdapter().build(
            {
                "id": "custom",
                "protocol": "template_json",
                "endpoint": "https://example.test",
                "model": "m1",
                "request_template": {"model": "${model}", "max_tokens": "${max_tokens}", "stream": "${streaming}"},
            },
            {"id": "text", "title": "Text", "metrics": []},
            {"maxTokens": 77, "streaming": False},
            "key",
        )
        self.assertEqual(spec.body["model"], "m1")
        self.assertEqual(spec.body["max_tokens"], 77)
        self.assertFalse(spec.body["stream"])

    def test_api_key_env_name_from_platform(self):
        self.assertEqual(
            api_key_for({"id": "profile", "platform": "Vendor"}, {"vendor": "secret"}),
            "secret",
        )

    def test_default_run_filters_to_deepwl_and_uses_samples(self):
        config = load_config(Path("tests/fixtures/exported_config.json"))
        samples = load_samples(Path("tests/fixtures/samples.json"))
        rows = run_benchmark(config, RunOptions(dry_run=True, samples=samples))
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["platform"] for row in rows}, {"DeepWL"})
        for row in rows:
            request = row["request"]
            self.assertNotIn("Ant Digital", row["platform"])
            self.assertIn(row["profile"], {"OpenAI Responses", "Claude Messages"})
            self.assertEqual(request["headers"].get("Authorization") or request["headers"].get("x-api-key"), "***")
            self.assertEqual(row["input_mode"], "image_url")

    def test_profile_and_task_filters(self):
        config = load_config(Path("tests/fixtures/exported_config.json"))
        rows = run_benchmark(
            config,
            RunOptions(dry_run=True, profile_ids={"deepwl-openai-responses"}, task_ids={"vqa"}),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["profile"], "OpenAI Responses")
        self.assertEqual(rows[0]["task_type"], "vqa")

    def test_missing_media_falls_back_to_text_only(self):
        spec = OpenAIResponsesAdapter().build(
            {
                "protocol": "openai_responses",
                "endpoint": "https://zx1.deepwl.net/v1/responses",
                "method": "POST",
                "headers": {},
                "model": "gpt-5.5",
            },
            {"id": "vqa", "prompt": "Text only"},
            {"streaming": False},
            "key",
        )
        self.assertEqual(spec.input_mode, "text")
        self.assertEqual(len(spec.body["input"][0]["content"]), 1)

    def test_parse_sse_collects_text_usage_and_done(self):
        parsed = parse_sse(
            'data: {"type":"response.output_text.delta","delta":"Hel"}\n\n'
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"lo"}}\n\n'
            'data: {"type":"response.completed","response":{"usage":{"input_tokens":3,"output_tokens":2}}}\n\n'
            "data: [DONE]\n\n"
        )
        self.assertEqual(parsed["output_text"], "Hello")
        self.assertEqual(parsed["input_tokens"], 3)
        self.assertEqual(parsed["output_tokens"], 2)
        self.assertEqual(parsed["events"][-1], "[DONE]")

    def test_dry_run_writes_csv_and_jsonl_for_two_deepwl_rows(self):
        config = load_config(Path("tests/fixtures/exported_config.json"))
        samples = load_samples(Path("tests/fixtures/samples.json"))
        rows = run_benchmark(config, RunOptions(dry_run=True, samples=samples))
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "dry-run.csv"
            jsonl_path = Path(temp_dir) / "dry-run.jsonl"
            write_csv(csv_path, rows, config["output_schema"])
            write_jsonl(jsonl_path, rows)
            csv_lines = csv_path.read_text(encoding="utf-8").splitlines()
            jsonl_lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(csv_lines), 3)
        self.assertEqual(len(jsonl_lines), 2)
        self.assertIn('"Authorization": "***"', jsonl_lines[0] + jsonl_lines[1])


if __name__ == "__main__":
    unittest.main()
