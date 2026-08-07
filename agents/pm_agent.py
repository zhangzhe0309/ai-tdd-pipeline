"""PM Agent：把粗糙需求降维成结构化 Feature List。纯文本 chat。"""
from core.agent import Agent, AgentResult


class PMAgent(Agent):
    name = "PM"
    system_prompt = (
        "你是一个资深产品经理。把用户的粗糙需求拆解为结构化的 Feature List，"
        "每条含验收标准。不要写代码，只写逻辑和验收标准。"
    )

    def run(self, requirement: str) -> AgentResult:
        features = self.client.chat(requirement, self.system_prompt)
        return AgentResult(success=True, output=features)
