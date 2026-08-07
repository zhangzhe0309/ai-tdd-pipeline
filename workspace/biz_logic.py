import json
from typing import Any, Dict, Union


def handle_message(message: Any, *args, **kwargs) -> Any:
    """
    处理收到的业务消息。
    支持 Dict、JSON 字符串以及普通文本消息的处理。
    """
    if message is None:
        raise ValueError("Message cannot be None")

    # 处理字符串输入
    if isinstance(message, str):
        stripped = message.strip()
        if not stripped:
            raise ValueError("Message cannot be empty")

        # 尝试解析 JSON 格式字符串
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict):
                return _process_dict_message(parsed)
        except (json.JSONDecodeError, TypeError):
            pass

        # 文本命令响应
        if stripped.lower() == "ping":
            return "pong"
        return message

    # 处理字典结构输入
    if isinstance(message, dict):
        return _process_dict_message(message)

    # 不支持的数据类型
    if not isinstance(message, (str, dict)):
        raise TypeError(f"Unsupported message type: {type(message).__name__}")

    return message


def _process_dict_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理字典类型的消息结构。
    """
    msg_type = msg.get("type") or msg.get("action") or msg.get("command") or msg.get("event")
    payload = msg.get("payload") if "payload" in msg else msg.get("data", msg.get("content", msg.get("text")))

    response = dict(msg)

    if msg_type == "ping":
        if "type" in msg:
            response["type"] = "pong"
        if "status" in msg or "result" in msg:
            response["status"] = "success"
            response["result"] = "pong"
        else:
            response["response"] = "pong"
        return response

    if msg_type == "echo":
        response["status"] = "success"
        response["result"] = payload
        return response

    if "status" not in response and msg_type:
        response["status"] = "success"

    return response