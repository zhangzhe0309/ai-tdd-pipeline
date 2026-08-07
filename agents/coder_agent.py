"""Coder Agent：约束编码 + 工具调用自愈循环。RLM 思想核心落地。

模型用工具操作环境（读 traceback、写 biz_logic、跑 pytest），
而不是把日志/代码全塞进 prompt。
"""
from pathlib import Path
from google.genai import types
from core.agent import Agent, AgentResult
from tools.file_io import read_file, write_file
from tools.pytest_runner import run_pytest
from memory import failure_store
import config


# 工具的 FunctionDeclaration（告诉模型有哪些工具可用）
_TOOLS = [
    types.FunctionDeclaration(
        name="read_file",
        description="读取指定路径文件内容（如读取 traceback.log 了解报错）",
        parameters=types.Schema(type="OBJECT", properties={
            "path": types.Schema(type="STRING", description="文件绝对路径"),
        }, required=["path"]),
    ),
    types.FunctionDeclaration(
        name="write_file",
        description="写入文件（如写入生成的 biz_logic.py）",
        parameters=types.Schema(type="OBJECT", properties={
            "path": types.Schema(type="STRING"),
            "content": types.Schema(type="STRING"),
        }, required=["path", "content"]),
    ),
    types.FunctionDeclaration(
        name="run_pytest",
        description="在隔离目录运行 pytest。返回通过与否及输出路径。",
        parameters=types.Schema(type="OBJECT", properties={
            "test_file": types.Schema(type="STRING"),
            "cwd": types.Schema(type="STRING", description="运行目录，通常 = run 目录"),
        }, required=["test_file", "cwd"]),
    ),
]


def _dispatch(name: str, args: dict, run_dir: Path) -> dict:
    """把模型发的工具调用路由到真实函数。run_dir 用于路径约束与 pytest 落盘。"""
    def _is_safe(p: str) -> bool:
        try:
            return Path(p).resolve().is_relative_to(run_dir.resolve())
        except ValueError:
            return False

    if name == "read_file":
        path = args.get("path")
        if not path: return {"error": "Missing 'path' parameter"}
        if not _is_safe(path): return {"error": f"Path traversal denied: {path} is outside run_dir"}
        return read_file(path)
        
    if name == "write_file":
        path = args.get("path")
        content = args.get("content", "")
        if not path: return {"error": "Missing 'path' parameter"}
        if not _is_safe(path): return {"error": f"Path traversal denied: {path} is outside run_dir"}
        return write_file(path, content)
        
    if name == "run_pytest":
        test_file = args.get("test_file")
        cwd = args.get("cwd")
        if not test_file or not cwd: return {"error": "Missing 'test_file' or 'cwd' parameter"}
        if not _is_safe(test_file) or not _is_safe(cwd):
            return {"error": "Security exception: test_file and cwd must be within run_dir"}
            
        res = run_pytest(test_file, cwd, timeout=config.PYTEST_TIMEOUT_SEC)
        # RLM 关键：长输出落盘，只把摘要回给模型；模型用 read_file 看细节
        log_path = run_dir / "traceback.log"
        # 优化点：直接返回错误日志的最后10行，避免必须请求read_file
        tail = "\n".join(res["output"].splitlines()[-10:])
        log_path.write_text(res["output"], encoding="utf-8")
        return {
            "passed": res["passed"],
            "output_path": str(log_path),
            "hint": f"完整输出已写入 output_path。这里是最后十行摘要:\n{tail}" if not res["passed"] else "",
        }
    return {"error": f"未知工具: {name}"}


class CoderAgent(Agent):
    name = "Coder"
    system_prompt = (
        "你是高级后端工程师。任务：编写 biz_logic.py 使给定 pytest 测试 100% 通过。\n"
        "工作方式：先用 run_pytest 跑测试；失败时用 read_file 读 output_path 指向的 traceback.log，"
        "分析后用 write_file 修正 biz_logic.py，再跑，直到全部通过。\n"
        "通过后，用 write_file 把最终 biz_logic.py 写好，并回复 DONE。"
    )

    def run(self, tests_code: str, run_dir: Path) -> AgentResult:
        # 1. 落盘测试代码
        test_path = run_dir / "test_biz_logic.py"
        write_file(str(test_path), tests_code)
        biz_path = run_dir / "biz_logic.py"
        # 写入一个初始空白框架，避免直接 ModuleNotFoundError
        write_file(str(biz_path), "def handle_message(msg):\n    pass\n")

        # 2. 经验记忆：查相似失败，命中则注入提示
        hint = ""
        # 先跑一次拿初始 traceback
        first = run_pytest(str(test_path), str(run_dir))
        if not first["passed"]:
            (run_dir / "traceback.log").write_text(first["output"], encoding="utf-8")
            mem = failure_store.query(first["output"])
            if mem:
                hint = f"\n\n[经验记忆] 同类错误曾出现 {mem['hits']} 次，当时修复思路：{mem['fix_summary']}"

        # 3. function-calling 自愈循环
        prompt = (
            f"测试文件已生成在 {test_path}，biz_logic 写在 {biz_path}（运行目录 {run_dir}）。\n"
            f"请编写 biz_logic.py 让测试通过。可用工具：read_file / write_file / run_pytest。{hint}"
        )
        dispatch = lambda name, args: _dispatch(name, args, run_dir)
        final = self.client.chat_with_tools(
            prompt, self.system_prompt, _TOOLS, dispatch, config.CODER_MAX_ITERS,
        )

        # 4. 验证最终产物
        biz_code = biz_path.read_text(encoding="utf-8") if biz_path.exists() else ""
        last = run_pytest(str(test_path), str(run_dir))
        if last["passed"]:
            # 成功 → 落盘经验记忆
            if first["passed"] is False and first["output"]:
                failure_store.record(first["output"], f"最终通过；末态代码见 {biz_path}")
            return AgentResult(success=True, output=biz_code, detail="测试全绿，已交付")
        # 失败
        return AgentResult(success=False, output=biz_code,
                           detail=f"达到最大迭代仍未通过。末次输出见 {run_dir}/traceback.log")
