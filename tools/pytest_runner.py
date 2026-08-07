"""隔离运行 pytest。Windows 兼容（用 sys.executable -m pytest）。"""
import subprocess
import sys


def run_pytest(test_file: str, cwd: str, timeout: int = 60) -> dict:
    """
    返回 {passed, output}。
    - passed: bool，pytest 返回码是否为 0
    - output: str，stdout+stderr（供落盘 traceback.log，不直接拼进 prompt）
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout + "\n" + result.stderr
        return {"passed": result.returncode == 0, "output": output}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": f"[pytest 超时，{timeout}s]"}
