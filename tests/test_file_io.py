"""tools/file_io.py 单元测试。"""
import pytest
from pathlib import Path
from tools.file_io import read_file, write_file


class TestReadFile:
    def test_read_existing_file(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        result = read_file(str(f))
        assert result == {"content": "hello"}

    def test_read_missing_file(self, tmp_path: Path):
        result = read_file(str(tmp_path / "nonexistent.txt"))
        assert "error" in result
        assert result["error"] == "File not found"


class TestWriteFile:
    def test_write_new_file(self, tmp_path: Path):
        f = tmp_path / "new.txt"
        result = write_file(str(f), "content")
        assert result["ok"] is True
        assert result["path"] == "new.txt"
        assert f.read_text(encoding="utf-8") == "content"

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        f = tmp_path / "a" / "b" / "deep.txt"
        result = write_file(str(f), "deep")
        assert result["ok"] is True
        assert f.read_text(encoding="utf-8") == "deep"

    def test_write_overwrite(self, tmp_path: Path):
        f = tmp_path / "overwrite.txt"
        f.write_text("old", encoding="utf-8")
        result = write_file(str(f), "new")
        assert result["ok"] is True
        assert f.read_text(encoding="utf-8") == "new"
