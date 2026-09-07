"""失败经验 JSONL 持久化。Continual Harness 对 TDD 自愈唯一有价值的子集。"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from config import FAILURES_FILE

logger = logging.getLogger(__name__)


def _extract_signature(traceback: str) -> str:
    """从 traceback 提取错误签名。

    优先匹配最后一行异常格式（如 'AssertionError: ...'），
    退化到匹配 traceback 中所有 Error/Exception 类名的最后一个。
    """
    lines = traceback.strip().splitlines()
    # 优先：匹配最后一行异常格式 "ExceptionType: message"
    for line in reversed(lines):
        m = re.match(r"\s*(\w+(?:Error|Exception))\s*:", line)
        if m:
            return m.group(1)
    # 退化：取最后一个 Error/Exception 类名
    matches = re.findall(r"\b([A-Z]\w*(?:Error|Exception))\b", traceback)
    return matches[-1] if matches else "unknown"


def query(traceback: str) -> dict | None:
    """查相似错误。命中返回记录，否则 None。"""
    sig = _extract_signature(traceback)
    if not FAILURES_FILE.exists():
        return None
    try:
        with FAILURES_FILE.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("error_signature") == sig:
                    return rec
    except OSError as e:
        logger.warning(f"读取失败记忆失败: {e}")
    return None


def record(traceback: str, fix_summary: str) -> None:
    """落盘一条失败经验。若同签名已存在则 hits+1。

    使用临时文件写后再覆盖，避免写操作中途崩溃导致文件损坏。
    """
    FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    sig = _extract_signature(traceback)
    now = datetime.now().isoformat(timespec="seconds")

    # 读已有记录
    existing: list[dict] = []
    if FAILURES_FILE.exists():
        try:
            with FAILURES_FILE.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        existing.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            logger.warning(f"读取失败记忆失败，将从空开始: {e}")

    # 命中则更新，否则新增
    for rec in existing:
        if rec.get("error_signature") == sig:
            rec["hits"] = rec.get("hits", 0) + 1
            rec["last_seen"] = now
            rec["fix_summary"] = fix_summary
            break
    else:
        existing.append({
            "error_signature": sig,
            "error_excerpt": traceback[:500],
            "fix_summary": fix_summary,
            "hits": 1,
            "last_seen": now,
        })

    # 写临时文件再 rename（避免写入中途崩溃导致文件损坏）
    tmp_path = FAILURES_FILE.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in existing),
            encoding="utf-8",
        )
        tmp_path.replace(FAILURES_FILE)
    except OSError as e:
        logger.warning(f"写入失败记忆失败: {e}")
