import sys
import os
import subprocess
import json

# Add parent core dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.llm_client import LLMClient

client = LLMClient()
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), 'workspace')

def init_workspace():
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(os.path.join(WORKSPACE_DIR, '__init__.py'), 'w') as f:
        f.write('')

def extract_python_code(text: str) -> str:
    if '```python' in text:
        return text.split('```python')[1].split('```')[0].strip()
    elif '```' in text:
        return text.split('```')[1].split('```')[0].strip()
    return text.strip()

def run_pytest(test_file_path: str):
    pytest_cmd = os.path.join(os.path.dirname(__file__), ".venv/bin/pytest")
    if not os.path.exists(pytest_cmd):
        pytest_cmd = "pytest"
    
    result = subprocess.run([pytest_cmd, test_file_path, '-v', '--tb=short'], 
                            capture_output=True, text=True, cwd=WORKSPACE_DIR)
    return result.returncode == 0, result.stdout + "\n" + result.stderr

def step1_pm_analysis(raw_requirement: str) -> str:
    print("\n[Node 1] PM Agent 正在解析需求 (降维)...")
    sys_prompt = "你是一个资深产品经理，请将用户的粗糙需求拆解为结构化的Feature List。不要写代��，只写逻辑和验收标准。"
    return client.chat(raw_requirement, system_prompt=sys_prompt)

def step2_qa_test_gen(features: str) -> str:
    print("\n[Node 2] QA Agent 正在生成边界测试用例 (TDD)...")
    sys_prompt = """你是一个资深测试开发工程师(QA)。基于提供的Feature List，编写Python pytest测试用例代码。
要求：
1. 约定测试目标模块为 `biz_logic`，请在测试代码顶部写 `from biz_logic import handle_message` 或导入需要的函数。
2. 只写测试逻辑，绝对不要写业务实现。
3. 请只输出纯 Python 代码，放在 ```python 代码块中。"""
    resp = client.chat(f"请为以下功能编写pytest测试用例:\n{features}", system_prompt=sys_prompt)
    return extract_python_code(resp)

def step3_human_approval(qa_output: str) -> str:
    print("\n====================================")
    print("【等待人工审核 (Human-In-The-Loop)】")
    print("QA Agent 产出的测试用例(验收标准)如下:\n")
    print(qa_output)
    print("====================================\n")
    
    if not sys.stdin.isatty():
        print("[System] 非交互环境，默认批准测试用例。")
        return qa_output

    while True:
        feedback = input("请审核测试用例边界。\n输入 'y' 批准并进入 Coder 递归执行阶段，或输入修改意见打回给 QA Agent重写: ").strip()
        if feedback.lower() == 'y':
            print("\n[System] 人类已批准测试用例边界。")
            return qa_output
        else:
            print("\n[System] 正在将修改意见打回给 QA Agent (多Agent协同)...")
            qa_output = client.chat(
                f"之前的测试用例有遗漏，请根据人类工程师的意见修改，并输出完整的pytest代码:\n人类意见: {feedback}\n\n之前的用例:\n{qa_output}", 
                system_prompt="你是一个资深测试开发工程师(QA)。请听从人类指令修改测试用例，放在 ```python 代码块中。"
            )
            qa_output = extract_python_code(qa_output)
            print("\n[System] QA Agent 已更新测试用例。")
            print(qa_output)

def step4_coder_recursive_repl(tests_code: str, max_iterations: int = 4) -> str:
    print(f"\n[Node 3] Coder Agent 启动递归执行引擎 (REPL) - 最大迭代次数: {max_iterations}...")
    
    test_file_path = os.path.join(WORKSPACE_DIR, 'test_biz_logic.py')
    biz_file_path = os.path.join(WORKSPACE_DIR, 'biz_logic.py')
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(tests_code)
        
    sys_prompt = """你是一个高级后端工程师。
任务：编写业务代码 (`biz_logic.py`)，使得测试用例能够 100% Pass。
注意：只输出业务实现代码，不要修改测试用例。请将代码放在 ```python 块中。"""

    print("\n[Coder] 正在生成初始业务代码...")
    prompt = f"请编写业务代码以通过以下测试用例:\n{tests_code}"
    biz_code_resp = client.chat(prompt, system_prompt=sys_prompt)
    biz_code = extract_python_code(biz_code_resp)
    
    for iteration in range(1, max_iterations + 1):
        with open(biz_file_path, 'w', encoding='utf-8') as f:
            f.write(biz_code)
            
        print(f"\n[REPL 沙盒] 正在执行 pytest (第 {iteration} 轮)...")
        is_success, output = run_pytest(test_file_path)
        
        if is_success:
            print(f"✅ [REPL 沙盒] 恭喜！测试全部通过！")
            return biz_code
        else:
            print(f"❌ [REPL 沙盒] 测试失败，正在将报错栈(Traceback)回传给 Coder Agent 进行自愈...")
            fix_prompt = f"""你在上次生成的代码在执行时报错了。
这是 pytest 的输出日志：
{output}

请分析报错原因，修复你的业务代码并重新输出完整代码。只输出 Python 代码，放在 ```python 块中。"""
            biz_code_resp = client.chat(fix_prompt, system_prompt=sys_prompt)
            biz_code = extract_python_code(biz_code_resp)
            
    print("\n⚠️ [警告] 达到最大迭代次数，Coder Agent 无法自愈该代码。")
    return biz_code

def run_pipeline(requirement: str):
    print(">>> 启动 AI-TDD Prime Agent (v2.0 递归进化版) <<<")
    print(f"原始需求: {requirement}")
    init_workspace()
    
    features = step1_pm_analysis(requirement)
    qa_tests = step2_qa_test_gen(features)
    approved_tests = step3_human_approval(qa_tests)
    business_code = step4_coder_recursive_repl(approved_tests)
    
    print("\n>>> 流水线执行完毕 <<<")
    print("\n【最终交付：历经 REPL 沙盒验证的业务代码 (biz_logic.py)】:\n")
    print(business_code)

if __name__ == "__main__":
    req = "写一个简单的飞书机器人模块，包含一个 handle_message(msg) 函数。如果消息包含'请假'，返回'已记录审批'；如果包含'加班'，返回'辛苦了'；否则返回'收到'。"
    run_pipeline(req)
