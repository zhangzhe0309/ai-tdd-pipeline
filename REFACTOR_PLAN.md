# AI-TDD-Pipeline 重构施工蓝图（接力文档）

> **用途**：本文件是完整施工说明，供换模型 / 新会话直接接手实施，**不依赖任何对话上下文**。
> 读这一份就能开干。生成日期：2026-08-07。
> 配套计划：`C:\Users\EDY\.claude\plans\golden-wandering-scone.md`（内容基本一致，本文件更详细且含代码骨架）。

---

## 0. 一句话目标

把这个**当前跑不通**的 TDD 多 Agent 脚本，重做成**地基扎实、架构正确、诚实体现代抗式 TDD + RLM 工具调用 + 失败经验记忆**的系统。受 Prime Agent 思想启发，但不蹭概念。

---

## 1. 现状诊断（为什么必须大改动）

真实项目根（双层嵌套，见 §3）：`D:\gitHub\ai-tdd-pipeline\ai-tdd-pipeline\`

| # | 问题 | 证据 | 严重度 |
|---|---|---|---|
| 1 | `core/llm_client.py` 彻底丢失，import 第一行就崩 | `main.py:8` `from core.llm_client import LLMClient` 指向 `D:\gitHub\core\`，但该目录在全 `D:\gitHub` 树下不存在 | 🔴 致命 |
| 2 | 零依赖声明 | 无 `requirements.txt` / `pyproject.toml` / `setup.py` | 🔴 致命 |
| 3 | 无 `.venv`，本机无可用 pytest | 默认 Python 3.13 无 pytest；uv 的 3.12 环境也无 | 🔴 致命 |
| 4 | Windows 不兼容 | `main.py:26` 写死 POSIX 路径 `.venv/bin/pytest`（Windows 应为 `Scripts\pytest.exe`） | 🟡 |
| 5 | 工程治理缺失 | 无 `.gitignore` / `.env` / `.env.example` / `README`；`__pycache__` 已被 git 跟踪 | 🟡 |
| 6 | ARCHITECTURE.md 名不副实 | 号称"V2.0 借鉴 Prime Agent 在 ARC-AGI-3 霸榜核心思想"，实际代码只有 `while` 重试 + traceback 拼进 prompt | 🟡 诚信 |

**当前 `main.py` 的粗糙自愈逻辑**（`step4_coder_recursive_repl`，第 75-114 行）：生成代码 → 跑 pytest → 把**整个 stdout+stderr 拼进 prompt** → 重试 4 次。这正是 RLM 要解决的"长内容撑爆上下文"痛点。

---

## 2. 用户已拍板的决策（不要再问）

| 维度 | 决策 |
|---|---|
| LLM SDK | **google-genai 原生**（不是老的 google-generativeai；不是 litellm；不是 LangChain） |
| 默认模型 | `gemini-2.5-flash`（在 `config.py` 可改） |
| 工具调用 | **手动 function-calling 循环**（自己解析 `response.function_calls` 并执行，不用 SDK 自动模式） |
| 范围 | **核心 + 经验记忆**（不做 Continual Harness 全套，不做 Agent 自改提示词） |
| 沙箱 | `subprocess` + 独立 run 目录 + 超时（不做 docker） |
| 人工审核节点 | 保留（零信任防线；非交互环境自动批） |
| git 操作 | **不做**（用户未要求，全局纪律禁止擅自 commit/branch） |

---

## 3. 项目根与双层嵌套（重要，别踩坑）

```
D:\gitHub\                    ← 总目录，聚合了一堆独立项目，不是 git repo
└── ai-tdd-pipeline\          ← 外层包装目录（只套了一层同名子目录）
    └── ai-tdd-pipeline\      ← ★ 真实项目根 = git 仓库根 ★
        ├── .git\             ← 独立 git repo，远程 origin = https://github.com/zhangzhe0309/ai-tdd-pipeline.git
        ├── ARCHITECTURE.md
        ├── main.py
        └── workspace\
