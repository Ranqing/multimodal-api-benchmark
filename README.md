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
cd /Users/ranqing/Projects/multimodal-api-benchmark
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
