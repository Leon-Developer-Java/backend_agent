"""成员6 · WRF 短临降水预测（测试模型，逻辑为占位）。"""
from services.plotting import line_chart

REGIONS = ["华北", "华东", "华南", "西南", "西北", "东北"]

SPEC = {
    "id": "model_wrf",
    "name": "WRF 短临降水预测",
    "data_type": "WRF",
    "description": "WRF 中尺度模式短临降水预测，给出指定区域未来数小时降水落区与强度。",
    "params": [
        {"name": "region", "label": "区域", "type": "select", "required": True, "options": REGIONS},
        {"name": "duration_hours", "label": "预报时长(小时)", "type": "select", "required": False,
         "options": ["6", "12", "24"], "default": "6"},
        {"name": "time", "label": "时间", "type": "text", "required": False,
         "default": "今天", "placeholder": "如 今天 / 明天"},
    ],
    "output": "降水预测结论 + 逐时降水量折线图。",
}


def run(params: dict) -> dict:
    region, dur, time = params.get("region"), params.get("duration_hours"), params.get("time")
    data = [0, 0.5, 1.2, 3.4, 6.1, 4.2, 1.8, 0.6]
    image_url = line_chart(f"WRF {region} 降水预测（{time}·{dur}h）", {"降水(mm)": data})
    summary = (f"WRF 短临预测：{time}{region}未来 {dur} 小时有分散性降水，"
               f"主雨带集中在时段中段，峰值约 {max(data)}mm，局地可达 25mm，注意短时强降水。")
    return {"summary": summary, "image_url": image_url, "data": {"series": data}}