```

**施工约定**：**不捋平嵌套**（移动 `.git` 风险高、收益低）。所有新文件一律建在真实项目根 `D:\gitHub\ai-tdd-pipeline\ai-tdd-pipeline\` 下。本文档后续所有相对路径都以这里为根。

> 原计划曾写"消除双层嵌套"——这里修正为**就地施工、不移动 .git**。功能完全不受影响。

---

## 4. 目标架构（完整目录树）

```
ai-tdd-pipeline/   (= D:\gitHub\ai-tdd-pipeline\ai-tdd-pipeline\)
├── main.py                    # 重写：仅做编排
├── config.py                  # 新建：模型/key/路径/超时/迭代上限
├── requirements.txt           # 新建
├── .env.example               # 新建
├── .gitignore                 # 新建
├── README.md                  # 新建
├── ARCHITECTURE.md            # 重写：校正措辞
├── REFACTOR_PLAN.md           # 本文件（施工蓝图，保留）
├── core/
│   ├── __init__.py
│   ├── llm_client.py          # 新建：Gemini 原生封装（chat + chat_with_tools）
│   └── agent.py               # 新建：Agent 基类
├── agents/
│   ├── __init__.py
│   ├── pm_agent.py            # 需求降维
│   ├── qa_agent.py            # 测试生成 + 人工审核闭环
│   └── coder_agent.py         # 约束编码 + 工具调用自愈循环（核心）
├── tools/
│   ├── __init__.py
│   ├── file_io.py             # read_file / write_file
│   └── pytest_runner.py       # run_pytest（隔离 cwd + 超时）
├── memory/
│   ├── __init__.py
│   └── failure_store.py       # 失败经验 JSONL 持久化
└── workspace/
    ├── __init__.py            # 保留
    ├── biz_logic.py           # 旧产物，可留可删（流水线会重新生成）
    ├── test_biz_logic.py      # 旧产物，可留可删
    └── runs/<run_id>/         # 新建：每次流水线一个隔离目录
