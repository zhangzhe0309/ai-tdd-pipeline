"""AI-TDD Pipeline 入口：编排 PM → QA → 人工审核 → Coder 自愈 → 交付。"""
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import RUNS_DIR, HUMAN_REVIEW
from core.llm_client import LLMClient
from agents.pm_agent import PMAgent
from agents.qa_agent import QAAgent
from agents.coder_agent import CoderAgent

# 基础日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline(requirement: str) -> None:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "requirement.md").write_text(requirement, encoding="utf-8")
    logger.info(
        "AI-TDD Pipeline 启动 | run_id=%s | run_dir=%s", run_id, run_dir
    )

    client = LLMClient()

    # Node 1: PM 降维
    pm = PMAgent(client)
    features = pm.run(requirement).output
    (run_dir / "features.md").write_text(features, encoding="utf-8")
    logger.info("[PM] Feature List 已生成 → %s/features.md", run_dir)

    # Node 2 + 3: QA 生成 + 人工审核
    qa = QAAgent(client)
    qa_res = qa.run(features, human_review=HUMAN_REVIEW)
    tests = qa_res.output
    status = "批准" if qa_res.success else "中止"
    logger.info("[QA] 测试用例已%s | %s", status, qa_res.detail)

    if not qa_res.success:
        logger.warning("流水线中止：测试用例未通过审核")
        return

    # Node 4: Coder 工具调用自愈
    coder = CoderAgent(client)
    code_res = coder.run(tests, run_dir)
    if code_res.output:
        (run_dir / "biz_logic.py").write_text(code_res.output, encoding="utf-8")

    ok = "交付" if code_res.success else "未完全通过"
    logger.info("流水线完毕 | 结果: %s | %s", ok, code_res.detail)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        req = " ".join(sys.argv[1:])
    else:
        req = ("写一个简单的飞书机器人模块，包含 handle_message(msg) 函数。"
               "如果消息包含'请假'，返回'已记录审批'；如果包含'加班'，返回'辛苦了'；"
               "否则返回'收到'。")
    run_pipeline(req)
