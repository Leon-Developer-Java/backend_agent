# backend_agent · 智能体后端

「智慧气象」系统智能体页面（`webpage_sys` 的 `Agent.vue`）的后端：用户用自然语言对话，
智能体（大脑用 DeepSeek，OpenAI 兼容接口）通过**工具调用**完成数据查询、模型调用与图像生成。

## 启动

```bash
cd backend_agent
python -m venv .venv
# Windows: .venv\Scripts\activate    其它: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # 然后填入 DeepSeek 密钥
python main.py         # 监听 http://127.0.0.1:8004
```

> 未配置密钥也能启动：进入**本地降级模式**（按关键词路由工具），用于先联调协议。

## DeepSeek 配置（`.env`）

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | 你的密钥 |
| `DEEPSEEK_BASE_URL` | 默认 `https://api.deepseek.com/v1`；用代理/聚合站则填对应地址 |
| `DEEPSEEK_MODEL` | 确切 model id（官方公开：`deepseek-chat`/`deepseek-reasoner`），**须支持 function calling** |
| `PUBLIC_BASE_URL` | 生成图片对外基址，默认 `http://127.0.0.1:8004` |

## 接口

### `POST /api/agent/chat` —— NDJSON 流式
请求体：`{ "messages": [{"role","content"}], "context": {} }`
响应：`application/x-ndjson`，每行一个 JSON 事件：

| 事件 | 形状 |
|------|------|
| 文本增量 | `{"type":"text","value":"…"}` |
| 工具进行/完成 | `{"type":"tool","name":"model_wrf","status":"running|done","label":"…","progress":30,"result":"…"}` |
| 缺参补全 | `{"type":"need_params","model":"model_wrf","model_name":"…","fields":[…],"prompt":"…"}` |
| 图片 | `{"type":"image","url":"http://127.0.0.1:8004/outputs/x.png","caption":"…"}` |
| 结束 | `{"type":"done"}` |
| 错误 | `{"type":"error","message":"…"}` |

### `GET /api/health`
返回 `{code,data:{status,llm_ready,model,...}}`。

### `/outputs/<file>.png`
静态托管运行期生成的图像。

## 工具（MVP）

- `query_weather_data(data_type?, variable?)`：扫描解析后端 `../backend/data/*/*.meta.json`；为空时返回示例清单。
- `make_chart(title, series?)`：matplotlib 折线图 → PNG。
- **6 个气象模型**（测试用占位逻辑）：`model_era5` / `model_gfs` / `model_cma` / `model_radar` /
  `model_himawari` / `model_wrf`，每个返回结论文字 + 示意图。工具由 `services/models/` 下的 `SPEC`
  自动生成，多人协作只改各自的模型文件，详见 [services/models/README.md](services/models/README.md)。

### 模型参数补全流程

模型工具的参数**不在 schema 里标 required**，因此大模型即使信息不全也会先调用，由注册表
校验必填项：

- 参数齐全 → 直接执行，流式返回 `tool` + `image` + 结论文本。
- 缺必填参数 → 返回 `need_params` 事件（含字段与可选项），前端弹「选择/输入」卡片；用户补全后
  作为新消息发回，大模型据上下文重新调用，直到参数齐全出结果。

`need_params` 事件形状：
```json
{"type":"need_params","model":"model_wrf","model_name":"WRF 短临降水预测",
 "fields":[{"name":"region","label":"区域","type":"select","options":["华北","华东",...],"required":true}],
 "prompt":"调用【WRF 短临降水预测】还需要补充参数：区域。"}
```

## 自测（无需前端）

```bash
curl -N -X POST http://127.0.0.1:8004/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"用WRF预测华北今天降水并出图"}],"context":{}}'
```
应看到逐行 NDJSON：text → tool(running→done) → image → done。

## 范围

MVP：流式对话、DeepSeek 工具调用循环、数据查询、模型桩、PNG 生成与托管。
非目标：真实模型接入、服务端会话持久化、鉴权（后续迭代）。
