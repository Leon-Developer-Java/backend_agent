"""6 个测试模型的注册表 —— 参数校验 + 缺参提示 + 工具 schema 自动生成。

设计目标：**便于多人协作**。每个模型一个独立文件（见 _template.py），导出
`SPEC`（描述 + 输入参数）与 `run(params)`（输出）。其他开发者只需：
  1. 复制 _template.py 改名为 <yourname>_model.py，填好 SPEC 与 run()；
  2. 在下面 _MODULE_NAMES 列表里登记模块名。
agent 层（tools/llm）无需改动——工具会自动从 SPEC 生成，必填校验与“缺参补全”
由本注册表统一处理。
"""
from importlib import import_module

# 已登记的模型模块（文件名去掉 .py）。新增模型在此加一行即可。
_MODULE_NAMES = [
    "era5_model",      # 成员1 ERA5
    "gfs_model",       # 成员2 GFS/ECMWF
    "cma_model",       # 成员3 CMA
    "radar_model",     # 成员4 雷达
    "himawari_model",  # 成员5 葵花卫星
    "wrf_model",       # 成员6 WRF
]

_MODULES = {}
SPECS = []
for _name in _MODULE_NAMES:
    _mod = import_module(f"{__name__}.{_name}")
    _MODULES[_mod.SPEC["id"]] = _mod
    SPECS.append(_mod.SPEC)


def list_specs() -> list[dict]:
    return SPECS


def label_for(model_id: str) -> str:
    mod = _MODULES.get(model_id)
    return (mod.SPEC["name"] + " 计算中") if mod else "模型计算中"


def _missing_params(spec: dict, params: dict) -> list[dict]:
    """返回缺失的必填参数（带选项，供前端渲染选择/输入）。"""
    miss = []
    for p in spec["params"]:
        if p.get("required") and not str(params.get(p["name"]) or "").strip():
            miss.append({
                "name": p["name"],
                "label": p["label"],
                "type": p.get("type", "text"),
                "options": p.get("options", []),
                "placeholder": p.get("placeholder", ""),
                "required": True,
            })
    return miss


def run_model(model_id: str, params: dict | None) -> dict:
    """调用模型。返回统一结构：
    - 成功： {"status":"ok", "summary", "image_url", "data"?}
    - 缺参： {"status":"need_params", "model", "model_name", "missing":[...], "summary"}
    - 出错： {"status":"error", "summary", "image_url":None}
    """
    mod = _MODULES.get(model_id)
    if mod is None:
        return {"status": "error", "summary": f"未知模型：{model_id}", "image_url": None}

    params = params or {}
    miss = _missing_params(mod.SPEC, params)
    if miss:
        labels = "、".join(m["label"] for m in miss)
        return {
            "status": "need_params",
            "model": model_id,
            "model_name": mod.SPEC["name"],
            "missing": miss,
            "summary": f"调用【{mod.SPEC['name']}】还需要补充参数：{labels}。请在下方选择或直接输入。",
            "image_url": None,
        }

    # 填入默认值后执行
    filled = dict(params)
    for p in mod.SPEC["params"]:
        if not str(filled.get(p["name"]) or "").strip() and p.get("default") is not None:
            filled[p["name"]] = p["default"]

    out = mod.run(filled)
    out.setdefault("status", "ok")
    return out


def build_tool_schemas() -> list[dict]:
    """把每个模型 SPEC 转成一个 OpenAI function-calling 工具。

    注意：参数一律不在 schema 里标 required，让大模型即使信息不全也先调用，
    由注册表返回 need_params，从而触发“前端选择/输入补全”的业务流程。
    """
    schemas = []
    for spec in SPECS:
        props = {}
        for p in spec["params"]:
            desc = p["label"]
            if p.get("options"):
                desc += "，可选：" + " / ".join(map(str, p["options"]))
            if p.get("required"):
                desc += "（必填）"
            props[p["name"]] = {"type": "string", "description": desc}
        schemas.append({
            "type": "function",
            "function": {
                "name": spec["id"],
                "description": f"{spec['name']}（数据类型 {spec['data_type']}）：{spec['description']}",
                "parameters": {"type": "object", "properties": props},
            },
        })
    return schemas
