"""Gemini 原生封装（google-genai SDK）。"""
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, MODEL_NAME, LLM_TEMPERATURE


class LLMClient:
    def __init__(self):
        # 缺 key 在这里直接报错，早失败早排查
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY 未配置，请检查 .env")
        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={"base_url": "http://localhost:3403"}
        )

    # ---- 纯文本 chat（兼容旧 main.py 调用面）----
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        resp = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=LLM_TEMPERATURE,
            ),
        )
        return resp.text or ""

    # ---- 手动 function-calling 循环 ----
    # tools_def: list[types.FunctionDeclaration]
    # dispatch: 可调用，签名 dispatch(name: str, args: dict) -> dict
    #           （由 Agent 传入，把工具调用路由到真实 Python 函数）
    def chat_with_tools(self, prompt, system_prompt, tools_def, dispatch,
                        max_iters=10) -> str:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        cfg = types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            tools=[types.Tool(function_declarations=tools_def)],
            temperature=LLM_TEMPERATURE,
        )
        for _ in range(max_iters):
            resp = self.client.models.generate_content(
                model=MODEL_NAME, contents=contents, config=cfg,
            )
            # 没有 function_call → 模型给出最终文本
            if not resp.function_calls:
                return resp.text or ""
            # 把模型的 function_call 回合加回上下文
            contents.append(resp.candidates[0].content)
            # 逐个执行工具，结果以 function_response 喂回
            response_parts = []
            for fc in resp.function_calls:
                result = dispatch(fc.name, dict(fc.args or {}))
                response_parts.append(types.Part.from_function_response(
                    name=fc.name, response=result,
                ))
            contents.append(types.Content(role="user", parts=response_parts))
        return ""  # 达到上限未收敛
