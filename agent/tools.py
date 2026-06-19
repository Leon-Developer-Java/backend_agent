"""工具定义与分发。

- query_weather_data / make_chart：本地内置工具。
- 6 个模型工具：从 services.models 注册表自动生成（开发者只改自己的模型文件）。

返回结构统一带 "status"：ok / need_params / error，供 llm 层转成事件。
"""
from __future__ import annotations

import json
from typing import Any

from services import data_query, models
from services.plotting import line_chart


# ── 本地工具实现 ────────────────────────────────────────────────────────

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


def _make_chart(title: str, series: Any = None, x: list | None = None) -> dict:
    parsed: dict | None = None
    if isinstance(series, str) and series.strip():
        try:
            parsed = json.loads(series)
        except json.JSONDecodeError:
            parsed = None
    elif isinstance(series, dict):
        parsed = series
    url = line_chart(title or "气象图表", parsed, x)
    return {"summary": f"已生成图表：{title or '气象图表'}。", "image_url": url}


_LOCAL_DISPATCH = {
    "query_weather_data": _query_weather_data,
    "make_chart": _make_chart,
}
_LOCAL_LABELS = {
    "query_weather_data": "查询数据中",
    "make_chart": "生成图表中",
}


def label_for(name: str) -> str:
    """工具卡进度文案。"""
    return _LOCAL_LABELS.get(name) or models.label_for(name)


def dispatch(name: str, args: dict[str, Any]) -> dict:
    """执行工具，返回带 status 的统一结构。"""
    try:
        fn = _LOCAL_DISPATCH.get(name)
        if fn is not None:
            res = fn(**(args or {}))
            res.setdefault("status", "ok")
            return res
        # 其余视为模型工具，交给注册表（含必填校验/缺参提示）
        return models.run_model(name, args or {})
    except Exception as exc:  # 工具内部异常不应中断对话
        return {"status": "error", "summary": f"工具 {name} 执行出错：{exc}", "image_url": None}


# ── 工具 schema：内置两个 + 6 个模型（自动生成）────────────────────────

_BASE_SCHEMAS: list[dict[str, Any]] = [
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
            "name": "make_chart",
            "description": "把时序数据画成折线图并展示。用户要求生成图表/画图/可视化且无需跑模型时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "图表标题"},
                    "series": {"type": "string",
                               "description": "可选，JSON 字符串，形如 {\"气温\":[21,22,...]}；不填用示例数据"},
                },
                "required": ["title"],
            },
        },
    },
]

TOOL_SCHEMAS: list[dict[str, Any]] = _BASE_SCHEMAS + models.build_tool_schemas()
