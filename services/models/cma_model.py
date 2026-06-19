"""成员3 · CMA 模式产品诊断（测试模型，逻辑为占位）。"""
from services.plotting import line_chart

REGIONS = ["华北", "华东", "华南", "西南", "西北", "东北", "全国"]

SPEC = {
    "id": "model_cma",
    "name": "CMA 模式产品诊断",
    "data_type": "CMA",
    "description": "中国气象局 CMA 模式产品的要素诊断，输出指定产品与要素的分析结论。",
    "params": [
        {"name": "product", "label": "模式产品", "type": "select", "required": True,
         "options": ["CMA-GFS", "CMA-MESO", "CMA-TYM"]},
        {"name": "variable", "label": "诊断要素", "type": "select", "required": True,
         "options": ["降水", "气温", "风"]},
        {"name": "region", "label": "区域", "type": "select", "required": True, "options": REGIONS},
    ],
    "output": "诊断结论 + 要素时序折线图。",
}

_SERIES = {
    "降水": [0, 0.4, 1.2, 2.6, 3.4, 1.8, 0.6, 0.2],
    "气温": [19, 20, 22, 25, 28, 27, 24, 21],
    "风": [3, 4, 5, 6, 7, 6, 5, 4],
}


def run(params: dict) -> dict:
    product, v, region = params.get("product"), params.get("variable"), params.get("region")
    data = _SERIES.get(v, [0] * 8)
    image_url = line_chart(f"{product} {region} {v}", {v: data})
    summary = (f"CMA 模式诊断（{product}）：{region}的「{v}」，"
               f"平均 {round(sum(data) / len(data), 1)}，峰值 {max(data)}。")
    return {"summary": summary, "image_url": image_url, "data": {"series": data}}
