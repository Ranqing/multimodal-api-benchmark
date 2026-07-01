const fixedModelOptions = ["claude-opus-4-8", "gpt-5.5"];

const defaultState = {
  platforms: [
    {
      id: "deepwl",
      name: "DeepWL",
      docs: "https://doc.deepwl.cn/zh",
      endpoint: "https://api.deepwl.cn/v1",
      models: fixedModelOptions,
      selectedModel: "claude-opus-4-8",
      keySaved: false
    },
    {
      id: "antdigital",
      name: "Ant Digital DTMaaS",
      docs: "https://maas.antdigital.com/models",
      endpoint: "https://maas-api.antdigital.com",
      models: fixedModelOptions,
      selectedModel: "gpt-5.5",
      keySaved: false
    },
    {
      id: "zenmux",
      name: "ZenMux",
      docs: "https://zenmux.ai/models?sort=newest&keyword=gpt",
      endpoint: "按控制台 API 文档填写",
      models: fixedModelOptions,
      selectedModel: "gpt-5.5",
      keySaved: false
    }
  ],
  apiProfiles: [
    {
      id: "deepwl-claude-messages",
      platformId: "deepwl",
      platform: "DeepWL",
      name: "Claude Messages",
      protocol: "anthropic_messages",
      docs: "https://doc.deepwl.cn/zh/texts/claude-messages",
      endpoint: "https://zx1.deepwl.net/v1/messages",
      method: "POST",
      auth: "x-api-key",
      headers: {
        "anthropic-version": "2023-06-01"
      },
      models: fixedModelOptions,
      selectedModel: "claude-opus-4-8",
      multimodalInput: "messages[].content[] 使用 type=image，source.type=url，source.url 为图片地址",
      notes: "用于测试 Claude 原生 Messages 格式下的图像理解、OCR、多图推理和流式输出。"
    },
    {
      id: "deepwl-openai-responses",
      platformId: "deepwl",
      platform: "DeepWL",
      name: "OpenAI Responses",
      protocol: "openai_responses",
      docs: "https://doc.deepwl.cn/zh/texts/openai-responses",
      endpoint: "https://zx1.deepwl.net/v1/responses",
      method: "POST",
      auth: "Authorization: Bearer",
      headers: {},
      models: fixedModelOptions,
      selectedModel: "gpt-5.5",
      multimodalInput: "input[].content[] 使用 input_text 和 input_image，image_url 传图片地址",
      notes: "用于测试 GPT 系列 Responses API 的多模态理解、结构化输出和流式响应。"
    },
    {
      id: "antdigital-claude-messages",
      platformId: "antdigital",
      platform: "Ant Digital DTMaaS",
      name: "Claude Messages",
      protocol: "anthropic_messages",
      docs: "https://maas.antdigital.com/models",
      endpoint: "https://maas-api.antdigital.com/v1/messages",
      method: "POST",
      auth: "x-api-key",
      headers: {
        "anthropic-version": "2023-06-01"
      },
      models: fixedModelOptions,
      selectedModel: "claude-opus-4-8",
      multimodalInput: "messages[].content[] 使用 type=image，source.type=url，source.url 为图片地址",
      notes: "Ant Digital 上的 Claude Messages 接口，支持图像理解和流式输出。"
    },
    {
      id: "antdigital-openai-chat",
      platformId: "antdigital",
      platform: "Ant Digital DTMaaS",
      name: "OpenAI Chat Completions",
      protocol: "openai_chat",
      docs: "https://maas.antdigital.com/models",
      endpoint: "https://maas-api.antdigital.com/v1/chat/completions",
      method: "POST",
      auth: "Authorization: Bearer",
      headers: {},
      models: fixedModelOptions,
      selectedModel: "gpt-5.5",
      multimodalInput: "messages[].content[] 使用 type=image_url，image_url.url 传图片地址",
      notes: "Ant Digital 上的 OpenAI Chat Completions 接口，支持多模态推理与流式输出。可用模型请通过 GET /v1/models 查询。"
    }
  ],
  weights: {
    capability: 40,
    performance: 25,
    stability: 20,
    cost: 15
  },
  runner: {
    repeatCount: 3,
    concurrencyLevels: "1,2,5,10",
    timeoutSeconds: 120,
    maxTokens: 1024,
    temperature: 0.2,
    imageMode: "image_url",
    streaming: true,
    randomOrder: true,
    saveRaw: false
  },
  selectedTasks: ["vqa", "ocr", "chart", "multi-image", "video-qa", "image-gen"],
  results: []
};

