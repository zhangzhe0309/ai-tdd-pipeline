"""失败经验 JSONL 持久化。Continual Harness 对 TDD 自愈唯一有价值的子集。"""
import json
import re
from datetime import datetime
from config import FAILURES_FILE


def _extract_signature(traceback: str) -> str:
    """从 traceback 抓错误签名（仅抓取错误类名，如 AssertionError），提高经验复用率。"""
    # 匹配独立的单词结尾为Error或Exception的，比如 AssertionError, TypeError
    matches = re.findall(r"\b([A-Z]\w*(?:Error|Exception))\b", traceback)
    return matches[-1] if matches else "unknown"


def query(traceback: str) -> dict | None:
    """查相似错误。命中返回记录，否则 None。"""
    sig = _extract_signature(traceback)
    if not FAILURES_FILE.exists():
        return None
    with FAILURES_FILE.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("error_signature") == sig:
                return rec
    return None


def record(traceback: str, fix_summary: str) -> None:
    """落盘一条失败经验。若同签名已存在则 hits+1。"""
    FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    sig = _extract_signature(traceback)
    now = datetime.now().isoformat(timespec="seconds")
    # 读已有
    existing = []
    if FAILURES_FILE.exists():
        existing = [json.loads(l) for l in FAILURES_FILE.open(encoding="utf-8")
                    if l.strip()]
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
    # 全量重写（jsonl 量小，全量写最简单可靠）
    with FAILURES_FILE.open("w", encoding="utf-8") as f:
        for rec in existing:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
