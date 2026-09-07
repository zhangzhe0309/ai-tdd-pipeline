"""全局配置。所有可调参数集中在此。"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# 路径（都以项目根为基准）
PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
RUNS_DIR = WORKSPACE_DIR / "runs"
MEMORY_DIR = PROJECT_ROOT / "memory"
FAILURES_FILE = MEMORY_DIR / "failures.jsonl"

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
LLM_TEMPERATURE = 0.2
# 可选：本地代理地址，未设置则直连 Gemini 官方 API
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "")

# 流水线
CODER_MAX_ITERS = 6          # Coder 工具调用循环最大轮数（含自愈）
PYTEST_TIMEOUT_SEC = 60      # 单次 pytest 子进程超时
HUMAN_REVIEW = True          # 是否启用人工审核节点（非交互环境自动批）
