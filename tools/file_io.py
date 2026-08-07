"""文件读写工具，供 Coder Agent 通过 function-calling 调用。"""
from pathlib import Path


def read_file(path: str) -> dict:
    """读文件。返回 {content} 或 {error}。"""
    try:
        text = Path(path).read_text(encoding="utf-8")
        return {"content": text}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def write_file(path: str, content: str) -> dict:
    """写文件。返回 {ok, path} 或 {error}。"""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(p)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
