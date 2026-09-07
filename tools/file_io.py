"""文件读写工具，供 Coder Agent 通过 function-calling 调用。"""
from pathlib import Path


def read_file(path: str) -> dict:
    """读文件。返回 {content} 或 {error}（不泄露完整路径）。"""
    try:
        text = Path(path).read_text(encoding="utf-8")
        return {"content": text}
    except FileNotFoundError:
        return {"error": "File not found"}
    except PermissionError:
        return {"error": "Permission denied"}
    except OSError:
        return {"error": "Failed to read file"}


def write_file(path: str, content: str) -> dict:
    """写文件。返回 {ok, path} 或 {error}（不泄露完整路径）。"""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": p.name}
    except OSError:
        return {"error": "Failed to write file"}
