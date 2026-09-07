"""agents/qa_agent.py 单元测试（不依赖 LLM 的部分）。"""
import pytest
from agents.qa_agent import _extract_code


class TestExtractCode:
    def test_basic_python_block(self):
        text = "```python\nassert 1 == 1\n```"
        assert _extract_code(text) == "assert 1 == 1"

    def test_python_keyword_optional(self):
        text = "```assert 1 == 1```"
        assert _extract_code(text) == "assert 1 == 1"

    def test_no_code_block_returns_empty(self):
        text = "Here is the test:\nassert 1 == 1"
        assert _extract_code(text) == ""

    def test_empty_code_block(self):
        text = "```python\n```"
        assert _extract_code(text) == ""

    def test_multiline_code(self):
        text = "```python\ndef test_a():\n    assert True\n```"
        assert _extract_code(text) == "def test_a():\n    assert True"

    def test_code_block_with_leading_newline(self):
        text = "```python\n\ndef foo():\n    pass\n```"
        assert _extract_code(text) == "def foo():\n    pass"
