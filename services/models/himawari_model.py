"""成员5 · 葵花卫星云图分析（测试模型，逻辑为占位）。"""
from services.plotting import line_chart

REGIONS = ["华北", "华东", "华南", "西南", "西北", "东北", "全国"]

SPEC = {
    "id": "model_himawari",
    "name": "葵花卫星云图分析",
    "data_type": "Himawari",
    "description": "Himawari-8/9 卫星云图分析，识别云系分布与对流活跃区（云顶亮温）。",
    "params": [
        {"name": "channel", "label": "通道", "type": "select", "required": True,
         "options": ["红外IR", "可见光VIS", "水汽WV"]},
        {"name": "region", "label": "区域", "type": "select", "required": True, "options": REGIONS},
    ],
    "output": "云系分析结论 + 云顶亮温时序折线图。",
}


def run(params: dict) -> dict:
    channel, region = params.get("channel"), params.get("region")
    data = [250, 245, 240, 238, 242, 248, 255, 260]
    image_url = line_chart(f"葵花卫星 {region} {channel}", {"云顶亮温(K)": data})
    summary = (f"葵花卫星云图（{channel}）：{region}上空为中高云覆盖，"
               f"云顶亮温最低约 {min(data)}K（对应对流活跃区），未来数小时云系缓慢东移。")
    return {"summary": summary, "image_url": image_url, "data": {"series": data}}
