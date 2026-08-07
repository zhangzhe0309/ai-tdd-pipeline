import sys
import os

# 将父级 core 目录加入环境变量
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.llm_client import LLMClient

client = LLMClient()

def step1_pm_analysis(raw_requirement: str) -> str:
    """PM Agent: 将粗糙需求转化为结构化的功能拆解"""
    print("\n[Node 1] PM Agent 正在解析需求...")
    sys_prompt = "你是一个资深产品经理，请将用户的粗糙需求拆解为结构化的Feature List。不要写代码，只写逻辑和验收标准。"
    return client.chat(raw_requirement, system_prompt=sys_prompt)

def step2_qa_test_gen(features: str) -> str:
    """QA Agent: 根据功能点，生成 Pytest 边界测试代码（不写业务实现）"""
    print("\n[Node 2] QA Agent 正在生成边界测试用例(TDD)...")
    sys_prompt = "你是一个资深测试开发工程师(QA)。基于提供的Feature List，编写Python pytest测试用例代码。只写测试代码和Mock逻辑，绝对不要写业务实现代码。用例需覆盖极端边界。请直接输出Python代码。"
    return client.chat(f"请为以下功能编写pytest测试用例:\n{features}", system_prompt=sys_prompt)

def step3_human_approval(qa_output: str) -> str:
    """Human-in-the-loop: 人工审核测试用例"""
    print("\n====================================")
    print("【等待人工审核 (Human-In-The-Loop)】")
    print("QA Agent 产出的测试用例(验收标准)如下:\n")
    print(qa_output)
    print("====================================\n")
    
    while True:
        feedback = input("请审核测试用例边界。\n输入 'y' 批准并生成代码，或输入修改意见打回给 QA Agent重写: ").strip()
        if feedback.lower() == 'y':
            print("\n[System] 人类已批准测试用例边界。")
            return qa_output
        else:
            print("\n[System] 正在将修改意见打回给 QA Agent...")
            # 重新调用 QA Agent 进行修改
            qa_output = client.chat(
                f"之前的测试用例有遗漏或错误，请根据以下人类工程师的意见修改，并输出完整的pytest代码:\n人类意见: {feedback}\n\n之前的用例:\n{qa_output}", 
                system_prompt="你是一个资深测试开发工程师(QA)。请听从人类指令修改测试用例。"
            )
            print("\n[System] QA Agent 已更新测试用例。")
            print(qa_output)

def step4_coder_implementation(tests_code: str) -> str:
    """Coder Agent: 根据测试用例，反向实现业务代码"""
    print("\n[Node 3] Coder Agent 正在根据受约束的测试用例编写业务代码...")
    sys_prompt = "你是一个高级后端工程师。你的任务是编写业务代码，使得提供的 pytest 测试用例能够 100% Pass。只输出业务实现代码，不要修改测试用例本身。"
    return client.chat(f"请编写业务代码以通过以下测试用例:\n{tests_code}", system_prompt=sys_prompt)

def run_pipeline(requirement: str):
    print(">>> 启动 AI-TDD Agent 流水线 <<<")
    print(f"原始需求: {requirement}")
    
    # 1. ��求分析
    features = step1_pm_analysis(requirement)
    
    # 2. 生成验收边界 (TDD)
    qa_tests = step2_qa_test_gen(features)
    
    # 3. 人工审核边界 (防止毒树之果 - Human-in-the-loop)
    approved_tests = step3_human_approval(qa_tests)
    
    # 4. 生成业务代码
    business_code = step4_coder_implementation(approved_tests)
    
    print("\n>>> 流水线执行完毕 <<<")
    print("\n【最终交付：受 TDD 强约束的业务代码】:\n")
    print(business_code)

if __name__ == "__main__":
    # 这是一个用来测试 MVP 的示例需求
    req = "写一个简单的飞书机器人模块，支持接收文本消息，如果消息包含'请假'，则返回'已记录审批'，否则原样复读。"
    run_pipeline(req)
