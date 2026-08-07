import time
import pytest
from biz_logic import handle_message


# AC-1: 单关键词匹配 - 请假
@pytest.mark.parametrize(
    "msg_input",
    [
        "张三明天请假",
        "请假一天",
        "我想请假",
        "请假",
    ],
)
def test_single_keyword_leave(msg_input):
    """测试包含'请假'关键词，应同步返回'已记录审批'"""
    assert handle_message(msg_input) == "已记录审批"


# AC-2: 单关键词匹配 - 加班
@pytest.mark.parametrize(
    "msg_input",
    [
        "今晚需要加班",
        "加班报销",
        "申请加班",
        "加班",
    ],
)
def test_single_keyword_overtime(msg_input):
    """测试包含'加班'关键词，应同步返回'辛苦了'"""
    assert handle_message(msg_input) == "辛苦了"


# AC-3: 默认兜底回复
@pytest.mark.parametrize(
    "msg_input",
    [
        "你好",
        "收到请回复",
        "今天天气真好",
        "123456",
        "hello world",
    ],
)
def test_default_fallback(msg_input):
    """测试未命中任何规则时，统一按兜底规则返回'收到'"""
    assert handle_message(msg_input) == "收到"


# AC-4: 多关键词冲突验证（高优先级覆盖低优先级）
@pytest.mark.parametrize(
    "msg_input",
    [
        "我申请请假，顺便问下加班费",
        "我今天加班处理请假流程",
        "请假与加班",
        "加班 请假",
    ],
)
def test_keyword_conflict_priority(msg_input):
    """测试同时包含'请假'和'加班'时，优先匹配高优先级的'请假'"""
    assert handle_message(msg_input) == "已记录审批"


# AC-5.1: 带空格/换行输入过滤
@pytest.mark.parametrize(
    "msg_input, expected",
    [
        ("  请假 \n ", "已记录审批"),
        ("\t加班\n", "辛苦了"),
        ("   你好 \n\r", "收到"),
    ],
)
def test_whitespace_and_newline_trimming(msg_input, expected):
    """测试输入文本包含前导、后导空格或换行符时的匹配能力"""
    assert handle_message(msg_input) == expected


# AC-5.2 & AC-5.3: 空输入、Null、非字符串及非文本消息容错处理
@pytest.mark.parametrize(
    "invalid_input",
    [
        "",  # 空字符串
        "   ",  # 纯空格字符串
        None,  # Null 类型
        12345,  # 数字类型
        ["请假"],  # 列表类型
        {"type": "image", "url": "http://example.com/a.jpg"},  # 模拟飞书图片卡片
        {"type": "interactive", "elements": []},  # 模拟飞书富文本/卡片消息
    ],
)
def test_invalid_and_non_text_inputs(invalid_input):
    """测试非标准输入（空值/None/非文本/卡片消息等）时，不崩溃且触发兜底返回'收到'"""
    assert handle_message(invalid_input) == "收到"


# 非功能性需求：性能验证（处理时长 < 10ms）
def test_performance_execution_time():
    """测试 handle_message 纯逻辑处理时长必须小于 10ms"""
    long_msg = "这是一个非常长但最后包含请假的测试消息文本" * 50
    
    start_time = time.perf_counter()
    result = handle_message(long_msg)
    end_time = time.perf_counter()

    elapsed_time_ms = (end_time - start_time) * 1000
    
    assert result == "已记录审批"
    assert elapsed_time_ms < 10, f"处理超时！实际耗时: {elapsed_time_ms:.2f}ms"