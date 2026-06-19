"""查询已解析的气象数据：扫描解析后端的 *.meta.json。

解析产物结构见 backend/adapters/base.py：字段含 dataset_id / data_type /
variables / times / png_files / weather_info / bbox 等。data/ 为空时返回内置示例清单。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import BACKEND_DATA_DIR

# 内置示例清单，用于解析后端 data/ 目录为空时演示（本后端不依赖其它后端服务）
SAMPLE_DATASETS = [
    {"dataset_id": "era5_demo", "data_type": "ERA5", "title": "ERA5 再分析",
     "variables": ["温度", "气压", "风", "降水"], "times": 8, "png_count": 0},
    {"dataset_id": "gfs_demo", "data_type": "GFS", "title": "GFS/ECMWF 数值预报",
     "variables": ["位势高度", "温度", "风"], "times": 8, "png_count": 0},
    {"dataset_id": "radar_demo", "data_type": "Radar", "title": "雷达组合反射率",
     "variables": ["组合反射率 DBZH"], "times": 24, "png_count": 0},
    {"dataset_id": "wrf_demo", "data_type": "WRF", "title": "WRF 短临预测",
     "variables": ["降水", "温度", "风"], "times": 8, "png_count": 0},
]


def _summarize(meta: dict[str, Any]) -> dict[str, Any]:
    """从一份 meta.json 提炼出查询用摘要。"""
    variables = meta.get("variables") or []
    times = meta.get("times") or []
    png_files = meta.get("png_files") or []
    return {
        "dataset_id": meta.get("dataset_id"),
        "data_type": meta.get("data_type"),
        "title": (meta.get("weather_info") or {}).get("product") or meta.get("data_type"),
        "variables": variables,
        "times": len(times) if isinstance(times, list) else times,
        "png_count": len(png_files),
        "png_files": png_files,
        "bbox": meta.get("bbox"),
    }


def list_datasets(data_type: str | None = None) -> dict[str, Any]:
    """列出已解析数据集。data_type 可选过滤（如 ERA5/Radar/WRF）。"""
    datasets: list[dict[str, Any]] = []
    if BACKEND_DATA_DIR.exists():
        for meta_path in BACKEND_DATA_DIR.glob("*/*.meta.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            datasets.append(_summarize(meta))

    using_sample = False
    if not datasets:
        datasets = [d.copy() for d in SAMPLE_DATASETS]
        using_sample = True

    if data_type:
        key = data_type.strip().upper()
        datasets = [d for d in datasets if str(d.get("data_type", "")).upper() == key]

    return {
        "count": len(datasets),
        "using_sample": using_sample,
        "datasets": datasets,
    }
