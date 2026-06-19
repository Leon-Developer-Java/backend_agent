"""模型文件模板 —— 复制本文件改名为 <yourname>_model.py 即可。

开发者三步接入自己的模型：
  1. 复制本文件，命名如 wrf_model.py，放在 services/models/ 下。
  2. 在 services/models/__init__.py 的 _MODULE_NAMES 列表里登记模块名。
  3. 填写 SPEC（模型描述 + 输入参数）与 run()（你的真实模型逻辑，先用占位也行）。

agent 会自动把 SPEC 转成工具供大模型按需调用；必填校验与“缺参补全”由注册表统一
处理，你无需关心 agent 层。
"""
from services.plotting import line_chart

# ── 模型说明与输入参数 ──────────────────────────────────────────────────
SPEC = {
    "id": "model_xxx",          # 工具名，全局唯一，约定 model_<类型>
    "name": "示例模型",          # 展示名（用于工具卡、参数补全卡）
    "data_type": "XXX",         # 对应的数据类型
    "description": "一句话说明这个模型做什么、解决什么问题、典型用途。",
    "params": [
        # type: "select" 前端给选项按钮；"text" 自由输入。required=True 表示必填。
        {"name": "region", "label": "区域", "type": "select", "required": True,
         "options": ["华北", "华东", "华南"]},
        {"name": "time", "label": "时间", "type": "text", "required": False,
         "default": "今天", "placeholder": "如 今天 / 明天 / 2025-06-18"},
    ],
    "output": "用文字描述模型输出：例如 结论文本 + 一张折线图。",
}


# ── 模型执行 ────────────────────────────────────────────────────────────
def run(params: dict) -> dict:
    """执行模型。注册表已完成必填校验并填好默认值，这里可直接取用。

    必须返回：{"summary": 文字结论, "image_url": 图片URL 或 None}
    可选附加：{"data": 任意结构化结果}
    真实接入时，把下面占位逻辑替换为模型/接口调用即可。
    """
    region = params.get("region")
    time = params.get("time")
    series = {"示例要素": [1, 2, 3, 4, 5, 4, 3, 2]}
    image_url = line_chart(f"{SPEC['name']} · {region}", series)
    summary = f"（示例）{time}{region}的模型结论。"
    return {"summary": summary, "image_url": image_url}