const taskCatalog = [
  {
    id: "vqa",
    title: "单图视觉问答",
    visual: "image",
    description: "识别主体、数量、颜色、场景和细节，适合作为基础能力基线。",
    metrics: ["accuracy", "hallucination", "latency"]
  },
  {
    id: "ocr",
    title: "OCR 与字段抽取",
    visual: "ocr",
    description: "票据、截图、菜单和手写样本，输出结构化 JSON 字段。",
    metrics: ["CER", "field-F1", "format"]
  },
  {
    id: "chart",
    title: "图表/表格理解",
    visual: "chart",
    description: "读取柱状图、折线图和表格截图，比较数值和趋势。",
    metrics: ["numeric-error", "accuracy", "reasoning"]
  },
  {
    id: "multi-image",
    title: "多图比较",
    visual: "multi",
    description: "比较多张商品、界面或状态图，找到差异与变化原因。",
    metrics: ["diff-recall", "consistency", "latency"]
  },
  {
    id: "spatial",
    title: "空间关系推理",
    visual: "reasoning",
    description: "判断前后、遮挡、相对位置、路径和组合约束。",
    metrics: ["accuracy", "stability", "format"]
  },
  {
    id: "video-qa",
    title: "视频理解",
    visual: "video",
    description: "短视频动作识别、事件顺序、关键帧问答和摘要。",
    metrics: ["accuracy", "completion", "cost"]
  },
  {
    id: "image-gen",
    title: "图像生成",
    visual: "image",
    description: "文生图、图生图、局部编辑和文字渲染质量评估。",
    metrics: ["quality", "success-rate", "time"]
  },
  {
    id: "video-gen",
    title: "视频生成",
    visual: "video",
    description: "文生视频、首帧续写、动作连贯性和任务队列耗时。",
    metrics: ["quality", "queue-time", "success-rate"]
  },
  {
    id: "long-context",
    title: "长上下文图片组",
    visual: "multi",
    description: "5 到 20 张图综合判断，测试上下文保持和漏看率。",
    metrics: ["coverage", "consistency", "latency"]
  }
];

const storageKey = "mm-api-benchmark-state";
let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(storageKey);
    return raw ? mergeState(defaultState, JSON.parse(raw)) : structuredClone(defaultState);
  } catch {
    return structuredClone(defaultState);
  }
}

function mergeState(base, next) {
  const mergedPlatforms = (next.platforms || base.platforms).map((platform, index) =>
    normalizeFixedModelTarget({
      ...platform,
      selectedModel: fixedModelOptions.includes(platform.selectedModel)
        ? platform.selectedModel
        : base.platforms[index]?.selectedModel
    })
  );
  const mergedProfiles = (next.apiProfiles || base.apiProfiles).map((profile, index) =>
    normalizeFixedModelTarget({
      ...profile,
      selectedModel: fixedModelOptions.includes(profile.selectedModel)
        ? profile.selectedModel
        : base.apiProfiles[index]?.selectedModel
    })
  );
  return {
    ...structuredClone(base),
    ...next,
    platforms: mergedPlatforms,
    apiProfiles: mergedProfiles,
    weights: { ...base.weights, ...(next.weights || {}) },
    runner: { ...base.runner, ...(next.runner || {}) },
    selectedTasks: next.selectedTasks || base.selectedTasks,
    results: next.results || base.results
  };
}

