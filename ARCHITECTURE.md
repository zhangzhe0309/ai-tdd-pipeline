# AI-TDD Pipeline: 基于测试驱动与零信任的 Agent 编排架构

## 1. 核心哲学 (Core Philosophy)
在传统的大模型代码生成中，人类直接向模型索要“业务代码”，这等同于在没有验收标准的情况下盲目外包，极易产生“大模型幻觉”和逻辑越界。

本架构引入**AI Reliability (AI 可靠性工程)** 与 **TDD (测试驱动开发)** 理念：
- **物理锚点**：大模型生成的代码是否正确，不能由另一个大模型空对空打分，必须由 Python 解释器（`pytest`）的执行终态来裁判。
- **边界前置**：在生成业务代码前，先由 QA Agent 生成“测试断言（Asserts）”。测试用例就是确定的边界。
- **零信任 (Zero-Trust)**：业务生成（Coder Agent）和测试生成（QA Agent）必须物理隔离，互不干扰，形成对抗博弈。

## 2. 流水线状态机 (State Machine)

流水线包含以下核心节点（Node）：

### [Node 1] PM Agent (需求降维)
- **输入**：粗糙、模糊的人类自然语言需求。
- **输出**：结构化的功能拆解（Feature List）与验收标准。
- **作用**：消除自然语言的歧义。

### [Node 2] QA Agent (边界圈定)
- **输入**：Node 1 产出的 Feature List。
- **输出**：Python `pytest` 自动化测试代码（仅含测试逻辑与 Mock，绝不包含业务实现）。
- **作用**：将业务逻辑具象化为确定的代码断言边界。

### [Node 3] Human-In-The-Loop (人工挂起点 - 关键防御)
- **机制**：流水线在此自动暂停（Suspend）。
- **人类动作**：人类工程师审核 Node 2 输出的测试用例。
    - 若边界缺失（如漏了负数校验），打回（Reject）并附��修改意见，QA Agent 重新生成。
    - 若边界严密，批准（Approve）。
- **作用**：防止“毒树之果”。大模型如果在需求理解阶段出错，后续的测试和代码错得再完美也是废品，必须由人类把控业务最终防线。

### [Node 4] Coder Agent (约束编码)
- **输入**：经过人工 Approve 的 `pytest` 测试代码。
- **输出**：业务实现代码（src code）。
- **系统提示词**：你的唯一目标是编写出能让输入的测试代码 100% 变绿的代码。

### [Node 5] Execution and Self-Healing (未来扩展：沙盒执行与自愈合)
- **机制**：物理环境拉起 `pytest` 运行 Node 4 的代码和 Node 2 的测试。
- **自愈闭环**：若 `Fail`，捕获 Error Traceback，重新发回 Node 4 强制修复；若 `Pass`，流水线终结，输出交付物。

## 3. 技术栈
- 编排层：纯 Python 脚本（后期可平滑迁移至 LangGraph）
- 模型层：`/core/llm_client.py` 封装的 Gemini 接口
- 执行层：本地沙盒 + `pytest`

## 4. V2.0 升级：引入 Prime Agent 递归与自愈机制
在 V2.0 版本中，我们借鉴了 Prime Agent 在 ARC-AGI-3 霸榜的核心思���，完成了以下架构演进：
1. **Persistent Orchestration (持久化协同)**：QA 节点和 Coder 节点不再是单向传值，人类打回测试用例时，QA Agent 会根据反馈上下文持续迭代，形成闭环。
2. **Recursive REPL (递归执行沙盒)**：Coder 生成业务代码后不再直接交付，而是自动挂载到本地沙盒运行 `pytest`。
3. **Traceback Self-Healing (基于报错栈的自愈)**：当 `pytest` 失败时，捕获终端报错日志（stdout/stderr），自动拼接成新 Prompt 回传给 Coder Agent，强制其修复代码。实现“不 Pass 不交付”的绝对防御。