```

模块化原则：每文件 200-400 行、单一职责（全局工程纪律规则 4）。

---

## 5. 逐文件施工规格

### 5.1 地基文件（最先建）

**`requirements.txt`**：
```
google-genai>=1.0.0
pytest>=8.0.0
python-dotenv>=1.0.0
```

**`.env.example`**：
```
# 在 https://aistudio.google.com/apikey 申请，复制到这里
GEMINI_API_KEY=
```
（实施时另建 `.env` 填真实 key，`.gitignore` 会忽略它）

**`.gitignore`**：
```
__pycache__/
*.pyc
.venv/
.env
workspace/runs/
*.log
```

**`README.md`**：写清三件事——(1) 装依赖 `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`；(2) 配 `.env` 里的 `GEMINI_API_KEY`；(3) 跑 `python main.py`。

### 5.2 `config.py`（新建）

```python
"""全局配置。所有可调参数集中在此。"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # 读 .env

# 路径（都以项目根为基准）
PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
RUNS_DIR = WORKSPACE_DIR / "runs"
MEMORY_DIR = PROJECT_ROOT / "memory"
FAILURES_FILE = MEMORY_DIR / "failures.jsonl"

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
LLM_TEMPERATURE = 0.2

# 流水线
CODER_MAX_ITERS = 6          # Coder 工具调用循环最大轮数（含自愈）
PYTEST_TIMEOUT_SEC = 60      # 单次 pytest 子进程超时
HUMAN_REVIEW = True          # 是否启用人工审核节点（非交互环境自动批）

# 启动时校验
RUNS_DIR.mkdir(parents=True, exist_ok=True)
if not GEMINI_API_KEY:
    # 不 raise，让缺 key 时也能 import；调用时报错更友好
    print("[config] 警告：未配置 GEMINI_API_KEY，LLM 调用将失败。")
```

### 5.3 `core/llm_client.py`（新建 ★核心★）

封装 google-genai。提供两个方法：`chat`（纯文本，供 PM/QA）和 `chat_with_tools`（手动 function-calling 循环，供 Coder）。

```python
"""Gemini 原生封装（google-genai SDK）。"""
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, MODEL_NAME, LLM_TEMPERATURE


class LLMClient:
    def __init__(self):
        # 缺 key 在这里直接报错，早失败早排查
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY 未配置，请检查 .env")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    # ---- 纯文本 chat（兼容旧 main.py 调用面）----
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        resp = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=LLM_TEMPERATURE,
            ),
        )
        return resp.text or ""

    # ---- 手动 function-calling 循环 ----
    # tools_def: list[types.FunctionDeclaration]
    # dispatch: 可调用，签名 dispatch(name: str, args: dict) -> dict
    #           （由 Agent 传入，把工具调用路由到真实 Python 函数）
    def chat_with_tools(self, prompt, system_prompt, tools_def, dispatch,
                        max_iters=10) -> str:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        cfg = types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            tools=[types.Tool(function_declarations=tools_def)],
            temperature=LLM_TEMPERATURE,
        )
        for _ in range(max_iters):
            resp = self.client.models.generate_content(
                model=MODEL_NAME, contents=contents, config=cfg,
            )
            # 没有 function_call → 模型给出最终文本
            if not resp.function_calls:
                return resp.text or ""
            # 把模型的 function_call 回合加回上下文
            contents.append(resp.candidates[0].content)
            # 逐个执行工具，结果以 function_response 喂回
            response_parts = []
            for fc in resp.function_calls:
                result = dispatch(fc.name, dict(fc.args or {}))
                response_parts.append(types.Part.from_function_response(
                    name=fc.name, response=result,
                ))
            contents.append(types.Content(role="user", parts=response_parts))
        return ""  # 达到上限未收敛
```

> ⚠️ google-genai API 细节备忘（见 §6）：`resp.function_calls` 是便利属性；`fc.name`/`fc.args`；`Part.from_function_response(name=, response={...})`。SDK 版本若 API 有出入，以 `pip show google-genai` 的版本对应的官方文档为准微调。

### 5.4 `core/agent.py`（新建）

```python
"""Agent 基类：统一接口，子类实现具体角色逻辑。"""
from dataclasses import dataclass
from core.llm_client import LLMClient


@dataclass
class AgentResult:
    success: bool
    output: str
    detail: str = ""   # 调试/过程信息


class Agent:
    """所有角色 Agent 的基类。"""
    name: str = "base"
    system_prompt: str = ""

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    def run(self, user_input: str) -> AgentResult:
        raise NotImplementedError
```

### 5.5 `tools/file_io.py`（新建）

```python
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
```

### 5.6 `tools/pytest_runner.py`（新建）

```python
"""隔离运行 pytest。Windows 兼容（用 sys.executable -m pytest）。"""
import subprocess
import sys


def run_pytest(test_file: str, cwd: str, timeout: int = 60) -> dict:
    """
    返回 {passed, output}。
    - passed: bool，pytest 返回码是否为 0
    - output: str，stdout+stderr（供落盘 traceback.log，不直接拼进 prompt）
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout + "\n" + result.stderr
        return {"passed": result.returncode == 0, "output": output}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": f"[pytest 超时，{timeout}s]"}
```

### 5.7 `memory/failure_store.py`（新建 ★经验记忆★）

```python
"""失败经验 JSONL 持久化。Continual Harness 对 TDD 自愈唯一有价值的子集。"""
import json
import re
from datetime import datetime
from config import FAILURES_FILE


def _extract_signature(traceback: str) -> str:
    """从 traceback 抓错误签名（最后一个 Error 行），用于相似度匹配。"""
    # 抓形如 AssertionError: / TypeError: / ValueError: 等
    matches = re.findall(r"([A-Z]\w*(?:Error|Exception)[^\n]*)", traceback)
    return matches[-1].strip() if matches else "unknown"


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
```

### 5.8 `agents/pm_agent.py`（新建）

```python
"""PM Agent：把粗糙需求降维成结构化 Feature List。纯文本 chat。"""
from core.agent import Agent, AgentResult


class PMAgent(Agent):
    name = "PM"
    system_prompt = (
        "你是一个资深产品经理。把用户的粗糙需求拆解为结构化的 Feature List，"
        "每条含验收标准。不要写代码，只写逻辑和验收标准。"
    )

    def run(self, requirement: str) -> AgentResult:
        features = self.client.chat(requirement, self.system_prompt)
        return AgentResult(success=True, output=features)
