"""成员4 · 雷达回波外推（测试模型，逻辑为占位）。"""
from services.plotting import line_chart

SPEC = {
    "id": "model_radar",
    "name": "雷达回波外推",
    "data_type": "Radar",
    "description": "基于雷达组合反射率做回波外推短临预报，给出移速移向与强度演变。",
    "params": [
        {"name": "station", "label": "雷达站", "type": "select", "required": True,
         "options": ["北京", "上海", "广州", "成都", "武汉"]},
        {"name": "lead_minutes", "label": "外推时长(分钟)", "type": "select", "required": False,
         "options": ["30", "60", "120"], "default": "60"},
    ],
    "output": "外推结论（移速/移向/强度）+ 回波强度时序折线图。",
}


def run(params: dict) -> dict:
    station, lead = params.get("station"), params.get("lead_minutes")
    data = [38, 41, 44, 43, 40, 37, 33, 30]
    image_url = line_chart(f"{station}雷达 回波外推（+{lead}min）", {"回波强度(dBZ)": data})
    summary = (f"雷达回波外推（{station}站）：当前回波单体向东北方向移动（约 35km/h），"
               f"未来 {lead} 分钟回波强度维持 {min(data)}–{max(data)}dBZ，需防范短时强降水。")
    return {"summary": summary, "image_url": image_url, "data": {"series": data}}
