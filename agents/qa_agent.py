"""QA Agent：基于 Feature List 生成 pytest 测试。含人工审核闭环。"""
import logging
import re
import sys
from core.agent import Agent, AgentResult

logger = logging.getLogger(__name__)


def _extract_code(text: str) -> str:
    """从 ```python ... ``` 中抽取代码。无代码块时返回空字符串。"""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    # 无代码块标记时，不盲目回退全文（避免把解释性文字当代码执行）
    logger.warning("QA 输出未包含代码块标记，将返回空字符串")
    return ""


class QAAgent(Agent):
    name = "QA"
    base_prompt = (
        "你是一个资深测试开发工程师(QA)。基于 Feature List 编写 Python pytest 测试用例。\n"
        "要求：\n"
        "1. 测试目标模块约定为 biz_logic，顶部写 from biz_logic import handle_message。\n"
        "2. 只写测试逻辑，绝对不要写业务实现。\n"
        "3. 只输出纯 Python 代码，放在 ```python``` 代码块中。"
    )

    def run(self, features: str, human_review: bool = True) -> AgentResult:
        resp = self.client.chat(
            f"请为以下功能编写 pytest 测试用例:\n{features}", self.base_prompt,
        )
        tests = _extract_code(resp)

        if not tests:
            return AgentResult(
                success=False, output="", detail="QA 未生成有效测试代码"
            )

        # 非交互环境自动批
        if not human_review or not sys.stdin.isatty():
            return AgentResult(success=True, output=tests, detail="非交互/关闭审核，自动批准")

        # 人工审核闭环
        for attempt in range(5):
            print(f"\n========== 【人工审核 QA 测试用例】(第 {attempt + 1} 次) ==========")
            print(tests)
            fb = input("输入 'y' 批准，输入修改意见打回给 QA，输入 'q' 退出: ").strip()
            if fb.lower() == "y":
                return AgentResult(success=True, output=tests, detail="人类已批准")
            if fb.lower() == "q":
                return AgentResult(success=False, output="", detail="用户主动退出审核")
            # 打回：用修改意见重新生成
            resp = self.client.chat(
                f"原始需求：\n{features}\n\n"
                f"之前的测试用例有遗漏，请按人类意见修改并输出完整 pytest 代码。\n"
                f"人类意见: {fb}\n\n之前用例:\n{tests}", self.base_prompt,
            )
            tests = _extract_code(resp)
            if not tests:
                return AgentResult(
                    success=False, output="", detail="打回后仍未生成有效测试代码"
                )

        return AgentResult(
            success=False, output="", detail="人工审核超过 5 次未批准，已中止"
        )