```

### 5.9 `agents/qa_agent.py`（新建，含人工审核闭环）

迁移原 `main.py:39-73` 的逻辑（QA 生成 + 人工打回重写）。

```python
"""QA Agent：基于 Feature List 生成 pytest 测试。含人工审核闭环。"""
import re
import sys
from core.agent import Agent, AgentResult


def _extract_code(text: str) -> str:
    """从 ```python ... ``` 中抽取代码。"""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


class QAAgent(Agent):
    name = "QA"
    base_prompt = (
        "你是一个资深测试开发工程师(QA)。基于 Feature List 编写 Python pytest 测试用例。\n"
        "要求：\n"
        "1. 测试目标模块约定为 biz_logic，顶部写 from biz_logic import handle_message。\n"
        "2. 只写测试逻辑，绝对不要写业务实现。\n"
        "3. 只输出纯 Python 代码，放在 ```python``` 代码块中。"
    )

    def run(self, features: str, human_review: bool = True) -> AgentResult:
        resp = self.client.chat(f"请为以下功能编写 pytest 测试用例:\n{features}", self.base_prompt)
        tests = _extract_code(resp)

        # 非交互环境自动批
        if not human_review or not sys.stdin.isatty():
            return AgentResult(success=True, output=tests, detail="非交互/关闭审核，自动批准")

        # 人工审核闭环
        while True:
            print("\n========== 【人工审核 QA 测试用例】 ==========")
            print(tests)
            fb = input("输入 'y' 批准，或输入修改意见打回给 QA: ").strip()
            if fb.lower() == "y":
                return AgentResult(success=True, output=tests, detail="人类已批准")
            resp = self.client.chat(
                f"之前的测试用例有遗漏，请按人类意见修改并输出完整 pytest 代码。\n"
                f"人类意见: {fb}\n\n之前用例:\n{tests}", self.base_prompt,
            )
            tests = _extract_code(resp)
```

### 5.10 `agents/coder_agent.py`（新建 ★RLM 核心★）

持有 `[read_file, write_file, run_pytest]` 三个真工具，走手动 function-calling 循环。这是整个重构的核心价值点。

```python
"""Coder Agent：约束编码 + 工具调用自愈循环。RLM 思想核心落地。

模型用工具操作环境（读 traceback、写 biz_logic、跑 pytest），
而不是把日志/代码全塞进 prompt。
"""
from pathlib import Path
from google.genai import types
from core.agent import Agent, AgentResult
from tools.file_io import read_file, write_file
from tools.pytest_runner import run_pytest
from memory import failure_store
import config


# 工具的 FunctionDeclaration（告诉模型有哪些工具可用）
_TOOLS = [
    types.FunctionDeclaration(
        name="read_file",
        description="读取指定路径文件内容（如读取 traceback.log 了解报错）",
        parameters=types.Schema(type="OBJECT", properties={
            "path": types.Schema(type="STRING", description="文件绝对路径"),
        }, required=["path"]),
    ),
    types.FunctionDeclaration(
        name="write_file",
        description="写入文件（如写入生成的 biz_logic.py）",
        parameters=types.Schema(type="OBJECT", properties={
            "path": types.Schema(type="STRING"),
            "content": types.Schema(type="STRING"),
        }, required=["path", "content"]),
    ),
    types.FunctionDeclaration(
        name="run_pytest",
        description="在隔离目录运行 pytest。返回通过与否及输出路径。",
        parameters=types.Schema(type="OBJECT", properties={
            "test_file": types.Schema(type="STRING"),
            "cwd": types.Schema(type="STRING", description="运行目录，通常 = run 目录"),
        }, required=["test_file", "cwd"]),
    ),
]


