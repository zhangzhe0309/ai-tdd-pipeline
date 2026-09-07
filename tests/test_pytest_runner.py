"""tools/pytest_runner.py 单元测试。"""
import pytest
from pathlib import Path
from tools.pytest_runner import run_pytest


class TestRunPytest:
    def test_passing_test(self, tmp_path: Path):
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def test_pass():\n    assert True\n", encoding="utf-8")
        result = run_pytest(str(test_file), str(tmp_path), timeout=10)
        assert result["passed"] is True

    def test_failing_test(self, tmp_path: Path):
        test_file = tmp_path / "test_fail.py"
        test_file.write_text("def test_fail():\n    assert False\n", encoding="utf-8")
        result = run_pytest(str(test_file), str(tmp_path), timeout=10)
        assert result["passed"] is False
        assert "FAILED" in result["output"]

    def test_missing_file(self, tmp_path: Path):
        result = run_pytest(str(tmp_path / "nonexistent.py"), str(tmp_path), timeout=10)
        assert result["passed"] is False
        assert "error" in result["output"].lower() or "no such" in result["output"].lower()
