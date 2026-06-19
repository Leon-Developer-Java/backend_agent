"""工具定义（OpenAI function-calling schema）与分发表。

每个工具返回 {"summary": str, "image_url": str|None}，便于 llm 层统一转成
text / image 事件。
"""
from __future__ import annotations

import json
from typing import Any, Callable

from services import data_query, models
from services.plotting import line_chart

# ── 工具实现 ────────────────────────────────────────────────────────────

def _query_weather_data(data_type: str | None = None, variable: str | None = None) -> dict:
    result = data_query.list_datasets(data_type)
    datasets = result["datasets"]
    if variable:
        datasets = [d for d in datasets
                    if any(variable in str(v) for v in d.get("variables", []))]

    if not datasets:
        return {"summary": "未找到匹配的数据集。", "image_url": None}

    lines = []
    for d in datasets:
        lines.append(
            f"- {d.get('title') or d['data_type']}（{d['data_type']}）："
            f"变量 {('、'.join(map(str, d.get('variables', []))) or '—')}；"
            f"{d.get('times', 0)} 个时次；已有图像 {d.get('png_count', 0)} 张"
        )
    head = "当前共 %d 个数据集" % len(datasets)
    if result.get("using_sample"):
        head += "（注：解析后端暂无真实数据，以下为示例清单）"
    return {"summary": head + "：\n" + "\n".join(lines), "image_url": None}


def _run_model(model: str, region: str | None = None, time: str | None = None) -> dict:
    return models.run_model(model=model, region=region, time=time)


def _make_chart(title: str, series: Any = None, x: list | None = None) -> dict:
    parsed: dict[str, list[float]] | None = None
    if isinstance(series, str) and series.strip():
        try:
            parsed = json.loads(series)
        except json.JSONDecodeError:
            parsed = None
    elif isinstance(series, dict):
        parsed = series
    url = line_chart(title or "气象图表", parsed, x)
    return {"summary": f"已生成图表：{title or '气象图表'}。", "image_url": url}


# ── 分发表与进度文案 ────────────────────────────────────────────────────

DISPATCH: dict[str, Callable[..., dict]] = {
    "query_weather_data": _query_weather_data,
    "run_model": _run_model,
    "make_chart": _make_chart,
}

# 工具卡上展示的中文进度文案
LABELS = {
    "query_weather_data": "查询数据中",
    "run_model": "模型计算中",
    "make_chart": "生成图表中",
}


def dispatch(name: str, args: dict[str, Any]) -> dict:
    fn = DISPATCH.get(name)
    if fn is None:
        return {"summary": f"未知工具：{name}", "image_url": None}
    try:
        return fn(**(args or {}))
    except Exception as exc:  # 工具内部异常不应中断对话
        return {"summary": f"工具 {name} 执行出错：{exc}", "image_url": None}


# ── OpenAI tools schema ─────────────────────────────────────────────────

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "query_weather_data",
            "description": "查询当前已解析的气象数据集、变量、时次与已有图像。用户询问有哪些数据、"
                           "某要素是否存在、数据情况时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "data_type": {"type": "string",
                                  "description": "可选，按业务类型过滤，如 ERA5/GFS/Radar/WRF/Himawari/CMA"},
                    "variable": {"type": "string", "description": "可选，按气象要素名过滤，如 温度、降水"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_model",
            "description": "调用气象预测模型并生成预测示意图。用户要求预测/外推/分析/跑模型时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "enum": ["wrf", "radar_ext", "era5", "himawari"],
                              "description": "模型：wrf 短临降水、radar_ext 雷达回波外推、era5 场分析、himawari 葵花云图"},
                    "region": {"type": "string", "description": "可选，目标区域，如 华北、长三角"},
                    "time": {"type": "string", "description": "可选，时间，如 今天、未来6小时"},
                },
                "required": ["model"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_chart",
            "description": "把时序数据画成折线图并展示。用户要求生成图表/画图/可视化且无需跑模型时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "图表标题"},
                    "series": {"type": "string",
                               "description": "可选，JSON 字符串，形如 {\"气温(℃)\":[21,22,...]}；不填用示例数据"},
                },
                "required": ["title"],
            },
        },
    },
]