def _dispatch(name: str, args: dict, run_dir: Path) -> dict:
    """把模型发的工具调用路由到真实函数。run_dir 用于 pytest 落盘。"""
    if name == "read_file":
        return read_file(args["path"])
    if name == "write_file":
        return write_file(args["path"], args["content"])
    if name == "run_pytest":
        res = run_pytest(args["test_file"], args["cwd"], timeout=config.PYTEST_TIMEOUT_SEC)
        # RLM 关键：长输出落盘，只把摘要回给模型；模型用 read_file 看细节
        log_path = run_dir / "traceback.log"
        log_path.write_text(res["output"], encoding="utf-8")
        return {
            "passed": res["passed"],
            "output_path": str(log_path),
            "hint": "完整输出已写入 output_path，用 read_file 查看" if not res["passed"] else "",
        }
    return {"error": f"未知工具: {name}"}


class CoderAgent(Agent):
    name = "Coder"
    system_prompt = (
        "你是高级后端工程师。任务：编写 biz_logic.py 使给定 pytest 测试 100% 通过。\n"
        "工作方式：先用 run_pytest 跑测试；失败时用 read_file 读 output_path 指向的 traceback.log，"
        "分析后用 write_file 修正 biz_logic.py，再跑，直到全部通过。\n"
        "通过后，用 write_file 把最终 biz_logic.py 写好，并回复 DONE。"
    )

    def run(self, tests_code: str, run_dir: Path) -> AgentResult:
        # 1. 落盘测试代码
        test_path = run_dir / "test_biz_logic.py"
        write_file(str(test_path), tests_code)
        biz_path = run_dir / "biz_logic.py"

        # 2. 经验记忆：查相似失败，命中则注入提示
        hint = ""
        # 先跑一次拿初始 traceback
        first = run_pytest(str(test_path), str(run_dir))
        if not first["passed"]:
            (run_dir / "traceback.log").write_text(first["output"], encoding="utf-8")
            mem = failure_store.query(first["output"])
            if mem:
                hint = f"\n\n[经验记忆] 同类错误曾出现 {mem['hits']} 次，当时修复思路：{mem['fix_summary']}"

        # 3. function-calling 自愈循环
        prompt = (
            f"测试文件已生成在 {test_path}，biz_logic 写在 {biz_path}（运行目录 {run_dir}）。\n"
            f"请编写 biz_logic.py 让测试通过。可用工具：read_file / write_file / run_pytest。{hint}"
        )
        dispatch = lambda name, args: _dispatch(name, args, run_dir)
        final = self.client.chat_with_tools(
            prompt, self.system_prompt, _TOOLS, dispatch, config.CODER_MAX_ITERS,
        )

        # 4. 验证最终产物
        biz_code = biz_path.read_text(encoding="utf-8") if biz_path.exists() else ""
        last = run_pytest(str(test_path), str(run_dir))
        if last["passed"]:
            # 成功 → 落盘经验记忆
            if first["passed"] is False and first["output"]:
                failure_store.record(first["output"], f"最终通过；末态代码见 {biz_path}")
            return AgentResult(success=True, output=biz_code, detail="测试全绿，已交付")
        # 失败
        return AgentResult(success=False, output=biz_code,
                           detail=f"达到最大迭代仍未通过。末次输出见 {run_dir}/traceback.log")
```

### 5.11 `main.py`（重写：瘦身为编排层）

```python
"""AI-TDD Pipeline 入口：编排 PM → QA → 人工审核 → Coder 自愈 → 交付。"""
from datetime import datetime
from pathlib import Path
from config import RUNS_DIR, HUMAN_REVIEW
from core.llm_client import LLMClient
from agents.pm_agent import PMAgent
from agents.qa_agent import QAAgent
from agents.coder_agent import CoderAgent


