# 模型层 · 多人协作说明

本目录每个 `*_model.py` 是一个独立的气象模型，互不影响。**你只需维护自己那一个文件。**

## 三步接入你的模型

1. **复制模板**：把 [`_template.py`](_template.py) 复制改名为 `xxx_model.py`（如 `wrf_model.py`）。
2. **登记**：在 [`__init__.py`](__init__.py) 的 `_MODULE_NAMES` 列表里加上你的模块名。
3. **填两样东西**：
   - `SPEC`：模型描述 + 输入参数（见下）。
   - `run(params)`：模型逻辑，返回 `{"summary": 文字结论, "image_url": 图片URL或None}`。

完成后，agent 会**自动**把你的模型暴露为一个工具，让大模型按用户意图调用——你**无需改动** agent / tools / llm 任何代码。

## SPEC 字段

```python
SPEC = {
    "id": "model_wrf",          # 工具名，全局唯一，约定 model_<类型>
    "name": "WRF 短临降水预测",  # 展示名
    "data_type": "WRF",         # 对应数据类型
    "description": "一句话说明用途。",
    "params": [
        # type="select" 前端给选项按钮；type="text" 自由输入
        # required=True 的参数缺失时，系统会自动弹卡片让用户补全
        {"name": "region", "label": "区域", "type": "select", "required": True,
         "options": ["华北", "华东", "华南"]},
        {"name": "time", "label": "时间", "type": "text", "required": False,
         "default": "今天", "placeholder": "如 今天 / 明天"},
    ],
    "output": "文字描述输出内容。",
}
```

## run() 约定

```python
def run(params: dict) -> dict:
    # params 已通过必填校验、并填好默认值
    ...
    return {"summary": "结论文字", "image_url": url_or_none, "data": {...}}  # data 可选
```

- 生成图片可直接用 `from services.plotting import line_chart`。
- 现在的 6 个文件都是**占位逻辑**（仅用于打通流程）；接真实模型时把 `run()` 内部替换为模型/接口调用即可，对外契约不变。

## 缺参补全流程（已内置，无需你实现）

用户说“跑一下 WRF” 但没给区域 → 注册表发现 `region` 必填缺失 → 前端弹出「区域」选择/输入卡 → 用户选 `华北` → 重新调用 → 出结果。你只要把必填参数标 `required: True` 并给 `options` 即可。