function saveState() {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function normalizeFixedModelTarget(target) {
  const selected = fixedModelOptions.includes(target.selectedModel) ? target.selectedModel : fixedModelOptions[0];
  return {
    ...target,
    models: fixedModelOptions,
    selectedModel: selected
  };
}

function render() {
  renderPlatforms();
  renderProfiles();
  renderWeights();
  renderTasks();
  renderRunner();
  renderConfigPreview();
  renderResults();
  renderSummary();
  drawScoreChart();
}

function renderPlatforms() {
  const root = document.querySelector("#platformList");
  root.innerHTML = "";
  state.platforms.forEach((platform, index) => {
    const card = document.createElement("article");
    card.className = "platform-card";
    card.innerHTML = `
      <div class="platform-title">
        <strong>${platform.name}</strong>
        <a class="status-pill" href="${platform.docs}" target="_blank" rel="noreferrer">文档</a>
      </div>
      <label>
        <span>Base URL</span>
        <input value="${escapeHtml(platform.endpoint)}" data-platform-field="endpoint" data-platform-index="${index}" />
      </label>
      <label>
        <span>API Key 状态</span>
        <input type="password" placeholder="仅保存在浏览器本地，不导出" data-platform-field="apiKey" data-platform-index="${index}" />
      </label>
      <label>
        <span>默认模型</span>
        <select data-platform-field="selectedModel" data-platform-index="${index}">
          ${platform.models.map((model) => `<option value="${escapeHtml(model)}" ${selectedPlatformModel(platform) === model ? "selected" : ""}>${escapeHtml(modelDisplayName(model))}</option>`).join("")}
        </select>
      </label>
      <div class="chip-row">
        ${platform.models.slice(0, 4).map((model) => `<span class="chip">${escapeHtml(modelDisplayName(model))}</span>`).join("")}
      </div>
    `;
    root.appendChild(card);
  });
}

function renderProfiles() {
  const root = document.querySelector("#profileList");
  if (!root) return;
  root.innerHTML = "";
  state.apiProfiles.forEach((profile, index) => {
    const card = document.createElement("article");
    card.className = "profile-card";
    card.innerHTML = `
      <div class="profile-card-head">
        <div>
          <p class="eyebrow">${escapeHtml(profile.platform)} · ${escapeHtml(profile.protocol)}</p>
          <h3>${escapeHtml(profile.name)}</h3>
        </div>
        <a class="status-pill" href="${profile.docs}" target="_blank" rel="noreferrer">文档</a>
      </div>
      <div class="profile-meta">
        <span>${escapeHtml(profile.method)}</span>
        <code>${escapeHtml(profile.endpoint)}</code>
      </div>
      <div class="profile-fields">
        <label>
          <span>Endpoint</span>
          <input value="${escapeHtml(profile.endpoint)}" data-profile-field="endpoint" data-profile-index="${index}" />
        </label>
        <label>
          <span>选择模型</span>
          <select data-profile-field="selectedModel" data-profile-index="${index}">
            ${profile.models.map((model) => `<option value="${escapeHtml(model)}" ${selectedModel(profile) === model ? "selected" : ""}>${escapeHtml(modelDisplayName(model))}</option>`).join("")}
          </select>
        </label>
      </div>
      <p>${escapeHtml(profile.multimodalInput)}</p>
      <p class="muted">${escapeHtml(profile.notes)}</p>
      <div class="chip-row">
        <span class="chip">${escapeHtml(profile.auth)}</span>
        ${Object.entries(profile.headers).map(([key, value]) => `<span class="chip">${escapeHtml(key)}: ${escapeHtml(value)}</span>`).join("")}
        ${profile.models.map((model) => `<span class="chip ${selectedModel(profile) === model ? "chip-selected" : ""}">${escapeHtml(modelDisplayName(model))}</span>`).join("")}
      </div>
    `;
    root.appendChild(card);
  });
}

function renderWeights() {
  Object.entries(state.weights).forEach(([key, value]) => {
    const input = document.querySelector(`[data-weight="${key}"]`);
    const label = document.querySelector(`#${key}Value`);
    if (input) input.value = value;
    if (label) label.textContent = value;
  });
  const total = Object.values(state.weights).reduce((sum, value) => sum + Number(value), 0);
  document.querySelector("#weightTotal").textContent = `${total}%`;
  document.querySelector("#weightTotal").style.color = total === 100 ? "var(--muted)" : "var(--red)";
}

function renderTasks() {
  const root = document.querySelector("#taskSuite");
  root.innerHTML = "";
  taskCatalog.forEach((task) => {
    const checked = state.selectedTasks.includes(task.id);
    const card = document.createElement("article");
    card.className = "task-card";
    card.innerHTML = `
      <div class="task-visual ${task.visual}" aria-hidden="true"></div>
      <div class="task-body">
        <div class="task-title">
          <h3>${task.title}</h3>
          <label class="switch" title="启用任务">
            <input type="checkbox" data-task="${task.id}" ${checked ? "checked" : ""} />
            <span></span>
          </label>
        </div>
        <p>${task.description}</p>
        <div class="task-metrics">
          ${task.metrics.map((metric) => `<span class="chip">${metric}</span>`).join("")}
        </div>
      </div>
    `;
    root.appendChild(card);
  });
}

function renderRunner() {
  Object.entries(state.runner).forEach(([key, value]) => {
    const input = document.querySelector(`#${key}`);
    if (!input) return;
    if (input.type === "checkbox") {
      input.checked = Boolean(value);
    } else {
      input.value = value;
    }
  });
}

function currentConfig() {
  const totalWeight = Object.values(state.weights).reduce((sum, value) => sum + Number(value), 0);
  return {
    benchmark_name: "multimodal_api_platform_benchmark",
    generated_at: new Date().toISOString(),
    platforms: state.platforms.map((platform) => ({
      id: platform.id,
      name: platform.name,
      docs: platform.docs,
      endpoint: platform.endpoint,
      model: selectedPlatformModel(platform),
      model_options: platform.models
    })),
    api_profiles: state.apiProfiles.map((profile) => ({
      id: profile.id,
      platform: profile.platform,
      name: profile.name,
      protocol: profile.protocol,
      docs: profile.docs,
      endpoint: profile.endpoint,
      method: profile.method,
      auth: profile.auth,
      headers: profile.headers,
      model: selectedModel(profile),
      model_options: profile.models,
      multimodal_input: profile.multimodalInput,
      notes: profile.notes
    })),
    tasks: taskCatalog
      .filter((task) => state.selectedTasks.includes(task.id))
      .map(({ id, title, metrics }) => ({ id, title, metrics })),
    runner: {
      ...state.runner,
      concurrencyLevels: parseConcurrency(state.runner.concurrencyLevels)
    },
    scoring_weights: {
      ...state.weights,
      normalized: normalizeWeights(state.weights),
      total: totalWeight
    },
    // Keep in sync with DEFAULT_OUTPUT_SCHEMA in runner/config.py
    output_schema: [
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
      "total_score"
    ]
  };
}

function renderConfigPreview() {
  document.querySelector("#configPreview").textContent = JSON.stringify(currentConfig(), null, 2);
}

function renderSummary() {
  const modelCount = state.apiProfiles.length;
  const taskCount = state.selectedTasks.length;
  const levels = parseConcurrency(state.runner.concurrencyLevels);
  const requestCount = modelCount * taskCount * Number(state.runner.repeatCount || 0) * Math.max(levels.length, 1);
  document.querySelector("#platformCount").textContent = state.apiProfiles.length;
  document.querySelector("#modelCount").textContent = modelCount;
  document.querySelector("#taskCount").textContent = taskCount;
  document.querySelector("#requestCount").textContent = requestCount;
}

function renderResults() {
  const filter = document.querySelector("#tableFilter").value.trim().toLowerCase();
  const root = document.querySelector("#resultRows");
  const rows = state.results.filter((row) => {
    const text = `${row.platform} ${row.profile} ${row.model} ${row.task}`.toLowerCase();
    return !filter || text.includes(filter);
  });

  if (!rows.length) {
    root.innerHTML = `
      <tr>
        <td colspan="10" class="muted">暂无结果。点击“生成样例结果”预览报表结构。</td>
      </tr>
    `;
    return;
  }

  root.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${row.platform}</td>
          <td>${row.profile}</td>
          <td>${row.model}</td>
          <td>${row.task}</td>
          <td>${row.capability.toFixed(1)}</td>
          <td>${row.p95Latency} ms</td>
          <td>${row.ttft} ms</td>
          <td>${row.successRate.toFixed(1)}%</td>
          <td>$${row.cost.toFixed(4)}</td>
          <td class="score">${row.total.toFixed(1)}</td>
        </tr>
      `
    )
    .join("");
}

function drawScoreChart() {
  const canvas = document.querySelector("#scoreChart");
  const ctx = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(720, Math.round(rect.width));
  const height = Math.max(380, Math.round(rect.height));
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, width, height);

  const summary = summarizeByPlatform();
  const labels = state.apiProfiles.map((profile) => profile.name);
  const values = labels.map((label) => summary[label]?.total || 0);
  const max = Math.max(100, ...values);
  const left = 60;
  const right = 26;
  const top = 38;
  const bottom = 92;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const colors = ["#247a52", "#356797", "#ad6816", "#2b8057"];

  ctx.strokeStyle = "#d9e1da";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#65716b";
  ctx.font = "16px system-ui";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let i = 0; i <= 5; i += 1) {
    const y = top + chartHeight - (chartHeight * i) / 5;
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(width - right, y);
    ctx.stroke();
    ctx.fillText(String(Math.round((max * i) / 5)), left - 18, y);
  }

  ctx.strokeStyle = "#eef2ee";
  ctx.beginPath();
  ctx.moveTo(left, top + chartHeight);
  ctx.lineTo(width - right, top + chartHeight);
  ctx.stroke();

  const slotWidth = chartWidth / Math.max(labels.length, 1);
  const barWidth = Math.min(168, slotWidth * 0.58);
  labels.forEach((label, index) => {
    const x = left + index * slotWidth + (slotWidth - barWidth) / 2;
    const value = values[index];
    const barHeight = (value / max) * chartHeight;
    const y = top + chartHeight - barHeight;
    ctx.fillStyle = colors[index % colors.length];
    roundedRect(ctx, x, y, barWidth, barHeight, 3);
    ctx.fill();
    ctx.fillStyle = "#1c241f";
    ctx.font = "700 26px system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText(value ? value.toFixed(1) : "待测", x + barWidth / 2, y - 16);
    ctx.fillStyle = "#26302a";
    ctx.font = "600 17px system-ui";
    wrapCanvasText(ctx, label, x + barWidth / 2, height - 62, Math.max(barWidth + 34, slotWidth - 30), 22);
  });
}

function roundedRect(ctx, x, y, width, height, radius) {
  const safeRadius = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + safeRadius, y);
  ctx.lineTo(x + width - safeRadius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + safeRadius);
  ctx.lineTo(x + width, y + height);
  ctx.lineTo(x, y + height);
  ctx.lineTo(x, y + safeRadius);
  ctx.quadraticCurveTo(x, y, x + safeRadius, y);
  ctx.closePath();
}

function summarizeByPlatform() {
  const summary = {};
  state.results.forEach((row) => {
    if (!summary[row.profile]) {
      summary[row.profile] = { count: 0, total: 0 };
    }
    summary[row.profile].count += 1;
    summary[row.profile].total += row.total;
  });
  Object.values(summary).forEach((item) => {
    item.total = item.total / item.count;
  });
  return summary;
}

function generateMockResults() {
  const selectedTasks = taskCatalog.filter((task) => state.selectedTasks.includes(task.id));
  const rows = [];
  state.apiProfiles.forEach((profile, profileIndex) => {
    [selectedModel(profile)].forEach((model, modelIndex) => {
      selectedTasks.forEach((task, taskIndex) => {
        const seed = profileIndex * 19 + modelIndex * 11 + taskIndex * 7 + model.length;
        const capability = clamp(68 + ((seed * 13) % 24) + modelBias(model), 45, 98);
        const p95Latency = Math.round(clamp(1100 + ((seed * 397) % 5200) - speedBias(profile.platformId), 520, 9000));
        const ttft = Math.round(clamp(p95Latency * (0.18 + ((seed % 5) * 0.035)), 180, 2800));
        const successRate = clamp(92 + ((seed * 3) % 7) - failureBias(task.id), 80, 99.9);
        const cost = clamp(0.0018 + ((seed % 13) * 0.0011) + costBias(model, task.id), 0.0008, 0.08);
        const total = scoreRow({ capability, p95Latency, successRate, cost });
        rows.push({
          platform: profile.platform,
          profile: profile.name,
          model,
          task: task.title,
          capability,
          p95Latency,
          ttft,
          successRate,
          cost,
          total
        });
      });
    });
  });
  state.results = rows.sort((a, b) => b.total - a.total);
  saveState();
  render();
  showToast("已生成离线样例结果，可用于预览报表和导出 CSV。");
}

function scoreRow(row) {
  const weights = normalizeWeights(state.weights);
  const performance = clamp(100 - (row.p95Latency - 800) / 75, 20, 100);
  const stability = row.successRate;
  const cost = clamp(100 - row.cost * 1300, 20, 100);
  return (
    row.capability * weights.capability +
    performance * weights.performance +
    stability * weights.stability +
    cost * weights.cost
  );
}

function normalizeWeights(weights) {
  const total = Object.values(weights).reduce((sum, value) => sum + Number(value), 0) || 1;
  return Object.fromEntries(Object.entries(weights).map(([key, value]) => [key, Number(value) / total]));
}

function selectedModel(profile) {
  return profile.selectedModel && profile.models.includes(profile.selectedModel)
    ? profile.selectedModel
    : profile.models[0] || "";
}

function selectedPlatformModel(platform) {
  return platform.selectedModel && platform.models.includes(platform.selectedModel)
    ? platform.selectedModel
    : platform.models[0] || "";
}

function modelDisplayName(model) {
  return {
    "claude-opus-4-8": "Claude Opus 4.8",
    "gpt-5.5": "GPT-5.5"
  }[model] || model;
}

function parseConcurrency(value) {
  return String(value)
    .split(",")
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isFinite(item) && item > 0);
}

function download(filename, body, type) {
  const blob = new Blob([body], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportCsv() {
  const header = ["platform", "profile", "model", "task", "capability", "p95_latency_ms", "ttft_ms", "success_rate", "cost", "total_score"];
  const rows = state.results.map((row) =>
    [row.platform, row.profile, row.model, row.task, row.capability.toFixed(2), row.p95Latency, row.ttft, row.successRate.toFixed(2), row.cost.toFixed(4), row.total.toFixed(2)]
      .map((value) => `"${String(value).replaceAll('"', '""')}"`)
      .join(",")
  );
  download("multimodal-api-benchmark-results.csv", [header.join(","), ...rows].join("\n"), "text/csv;charset=utf-8");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(" ");
  let line = "";
  ctx.textAlign = "center";
  words.forEach((word, index) => {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, y);
      line = word;
      y += lineHeight;
    } else {
      line = test;
    }
    if (index === words.length - 1) {
      ctx.fillText(line, x, y);
    }
  });
}