def run_pipeline(requirement: str) -> None:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "requirement.md").write_text(requirement, encoding="utf-8")
    print(f">>> AI-TDD Pipeline 启动 | run_id={run_id} | run_dir={run_dir}")

    client = LLMClient()

    # Node 1: PM 降维
    pm = PMAgent(client)
    features = pm.run(requirement).output
    (run_dir / "features.md").write_text(features, encoding="utf-8")
    print(f"[PM] Feature List 已生成 → {run_dir}/features.md")

    # Node 2 + 3: QA 生成 + 人工审核
    qa = QAAgent(client)
    qa_res = qa.run(features, human_review=HUMAN_REVIEW)
    tests = qa_res.output
    print(f"[QA] 测试用例已{'批准' if qa_res.success else '中止'} | {qa_res.detail}")

    # Node 4: Coder 工具调用自愈
    coder = CoderAgent(client)
    code_res = coder.run(tests, run_dir)
    (run_dir / "biz_logic.py").write_text(code_res.output, encoding="utf-8")

    print("\n>>> 流水线完毕 <<<")
    print(f"结果: {'✅ 交付' if code_res.success else '⚠️ 未完全通过'}")
    print(f"交付物: {run_dir}/biz_logic.py | 详情: {code_res.detail}")


if __name__ == "__main__":
    req = ("写一个简单的飞书机器人模块，包含 handle_message(msg) 函数。"
           "如果消息包含'请假'，返回'已记录审批'；如果包含'加班'，返回'辛苦了'；否则返回'收到'。")
    run_pipeline(req)
