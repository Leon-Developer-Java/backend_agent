"""预测模型调用（MVP 桩）。

真实模型尚未接入（backend_pro 的 parser/模型注册表均为 None）。此处返回模拟
预测结论，并调 plotting 生成一张「预测曲线」示例图。后续把每个分支替换为真实
模型脚本调用即可，对外契约不变。
"""
from __future__ import annotations

from services.plotting import line_chart

# 支持的模型 -> (展示名, 模拟结论, 示例曲线)
_MODELS: dict[str, dict] = {
    "wrf": {
        "name": "WRF 短临降水预测",
        "summary": "WRF 模式预测：未来 6 小时{region}有分散性降水，主雨带集中在 12:00–15:00，"
                   "累计降水约 8–15mm，局地可达 25mm，建议关注短时强降水。",
        "series": {"降水(mm)": [0, 0.5, 1.2, 3.4, 6.1, 4.2, 1.8, 0.6]},
    },
    "radar_ext": {
        "name": "雷达回波外推",
        "summary": "雷达回波外推：当前回波单体向东北移动（约 35km/h），未来 1 小时{region}"
                   "回波强度维持 35–45dBZ，需防范短时强降水与雷暴。",
        "series": {"回波强度(dBZ)": [38, 41, 44, 43, 40, 37, 33, 30]},
    },
    "era5": {
        "name": "ERA5 场分析",
        "summary": "ERA5 再分析：{region}近地面气温日变化明显，午后 14 时前后达峰值约 30℃，"
                   "整体气压稳定，无明显天气系统过境。",
        "series": {"气温(℃)": [21, 22, 24, 27, 30, 29, 26, 23]},
    },
    "himawari": {
        "name": "葵花云图分析",
        "summary": "葵花卫星云图：{region}上空为中高云覆盖，云顶亮温偏低区对应对流活跃，"
                   "未来数小时云系缓慢东移。",
        "series": {"云顶亮温(K)": [250, 245, 240, 238, 242, 248, 255, 260]},
    },
}

ALIASES = {
    "wrf": "wrf", "radar": "radar_ext", "radar_ext": "radar_ext", "ext": "radar_ext",
    "era5": "era5", "himawari": "himawari", "satellite": "himawari",
}


def run_model(model: str, region: str | None = None, time: str | None = None) -> dict:
    """运行（模拟）指定模型，返回 {summary, image_url}。"""
    key = ALIASES.get((model or "").strip().lower())
    if key is None:
        return {
            "summary": f"暂不支持模型「{model}」。当前可用：wrf、radar_ext、era5、himawari。",
            "image_url": None,
        }

    spec = _MODELS[key]
    region_text = (region or "目标区域").strip()
    summary = spec["summary"].format(region=region_text)
    title = f"{spec['name']} · {region_text}"
    image_url = line_chart(title, spec["series"])
    return {"summary": summary, "image_url": image_url}
