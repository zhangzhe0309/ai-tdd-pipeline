# AI-TDD Pipeline

基于 AI Agent 驱动的自动化 TDD (Test-Driven Development) 开发流水线。通过多智能体协作与工��调用（RLM 模式），实现从“一句话需求”到“结构化产品文档”，再到“测试用例”，最后由 AI 自动编写代码、跑通测试的完整工程闭环。

## 🌟 核心特性 (Features)

1. **对抗式 TDD 闭环 (Adversarial TDD)**
   - **PM Agent**：将模糊的用户需求转化为精确的结构化特性列表 (Feature List)。
   - **QA Agent**：根据需求严格编写边缘测试与主流程的验收用例 (Pytest)。
   - **Coder Agent**：根据测试用例开发业务代码，若测试未通过，则根据真实报错自动迭代自愈。测试用例作为绝对事实裁判，物理隔离“提需求”与“写代码”的人设，避免 AI 左右互搏。

2. **长文境治理与工具调用 (RLM-style Tool Calling)**
   - 不盲目将庞大的报错日志塞进 Prompt 中。
   - Coder Agent 通过真实的 `read_file`、`write_file`、`run_pytest` 等工具函数与本地环境交互，像人类开发者一样操作终端与文件系统，极大降低上下文 Token 污染风险。

3. **经验记忆模块 (Failure Memory)**
   - 具有轻量级的错误记忆机制 (`memory/failures.jsonl`)，失败的经验与模式会被记录，使后续的修复过程更具方向性。

---

## 🏗️ 架构概览

```
ai-tdd-pipeline/
├── agents/             # 多智能体角色定义 (PM, QA, Coder)
├── core/               # 核心引擎 (LLM 客户端接入, 基类抽象)
├── tools/              # RLM 工具集 (文件读写, Pytest 沙盒)
├── memory/             # 历史失败经验挂载点
├── workspace/runs/     # 每次执行的产物隔离目录 (日志、源码、用例)
├── config.py           # 全局配置中心 (超参、超时、路径)
├── main.py             # 流水线主入口
└── requirements.txt    # 项目依赖
```

---

## 🚀 快速开始

### 1. 环境准备 (推荐使用 `.venv` 虚拟环境)

为避免依赖冲突和遵循系统级安全限制（尤其是 Linux 服务器环境下），**必须使用**虚拟环境进行安装。

```bash
# 1. 克隆代码
git clone https://github.com/zhangzhe0309/ai-tdd-pipeline.git
cd ai-tdd-pipeline

# 2. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# Windows: .venv\Scripts\activate

# 3. 安装核心依赖
pip install -r requirements.txt
```

### 2. LLM 接入配置

本项目原生使用 Google 的 `google-genai` SDK，可直连大模型，也可搭配本地网关代理使用。

复制 `.env.example` 并重命名为 `.env`：

```bash
# 将配置安全写入 .env (避免使用 VIM 直接覆盖引发格式问题，推荐追加写入)
echo 'GEMINI_API_KEY=你的API_KEY' >> .env
echo 'MODEL_NAME=gemini-3.6-flash-medium' >> .env
```

**💡 进阶：使用本地 Gemini 代理服务接入 (如 agycli2api 方案)**
如果你在服务器配置了本地 OAuth2 转换代理（如监听在 3403 端口），流水线中已做好代码级别支持，可以直接在 `core/llm_client.py` 初始化时注入 `http_options={"base_url": "http://localhost:3403"}` 即可无缝代理。

### 3. 运行流水线

激活虚拟环境后，直接运行主函数：

```bash
python main.py
```

执行后，流水线将在 `workspace/runs/<timestamp>/` 目录下生成本次任务的：
- `features.md` (需求文档)
- `test_logic.py` (测试用例)
- `biz_logic.py` (业务代码)
- `traceback.log` (自愈错误记录)

你可以打开 `main.py` 底部的 `run_pipeline` 参数，修改为你想要开发的具体需求！

---

## 🛠️ 关于作者与贡献

基于 AI 与工程化效能提效探索构建，项目思路融合了智能体协作与 TDD 驱动原则。欢迎提出 Issue 或通过 PR 完善项目架构！
