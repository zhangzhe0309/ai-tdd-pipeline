"""Gemini 原生封装（google-genai SDK）。"""
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, MODEL_NAME, LLM_TEMPERATURE, GEMINI_BASE_URL

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY 未配置，请检查 .env")
        kwargs: dict = {"api_key": GEMINI_API_KEY}
        if GEMINI_BASE_URL:
            kwargs["http_options"] = {"base_url": GEMINI_BASE_URL}
        self.client = genai.Client(**kwargs)

    def chat(self, prompt: str, system_prompt: str = "") -> str:
        """纯文本 chat，兼容旧 main.py 调用面。"""
        try:
            resp = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt or None,
                    temperature=LLM_TEMPERATURE,
                ),
            )
            if not resp.candidates:
                logger.warning("LLM chat 返回空 candidates")
                return ""
            return resp.text or ""
        except Exception as e:
            raise RuntimeError(f"LLM chat 调用失败: {e}") from e

    def chat_with_tools(self, prompt, system_prompt, tools_def, dispatch,
                        max_iters=10) -> str:
        """手动 function-calling 循环。

        tools_def: list[types.FunctionDeclaration]
        dispatch: 可调用，签名 dispatch(name: str, args: dict) -> dict
                  （由 Agent 传入，把工具调用路由到真实 Python 函数）
        """
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        cfg = types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            tools=[types.Tool(function_declarations=tools_def)],
            temperature=LLM_TEMPERATURE,
        )
        for i in range(max_iters):
            try:
                resp = self.client.models.generate_content(
                    model=MODEL_NAME, contents=contents, config=cfg,
                )
            except Exception as e:
                logger.warning(f"LLM 调用失败 (迭代 {i+1}/{max_iters}): {e}")
                return f"[LLM 调用失败: {e}]"

            if not resp.function_calls:
                return resp.text or ""

            # 安全访问 candidates
            if not resp.candidates:
                logger.warning(f"LLM 返回空 candidates (迭代 {i+1})")
                return ""

            contents.append(resp.candidates[0].content)
            response_parts = []
            for fc in resp.function_calls:
                result = dispatch(fc.name, dict(fc.args or {}))
                response_parts.append(types.Part.from_function_response(
                    name=fc.name, response=result,
                ))
            contents.append(types.Content(role="user", parts=response_parts))

        return "[达到最大迭代次数未收敛]"  # 不再静默返回空字符串
