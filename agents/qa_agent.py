"""QA Agent：基于 Feature List 生成 pytest 测试。含人工审核闭环。"""
import re
import sys
from core.agent import Agent, AgentResult


def _extract_code(text: str) -> str:
    """从 ```python ... ``` 中抽取代码。"""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


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
        resp = self.client.chat(f"请为以下功能编写 pytest 测试用例:\n{features}", self.base_prompt)
        tests = _extract_code(resp)

        # 非交互环境自动批
        if not human_review or not sys.stdin.isatty():
            return AgentResult(success=True, output=tests, detail="非交互/关闭审核，自动批准")

        # 人工审核闭环
        while True:
            print("\n========== 【人工审核 QA 测试用例】 ==========")
            print(tests)
            fb = input("输入 'y' 批准，或输入修改意见打回给 QA: ").strip()
            if fb.lower() == "y":
                return AgentResult(success=True, output=tests, detail="人类已批准")
            resp = self.client.chat(
                f"原始需求：\n{features}\n\n"
                f"之前的测试用例有遗漏，请按人类意见修改并输出完整 pytest 代码。\n"
                f"人类意见: {fb}\n\n之前用例:\n{tests}", self.base_prompt,
            )
            tests = _extract_code(resp)
