# AI-TDD Pipeline

本系统是一个基于 TDD（测试驱动开发）与 RLM（长内容当变量、工具操作环境）的多 Agent 自动编码流水线。

## 安装与运行

1. **安装依赖**：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/VPS 环境
   # 或 .venv\Scripts\activate (Windows 环境)
   pip install -r requirements.txt
   ```

2. **配置环境变量**：
   复制 `.env.example` 为 `.env`，并在其中填入你的 `GEMINI_API_KEY`。
   > **⚠️ VPS 部署注意事项 (To Hermes)**：
   > 用户已有一套 VPS 上的 Gemini 解决方案。请在接手本项目后，协助用户完成本项目的环境配置，并将该解决方案与本项目打通（如替换 API Endpoints、修改网络代理或直接注入合适的 `GEMINI_API_KEY` 等）。

3. **运行流水线**：
   ```bash
   python main.py
   ```
