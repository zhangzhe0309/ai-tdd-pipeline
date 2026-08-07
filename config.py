"""全局配置。所有可调参数集中在此。"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # 读 .env

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

# 流水线
CODER_MAX_ITERS = 6          # Coder 工具调用循环最大轮数（含自愈）
PYTEST_TIMEOUT_SEC = 60      # 单次 pytest 子进程超时
HUMAN_REVIEW = True          # 是否启用人工审核节点（非交互环境自动批）

# 启动时校验
RUNS_DIR.mkdir(parents=True, exist_ok=True)
if not GEMINI_API_KEY:
    # 不 raise，让缺 key 时也能 import；调用时报错更友好
    print("[config] 警告：未配置 GEMINI_API_KEY，LLM 调用将失败。")
