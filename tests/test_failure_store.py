"""memory/failure_store.py 单元测试。"""
import json
import pytest
from pathlib import Path
from memory.failure_store import _extract_signature, record, query


class TestExtractSignature:
    def test_assertion_error(self):
        tb = "AssertionError: assert 'a' == 'b'"
        assert _extract_signature(tb) == "AssertionError"

    def test_value_error_with_message(self):
        tb = "ValueError: invalid literal for int()"
        assert _extract_signature(tb) == "ValueError"

    def test_key_error(self):
        tb = "KeyError: 'missing_key'"
        assert _extract_signature(tb) == "KeyError"

    def test_module_not_found(self):
        tb = "ModuleNotFoundError: No module named 'foo'"
        assert _extract_signature(tb) == "ModuleNotFoundError"

    def test_no_exception(self):
        tb = "some random text without exceptions"
        assert _extract_signature(tb) == "unknown"

    def test_prefers_last_exception_line(self):
        """优先匹配最后一行异常格式。"""
        tb = (
            "Traceback (most recent call last):\n"
            "  File 'test.py', line 1\n"
            "ValueError: first error\n"
            "AssertionError: second error\n"
        )
        assert _extract_signature(tb) == "AssertionError"


class TestQuery:
    def _setup_store(self, tmp_failures_file: Path):
        """临时替换 FAILURES_FILE。"""
        import memory.failure_store as fs
        fs._original_file = getattr(fs, '_original_file', fs.FAILURES_FILE)
        fs.FAILURES_FILE = tmp_failures_file
        return fs

    def _restore(self, fs):
        fs.FAILURES_FILE = getattr(fs, '_original_file', fs.FAILURES_FILE)

    def test_query_miss(self, tmp_failures_file):
        fs = self._setup_store(tmp_failures_file)
        try:
            assert query("random error") is None
        finally:
            self._restore(fs)

    def test_query_hit(self, tmp_failures_file):
        tmp_failures_file.write_text(
            json.dumps({"error_signature": "ValueError", "fix_summary": "fix"}) + "\n",
            encoding="utf-8",
        )
        fs = self._setup_store(tmp_failures_file)
        try:
            result = query("ValueError: bad input")
            assert result is not None
            assert result["error_signature"] == "ValueError"
            assert result["fix_summary"] == "fix"
        finally:
            self._restore(fs)

    def test_query_skips_corrupt_lines(self, tmp_failures_file):
        tmp_failures_file.write_text(
            "this is not valid json\n"
            + json.dumps({"error_signature": "ValueError", "fix_summary": "ok"}) + "\n",
            encoding="utf-8",
        )
        fs = self._setup_store(tmp_failures_file)
        try:
            result = query("ValueError: test")
            assert result is not None
        finally:
            self._restore(fs)


class TestRecord:
    def _setup_store(self, tmp_failures_file: Path):
        import memory.failure_store as fs
        fs._original_file = getattr(fs, '_original_file', fs.FAILURES_FILE)
        fs.FAILURES_FILE = tmp_failures_file
        return fs

    def _restore(self, fs):
        fs.FAILURES_FILE = getattr(fs, '_original_file', fs.FAILURES_FILE)

    def test_record_new(self, tmp_failures_file):
        tmp_failures_file.write_text("", encoding="utf-8")
        fs = self._setup_store(tmp_failures_file)
        try:
            record("ValueError: test", "fix it")
            content = tmp_failures_file.read_text(encoding="utf-8")
            lines = [l for l in content.strip().split("\n") if l.strip()]
            assert len(lines) == 1
            rec = json.loads(lines[0])
            assert rec["error_signature"] == "ValueError"
            assert rec["fix_summary"] == "fix it"
            assert rec["hits"] == 1
        finally:
            self._restore(fs)

    def test_record_increment_hit(self, tmp_failures_file):
        tmp_failures_file.write_text(
            json.dumps({"error_signature": "ValueError", "fix_summary": "old", "hits": 2}) + "\n",
            encoding="utf-8",
        )
        fs = self._setup_store(tmp_failures_file)
        try:
            record("ValueError: test v2", "new fix")
            content = tmp_failures_file.read_text(encoding="utf-8")
            lines = [l for l in content.strip().split("\n") if l.strip()]
            assert len(lines) == 1
            rec = json.loads(lines[0])
            assert rec["hits"] == 3
            assert rec["fix_summary"] == "new fix"
        finally:
            self._restore(fs)

    def test_record_skips_corrupt_file(self, tmp_failures_file):
        tmp_failures_file.write_text("not json at all\n", encoding="utf-8")
        fs = self._setup_store(tmp_failures_file)
        try:
            record("TypeError: bad", "fix")
            content = tmp_failures_file.read_text(encoding="utf-8")
            lines = [l for l in content.strip().split("\n") if l.strip()]
            assert len(lines) == 1
            assert json.loads(lines[0])["error_signature"] == "TypeError"
        finally:
            self._restore(fs)
