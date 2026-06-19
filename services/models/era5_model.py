"""成员1 · ERA5 要素场分析（测试模型，逻辑为占位）。"""
from services.plotting import line_chart

REGIONS = ["华北", "华东", "华南", "西南", "西北", "东北", "全国"]

SPEC = {
    "id": "model_era5",
    "name": "ERA5 要素场分析",
    "data_type": "ERA5",
    "description": "查询并分析 ERA5 再分析数据的指定气象要素，输出统计与逐时变化曲线。",
    "params": [
        {"name": "variable", "label": "气象要素", "type": "select", "required": True,
         "options": ["2m气温", "海平面气压", "10m风速", "总降水"]},
        {"name": "region", "label": "区域", "type": "select", "required": True, "options": REGIONS},
        {"name": "time", "label": "时间", "type": "text", "required": False,
         "default": "今天", "placeholder": "如 今天 / 2025-06-18"},
    ],
    "output": "要素统计（最大/最小/平均）+ 逐时变化折线图。",
}

_SERIES = {
    "2m气温": [21, 22, 24, 27, 30, 29, 26, 23],
    "海平面气压": [1009, 1008, 1007, 1006, 1004, 1005, 1007, 1008],
    "10m风速": [3.1, 3.8, 4.5, 5.2, 6.1, 5.6, 4.8, 3.9],
    "总降水": [0, 0.2, 0.8, 1.6, 2.4, 1.2, 0.4, 0.1],
}


def run(params: dict) -> dict:
    v, region, time = params.get("variable"), params.get("region"), params.get("time")
    data = _SERIES.get(v, [0] * 8)
    image_url = line_chart(f"ERA5 {region} {v}（{time}）", {v: data})
    summary = (f"ERA5 再分析：{time}{region}的「{v}」——"
               f"最大 {max(data)}，最小 {min(data)}，平均 {round(sum(data) / len(data), 1)}。")
    return {"summary": summary, "image_url": image_url, "data": {"series": data}}
