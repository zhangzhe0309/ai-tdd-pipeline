"""agents/coder_agent.py 单元测试（不依赖 LLM 的部分）。"""
import pytest
from pathlib import Path
from agents.coder_agent import _is_safe


class TestIsSafe:
    def test_absolute_path_inside_run_dir(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "abc"
        run_dir.mkdir(parents=True)
        target = run_dir / "biz_logic.py"
        target.write_text("code", encoding="utf-8")
        assert _is_safe(str(target), run_dir) is True

    def test_relative_path_inside_run_dir(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "abc"
        run_dir.mkdir(parents=True)
        assert _is_safe("biz_logic.py", run_dir) is True

    def test_relative_path_outside_run_dir(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "abc"
        run_dir.mkdir(parents=True)
        # 从 run_dir 解析，'../config.py' 会跑到 run_dir 外面
        assert _is_safe("../config.py", run_dir) is False

    def test_absolute_path_outside_run_dir(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "abc"
        run_dir.mkdir(parents=True)
        assert _is_safe(str(tmp_path / "other.py"), run_dir) is False

    def test_none_path_returns_false(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "abc"
        run_dir.mkdir(parents=True)
        assert _is_safe("", run_dir) is False
