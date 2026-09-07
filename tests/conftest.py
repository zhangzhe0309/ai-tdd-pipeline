"""共享测试夹具。"""
import json
import pytest
from pathlib import Path


@pytest.fixture
def tmp_failures_file(tmp_path: Path):
    """临时失败记忆文件，每次测试独立。"""
    f = tmp_path / "failures.jsonl"
    f.write_text("", encoding="utf-8")
    return f


@pytest.fixture
def sample_traceback() -> str:
    """模拟典型的 pytest 失败 traceback。"""
    return (
        "============================= test session starts ==============================\n"
        "collected 1 item\n\n"
        "tests/test_biz_logic.py F                                                    [100%]\n\n"
        "================================== FAILURES ===================================\n"
        "___________________________ test_handle_message请假 ____________________________\n\n"
        "    def test_handle_message请假():\n>       assert handle_message('请假') == '已记录审批'\n"
        "E       AssertionError: assert 'pass' == '已记录审批'\n"
        "E         - pass\n"
        "E         + 已记录审批\n\n"
        "tests/test_biz_logic.py:5: AssertionError\n"
        "=========================== short test summary info ===========================\n"
        "FAILED tests/test_biz_logic.py::test_handle_message请假 - AssertionError: ...\n"
        "============================== 1 failed in 0.01s ==============================\n"
    )
