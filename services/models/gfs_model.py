"""成员2 · GFS/ECMWF 数值预报（测试模型，逻辑为占位）。"""
from services.plotting import line_chart

REGIONS = ["华北", "华东", "华南", "西南", "西北", "东北", "全国"]

SPEC = {
    "id": "model_gfs",
    "name": "GFS/ECMWF 数值预报",
    "data_type": "GFS",
    "description": "基于 GFS/ECMWF 全球数值预报，预测指定区域要素的未来演变。",
    "params": [
        {"name": "variable", "label": "预报要素", "type": "select", "required": True,
         "options": ["500hPa位势高度", "2m气温", "降水", "10m风"]},
        {"name": "region", "label": "区域", "type": "select", "required": True, "options": REGIONS},
        {"name": "lead_hours", "label": "预报时效(小时)", "type": "select", "required": False,
         "options": ["24", "48", "72", "120"], "default": "24"},
    ],
    "output": "预报结论 + 要素时序折线图。",
}

_SERIES = {
    "500hPa位势高度": [584, 585, 586, 587, 588, 587, 586, 585],
    "2m气温": [20, 21, 23, 26, 29, 28, 25, 22],
    "降水": [0, 0.3, 1.0, 2.1, 3.0, 1.5, 0.5, 0.1],
    "10m风": [4, 5, 6, 7, 8, 7, 6, 5],
}


def run(params: dict) -> dict:
    v, region, lead = params.get("variable"), params.get("region"), params.get("lead_hours")
    data = _SERIES.get(v, [0] * 8)
    image_url = line_chart(f"GFS/ECMWF {region} {v}（+{lead}h）", {v: data})
    summary = (f"GFS/ECMWF 数值预报：未来 {lead} 小时{region}的「{v}」整体呈"
               f"{'上升' if data[-1] >= data[0] else '下降'}趋势，峰值约 {max(data)}。")
    return {"summary": summary, "image_url": image_url, "data": {"series": data}}
