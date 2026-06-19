"""集中配置：路径与 DeepSeek 接入参数（从 .env 读取）。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
# 解析后端的数据目录（与本项目同级的 backend/data）
BACKEND_DATA_DIR = BASE_DIR.parent / "backend" / "data"

load_dotenv(BASE_DIR / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8004").strip().rstrip("/")

# v4-pro 为推理模型，官方样例启用 thinking。enabled/disabled；flash 可设 disabled 提速。
DEEPSEEK_THINKING = os.getenv("DEEPSEEK_THINKING", "enabled").strip().lower()
DEEPSEEK_REASONING_EFFORT = os.getenv("DEEPSEEK_REASONING_EFFORT", "high").strip()

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def has_llm() -> bool:
    """是否配置了可用的 DeepSeek 密钥。"""
    return bool(DEEPSEEK_API_KEY) and not DEEPSEEK_API_KEY.startswith("sk-your-key")
