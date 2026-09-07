"""隔离运行 pytest。Windows 兼容（用 sys.executable -m pytest）。"""
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def run_pytest(test_file: str, cwd: str, timeout: int = 60) -> dict:
    """
    返回 {passed, output}。
    - passed: bool，pytest 返回码是否为 0
    - output: str，stdout+stderr（供落盘 traceback.log）
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
    except FileNotFoundError:
        return {"passed": False, "output": "[pytest 命令未找到，请检查环境]"}
    except PermissionError:
        return {"passed": False, "output": "[无权限执行 pytest]"}
    except OSError as e:
        logger.warning(f"pytest 执行失败: {e}")
        return {"passed": False, "output": f"[pytest 执行异常: {e}]"}