```

### 5.12 `ARCHITECTURE.md`（重写：校正）

删掉"借鉴 Prime Agent 在 ARC-AGI-3 霸榜核心思想"等夸大。如实写成三块：
1. **对抗式 TDD**：QA（出测试）与 Coder（写实现）物理隔离，pytest 执行终态裁判，零信任。
2. **RLM 式工具调用**：Coder 用 `read_file/write_file/run_pytest` 真工具操作环境；长内容（traceback/需求）落盘到 `workspace/runs/<run_id>/`，按需读取，不塞 prompt。
3. **失败经验记忆**：自愈失败的错误模式落盘到 `memory/failures.jsonl`，下次同类错误优先注入已知解法。
末尾如实标注："受 Prime Agent 的 RLM 思想启发；未实现其 Continual Harness 全套（自改提示词/技能），因对固定流水线收益有限且有 reward hacking 风险。"

### 5.13 各 `__init__.py`

`core/__init__.py`、`agents/__init__.py`、`tools/__init__.py`、`memory/__init__.py`：空文件即可（`memory/__init__.py` 可加 `from . import failure_store` 方便导入）。`workspace/__init__.py` 已存在，保留。

---

## 6. 关键实现细节备忘（接手者必读）

### 6.1 google-genai 手动 function-calling 正确写法
- `resp.function_calls`（便利属性）→ 返回 `list[FunctionCall]`，每个有 `.name`、`.args`
- 无 function_call 时，`resp.text` 即最终答案
- **必须把模型的 function_call 回合加回 contents**：`contents.append(resp.candidates[0].content)`
- 工具结果用 `types.Part.from_function_response(name=..., response={...})` 包装，包进 `Content(role="user", parts=[...])` 再 append
- `tools=[types.Tool(function_declarations=[...])]`，FunctionDeclaration 用 `types.Schema(type="OBJECT", properties={...}, required=[...])`
- 安装后先 `pip show google-genai` 看版本；若 API 名有出入，查该版本官方文档微调（核心循环逻辑不变）

### 6.2 RLM 落地的关键设计
- `run_pytest` 工具**不把完整 output 塞回模型**，而是写进 `traceback.log`，只回传 `{passed, output_path, hint}`
- 模型需要细节时自己调 `read_file(output_path)`——这就是"长内容当变量，按需读取"
- 对比旧 `main.py:107` 把整个 stderr 拼进 prompt，token 消耗和上下文污染大幅下降

### 6.3 经验记忆的诚实边界
- 只记"错误签名（最后一个 XxxError 行）→ 修复思路"
- 查询用签名精确匹配（不上向量相似度，YAGNI）
- **不做**自改系统提示词、不做技能库——那是 Continual Harness 全套，reward hacking 风险，砍掉

### 6.4 run_id 生成
`datetime.now().strftime("%Y%m%d_%H%M%S")`，每次流水线一个隔离目录。无需 UUID，时间戳够用。

### 6.5 模块导入
所有 `from config import ...`、`from core.llm_client import ...` 都假设**从项目根运行** `python main.py`。项目根在 `sys.path[0]`（脚本所在目录），无需 `sys.path.append` 那套跨级 hack。

---

## 7. 实施顺序（分阶段，每阶段可独立验证）

**阶段 0 · 地基**（最高优先）
1. 建 `requirements.txt` / `.env.example` / `.gitignore`
2. 建 `.venv`：`python -m venv .venv` → 激活（Windows `.venv\Scripts\activate`）
3. `pip install -r requirements.txt`
4. 建 `.env` 填 `GEMINI_API_KEY`
5. 验证：`.venv` 下 `python -c "import google.genai; import pytest; import dotenv"` 无报错

**阶段 1 · 配置与 LLM 封装**
6. 建 `config.py`
7. 建 `core/llm_client.py`，写个小脚本验证 `LLMClient().chat("说ok", "")` 能返回

**阶段 2 · 工具与记忆**
8. 建 `tools/file_io.py`、`tools/pytest_runner.py`（单元自测：临时建文件读写、跑个空 pytest）
9. 建 `memory/failure_store.py`（自测 record→query 往返）

**阶段 3 · Agents**
10. 建 `core/agent.py` 基类
11. 建 `agents/pm_agent.py`、`agents/qa_agent.py`
12. 建 `agents/coder_agent.py`（最复杂，function-calling 循环）

**阶段 4 · 编排与文档**
13. 重写 `main.py`
14. 重写 `ARCHITECTURE.md`、写 `README.md`

**阶段 5 · 端到端验证**（见 §8）

---

## 8. 验证清单（端到端）

1. **地基**：`from core.llm_client import LLMClient` 不报 ImportError；`.venv` 有 pytest
2. **冒烟**：配好 key 后 `python main.py` 跑通——PM→QA→（人工 y 或自动批）→Coder 自愈→交付
3. **RLM 落地**：检查 `workspace/runs/<run_id>/traceback.log` 存在；Coder 调试打印里能看到它走了 `read_file(traceback.log)` 而非把 stderr 拼进 prompt
4. **经验记忆**：故意构造一个让 Coder 首次失败的测试；第二次跑相似错误时确认 `memory/failures.jsonl` 有记录且被命中注入（看 Coder 日志的 `[经验记忆]` 提示）
5. **Windows 兼容**：pytest 子进程用 `sys.executable -m pytest`，无 "command not found"
6. **隔离**：每次运行产物都在独立 `runs/<run_id>/`，不污染主项目

---

## 9. 明确不做（YAGNI 边界，不要被"再完善一下"诱惑）

- ❌ Agent 自改系统提示词 / 技能库（Continual Harness 全套）——reward hacking 风险（Prime Agent 在 Factorio 作弊刷分那种），对固定流水线收益低
- ❌ docker 沙箱——subprocess + 临时目录 + 超时已够
- ❌ 常驻 IPython 内核（Prime Agent 原版的"不关机 Python"）——对 5 步固定流水线是过度抽象，function-calling 工具循环已覆盖其核心价值
- ❌ 多 Agent 真并行 / 父子 Agent 消息总线——本流水线是顺序依赖，无并行需求
- ❌ 捋平双层嵌套目录 / 移动 .git——风险高收益低，就地施工
- ❌ git commit / branch——用户未要求，禁止擅自做

---

## 10. 可复用参考（跨仓库，不 import，只借鉴写法）

- `D:\gitHub\strix\strix\llm\llm.py`：成熟的 LLM 封装（litellm 多提供商 + 用量统计 + 约 18 种错误类型捕获），供 `llm_client.py` 补错误处理时参考
- `D:\gitHub\ai_test_case_agent\services\llm_service.py`：LangChain `JsonOutputParser` 结构化输出思路，若未来想让 QA 输出结构化 Feature List（当前 YAGNI，纯文本够）可参考

---

## 11. 接手者一句话指引

> 项目根 = `D:\gitHub\ai-tdd-pipeline\ai-tdd-pipeline\`。按 §7 阶段 0→5 顺序做，每个文件规格见 §5，代码骨架已给齐。先建地基和 `.env`（key），再逐层往上。遇到 google-genai API 出入，以 `pip show google-genai` 版本的官方文档为准。全程不碰 git。
