# 架构说明 (ARCHITECTURE.md)

本项目的架构如实实现以下三个核心部分：

1. **对抗式 TDD (Test-Driven Development)**：
   QA Agent（生成测试用例）与 Coder Agent（编写业务实现）物理隔离。
   使用 `pytest` 执行结果作为最终态裁判，实现零信任闭环测试。

2. **RLM 式工具调用 (Representation Learning Models)**：
   Coder Agent 通过 `read_file`、`write_file`、`run_pytest` 真实工具与环境交互。
   长篇报错（traceback）和复杂需求落盘到 `workspace/runs/<run_id>/` 目录，由 Agent 按需读取，而不盲目填充系统提示词 (Prompt)，以此控制 Token 消耗和避免上下文污染。

3. **失败经验记忆 (Failure Memory)**：
   将自愈失败的错误模式记录在 `memory/failures.jsonl` 中。
   在下次发生类似错误时，系统会优先将已知的修复方案注入上下文提供给 Agent。

**备注**：本项目深受 Prime Agent 的 RLM 思想启发；但在实践中并未实现其 Continual Harness 全套机制（例如让 Agent 自修改系统提示词或扩充功能技能），因为此类机制在固定流水线中的实际收益有限，并存在 reward hacking (奖励黑客行为) 风险。
