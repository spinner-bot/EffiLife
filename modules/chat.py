"""
    ====== modules/chat.py ======
    LLM service
        by spinner-bot
"""

import json
import urllib.request
import urllib.error

OLLAMA_API_URL = "http://localhost:11434/api/chat"


def _prepare_messages(message, sys_prompt=None, chat_history=None):
    """
    组装 messages 列表，按 system → history → user 顺序。
    若 sys_prompt 为列表，则转换为 JSON 字符串作为一个 system 消息。
    """
    messages = []
    if sys_prompt:
        if isinstance(sys_prompt, str):
            system_content = sys_prompt
        elif isinstance(sys_prompt, list):
            # 将列表包装成 JSON 字符串，模型可解析
            system_content = json.dumps(sys_prompt, ensure_ascii=False)
        else:
            system_content = str(sys_prompt)
        messages.append({"role": "system", "content": system_content})

    if chat_history:
        if isinstance(chat_history, list):
            messages.extend(chat_history)
        # 其他类型（如 dict）暂不支持，忽略

    messages.append({"role": "user", "content": message})
    return messages


def chat(message, sys_prompt=None, chat_history=None, model="qwen3.5:2b"):
    """
    非流式对话，一次性返回完整回复。

    参数:
        message (str): 用户输入
        sys_prompt (str|list|None): 系统提示，若为列表则序列化为 JSON
        chat_history (list|None): 历史消息列表
        model (str): 模型名称

    返回:
        str: 助手回复文本
    """
    messages = _prepare_messages(message, sys_prompt, chat_history)
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('message', {}).get('content', '')
    except urllib.error.URLError as e:
        raise ConnectionError(f"无法连接到 Ollama 服务: {e}")
    except Exception as e:
        raise RuntimeError(f"调用 Ollama 出错: {e}")


def chat_stream(message, sys_prompt=None, chat_history=None, model="qwen3.5:2b"):
    """
    流式对话，返回生成器，逐段输出助手回复。
    """
    messages = _prepare_messages(message, sys_prompt, chat_history)
    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        resp = urllib.request.urlopen(req)
        for line in resp:
            line = line.strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
            if chunk.get('done'):
                break
    except urllib.error.URLError as e:
        raise ConnectionError(f"无法连接到 Ollama 服务: {e}")
    except Exception as e:
        raise RuntimeError(f"调用 Ollama 出错: {e}")