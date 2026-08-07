"""Agent 基类：统一接口，子类实现具体角色逻辑。"""
from dataclasses import dataclass
from core.llm_client import LLMClient


@dataclass
class AgentResult:
    success: bool
    output: str
    detail: str = ""   # 调试/过程信息


class Agent:
    """所有角色 Agent 的基类。"""
    name: str = "base"
    system_prompt: str = ""

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    def run(self, user_input: str) -> AgentResult:
        raise NotImplementedError