function modelBias(model) {
  if (/mini|nano|flash/i.test(model)) return -6;
  if (/pro|sonnet|4o|4\.1/i.test(model)) return 5;
  return 0;
}

function speedBias(platformId) {
  return { deepwl: 340, antdigital: 120, zenmux: 260 }[platformId] || 0;
}

function failureBias(taskId) {
  return { "video-gen": 5.6, "image-gen": 2.8, "video-qa": 2.2, "long-context": 1.5 }[taskId] || 0;
}

function costBias(model, taskId) {
  const modelExtra = /pro|sonnet|4o|4\.1/i.test(model) ? 0.006 : 0.0015;
  const taskExtra = /video|image-gen/.test(taskId) ? 0.012 : 0;
  return modelExtra + taskExtra;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

document.addEventListener("input", (event) => {
  const weight = event.target.dataset.weight;
  if (weight) {
    state.weights[weight] = Number(event.target.value);
    saveState();
    renderWeights();
    renderConfigPreview();
    drawScoreChart();
  }

  const platformField = event.target.dataset.platformField;
  if (platformField) {
    const index = Number(event.target.dataset.platformIndex);
    if (platformField === "models") {
      state.platforms[index].models = event.target.value
        .split(",")
        .map((model) => model.trim())
        .filter(Boolean);
    } else if (platformField === "apiKey") {
      state.platforms[index].keySaved = Boolean(event.target.value);
      sessionStorage.setItem(`api-key-${state.platforms[index].id}`, event.target.value);
    } else {
      state.platforms[index][platformField] = event.target.value;
    }
    saveState();
    renderConfigPreview();
    renderSummary();
  }

  const profileField = event.target.dataset.profileField;
  if (profileField) {
    const index = Number(event.target.dataset.profileIndex);
    if (profileField === "models") {
      state.apiProfiles[index].models = event.target.value
        .split(",")
        .map((model) => model.trim())
        .filter(Boolean);
    } else {
      state.apiProfiles[index][profileField] = event.target.value;
    }
    saveState();
    renderConfigPreview();
    renderSummary();
  }

  if (event.target.id in state.runner) {
    const input = event.target;
    state.runner[input.id] = input.type === "checkbox" ? input.checked : input.value;
    saveState();
    renderConfigPreview();
    renderSummary();
  }

  if (event.target.id === "tableFilter") {
    renderResults();
  }
});

document.addEventListener("change", (event) => {
  const platformField = event.target.dataset.platformField;
  if (platformField) {
    const index = Number(event.target.dataset.platformIndex);
    state.platforms[index][platformField] = event.target.value;
    saveState();
    renderConfigPreview();
    renderSummary();
  }

  const profileField = event.target.dataset.profileField;
  if (profileField) {
    const index = Number(event.target.dataset.profileIndex);
    state.apiProfiles[index][profileField] = event.target.value;
    saveState();
    renderConfigPreview();
    renderSummary();
  }

  const task = event.target.dataset.task;
  if (task) {
    if (event.target.checked) {
      state.selectedTasks = [...new Set([...state.selectedTasks, task])];
    } else {
      state.selectedTasks = state.selectedTasks.filter((id) => id !== task);
    }
    saveState();
    renderConfigPreview();
    renderSummary();
  }
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.tab}`).classList.add("active");
  });
});

document.querySelector("#runMock").addEventListener("click", generateMockResults);
document.querySelector("#exportJson").addEventListener("click", () => {
  download("multimodal-api-benchmark-config.json", JSON.stringify(currentConfig(), null, 2), "application/json;charset=utf-8");
});
document.querySelector("#exportCsv").addEventListener("click", exportCsv);
document.querySelector("#copyConfig").addEventListener("click", async () => {
  await navigator.clipboard.writeText(JSON.stringify(currentConfig(), null, 2));
  showToast("Runner 配置已复制。");
});
document.querySelector("#resetConfig").addEventListener("click", () => {
  state = structuredClone(defaultState);
  localStorage.removeItem(storageKey);
  render();
  showToast("已恢复默认配置。");
});
window.addEventListener("resize", () => {
  window.clearTimeout(window.__scoreChartResizeTimer);
  window.__scoreChartResizeTimer = window.setTimeout(drawScoreChart, 120);
});

render();
