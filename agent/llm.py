"""DeepSeek（OpenAI 兼容）对话与工具调用循环，产出 NDJSON 事件流。

事件类型：text / tool / image / done / error。
run_chat 是同步生成器，供 FastAPI StreamingResponse 使用。
无可用密钥时降级为基于关键词的本地路由，保证协议可联调。
"""
from __future__ import annotations

import json
from typing import Any, Iterator

from openai import OpenAI

from agent import tools
from agent.prompts import SYSTEM_PROMPT
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_REASONING_EFFORT,
    DEEPSEEK_THINKING,
    has_llm,
)

MAX_ROUNDS = 4  # 工具调用最多往返轮数，防止死循环

_client: OpenAI | None = None


def _client_lazy() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _client


def _create_kwargs() -> dict[str, Any]:
    """推理模型（v4-pro）按官方样例启用 thinking；flash 可关闭以提速。"""
    kwargs: dict[str, Any] = {}
    if DEEPSEEK_THINKING == "enabled":
        kwargs["reasoning_effort"] = DEEPSEEK_REASONING_EFFORT
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
    return kwargs


def run_chat(history: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """主入口：根据是否配置密钥选择真实 LLM 或降级路由。"""
    try:
        if has_llm():
            yield from _run_with_llm(history)
        else:
            yield from _run_fallback(history)
    except Exception as exc:  # 兜底，避免连接异常导致前端流挂死
        yield {"type": "error", "message": f"智能体处理出错：{exc}"}
    yield {"type": "done"}


# ── 真实 LLM 路径 ───────────────────────────────────────────────────────

def _run_with_llm(history: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    client = _client_lazy()
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m["role"], "content": m.get("content", "")} for m in history]

    for _ in range(MAX_ROUNDS):
        stream = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            tools=tools.TOOL_SCHEMAS,
            stream=True,
            **_create_kwargs(),
        )

        text_buf = ""
        tool_acc: dict[int, dict[str, str]] = {}  # index -> {id,name,arguments}
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # 推理模型的思维链走 reasoning_content，前端不展示，仅取最终 content
            if delta.content:
                text_buf += delta.content
                yield {"type": "text", "value": delta.content}
            for tc in (delta.tool_calls or []):
                slot = tool_acc.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    slot["arguments"] += tc.function.arguments

        if not tool_acc:
            return  # 模型已给出最终回答（文本已流出）

        # 回填本轮 assistant（含 tool_calls），再逐个执行工具
        assistant_tool_calls = [
            {"id": s["id"] or f"call_{i}", "type": "function",
             "function": {"name": s["name"], "arguments": s["arguments"] or "{}"}}
            for i, s in sorted(tool_acc.items())
        ]
        messages.append({"role": "assistant", "content": text_buf or None,
                         "tool_calls": assistant_tool_calls})

        for call in assistant_tool_calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            stop = yield from _exec_tool(call["id"], name, args, messages)
            if stop:
                return  # 缺参：交回用户补全，结束本轮

    yield {"type": "text", "value": "\n（已达到工具调用上限，先汇报到这里。）"}


# ── 工具执行 + 事件 ─────────────────────────────────────────────────────

def _exec_tool(call_id: str, name: str, args: dict[str, Any],
               messages: list[dict[str, Any]]):
    """执行单个工具并产出事件。返回 True 表示需要停止本轮（缺参，等用户补全）。"""
    label = tools.label_for(name)
    yield {"type": "tool", "name": name, "status": "running", "label": label, "progress": 30}

    result = tools.dispatch(name, args)

    # 缺参：发结构化补全卡，并以文本说明，结束本轮
    if result.get("status") == "need_params":
        yield {"type": "tool", "name": name, "status": "done", "progress": 100, "result": "待补充参数"}
        yield {"type": "need_params", "model": result["model"],
               "model_name": result["model_name"], "fields": result["missing"],
               "prompt": result["summary"]}
        yield {"type": "text", "value": result["summary"]}
        return True

    summary = result.get("summary", "")
    image_url = result.get("image_url")
    if image_url:
        yield {"type": "image", "url": image_url, "caption": label}
    yield {"type": "tool", "name": name, "status": "done", "progress": 100,
           "result": summary[:60] + ("…" if len(summary) > 60 else "")}

    # 工具结果回填给模型，让其用自然语言总结
    messages.append({"role": "tool", "tool_call_id": call_id, "name": name,
                     "content": json.dumps({"summary": summary, "image_url": image_url},
                                           ensure_ascii=False)})
    return False


# ── 降级路径（无密钥时的本地关键词路由）────────────────────────────────

def _run_fallback(history: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    user_text = ""
    for m in reversed(history):
        if m.get("role") == "user":
            user_text = m.get("content", "")
            break
    t = user_text.lower()

    yield {"type": "text",
           "value": "（提示：未配置 DeepSeek 密钥，当前为本地降级模式，按关键词调用工具。）\n\n"}

    if any(k in user_text for k in ("预测", "外推", "跑模型", "调用模型", "分析", "诊断")) or "model" in t:
        model_id = ("model_radar" if ("雷达" in user_text or "外推" in user_text)
                    else "model_himawari" if ("葵花" in user_text or "云图" in user_text)
                    else "model_cma" if "cma" in t
                    else "model_gfs" if ("gfs" in t or "ecmwf" in t)
                    else "model_era5" if "era5" in t
                    else "model_wrf")
        args: dict[str, Any] = {}
        region = next((r for r in ("华北", "华东", "华南", "西南", "西北", "东北", "全国") if r in user_text), None)
        if region:
            args["region"] = region
        yield from _fallback_tool(model_id, args)
    elif any(k in user_text for k in ("图表", "画图", "出图", "可视化", "折线")):
        yield from _fallback_tool("make_chart", {"title": user_text[:16] or "气象图表"})
    else:
        yield from _fallback_tool("query_weather_data", {})


def _fallback_tool(name: str, args: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """降级模式：触发工具事件；缺参则发补全卡，否则把 summary 作为文本流出。"""
    label = tools.label_for(name)
    yield {"type": "tool", "name": name, "status": "running", "label": label, "progress": 30}
    result = tools.dispatch(name, args)

    if result.get("status") == "need_params":
        yield {"type": "tool", "name": name, "status": "done", "progress": 100, "result": "待补充参数"}
        yield {"type": "need_params", "model": result["model"],
               "model_name": result["model_name"], "fields": result["missing"],
               "prompt": result["summary"]}
        yield {"type": "text", "value": result["summary"]}
        return

    if result.get("image_url"):
        yield {"type": "image", "url": result["image_url"], "caption": label}
    yield {"type": "tool", "name": name, "status": "done", "progress": 100, "result": "已完成"}
    yield {"type": "text", "value": result.get("summary", "")}
