# 多模态 API 测评台

这是一个零依赖的本地静态测评网站，用于规划和预览 DeepWL、Ant Digital DTMaaS 等多模态 API 的性能与能力测试。

## 当前内置接口档案

- DeepWL Claude Messages: <https://doc.deepwl.cn/zh/texts/claude-messages>
- DeepWL OpenAI Responses: <https://doc.deepwl.cn/zh/texts/openai-responses>
- Ant Digital ModelService 1779371228498001025: <https://maas.antdigital.com/models/modelservice-1779371228498001025>
- Ant Digital ModelService 1780022931241001664: <https://maas.antdigital.com/models/modelservice-1780022931241001664>

## 固定模型选项

每个接口档案的模型下拉框目前统一写死为：

- `claude-opus-4-8`，页面显示为 Claude Opus 4.8
- `gpt-5.5`，页面显示为 GPT-5.5

## 启动

```bash
python3 -m http.server 5179
```

然后打开：

```text
http://127.0.0.1:5179
```

## 当前能力

- 平台、Base URL、模型 ID 配置
- 按文档独立配置接口档案、协议、Endpoint 和模型下拉选择
- 多模态测试套件开关
- 并发、重复次数、超时、流式响应等 runner 参数
- 评分权重配置
- 离线样例结果生成
- 导出 `runner_config.json`
- 导出结果 CSV 模板

API Key 只保存在浏览器会话里，不会写入导出的配置文件。

## Benchmark Runner

本仓库现在包含一个零依赖 Python runner，可读取页面导出的 `runner_config.json`，默认只运行 DeepWL 档案，发起并发请求并输出 CSV / JSONL。

```bash
python3 -m runner --config multimodal-api-benchmark-config.json --samples samples.json --dry-run --out dry-run.csv --jsonl dry-run.jsonl
```

真实请求示例：

```bash
export DEEPWL_API_KEY="..."
python3 -m runner --config multimodal-api-benchmark-config.json --samples samples.json --out results.csv --jsonl results.jsonl
```

`samples.json` 用任务 ID 绑定测试输入：

```json
{
  "tasks": {
    "vqa": {
      "prompt": "Describe this image in one sentence.",
      "image_url": "https://example.test/sample.png"
    }
  }
}
```

新增供应商有两种方式：

- 在 `runner/adapters.py` 添加协议适配器并注册到 `ADAPTERS`
- 在配置里使用 `template_json` + `request_template`，无需改代码

Ant Digital DTMaaS 当前走模板适配路径；需要模型服务请求体和鉴权文档后才能填充真实 `request_template`。
