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

def chat_loop(history=None, sys_prompt=None, model="qwen3.5:2b", stream=True):
    """
    连续对话循环，可接续已有历史。

    参数:
        history (list|None): 初始历史消息列表，格式 [{"role":"user","content":"..."}, ...]
                             如果为 None，则创建空列表。
        sys_prompt: 系统提示词（字符串或列表）
        model: 模型名称
        stream: True 使用流式输出，False 使用非流式一次性输出
    """
    if history is None:
        history = []
    print(f"开始连续对话（模型: {model}），输入 'exit' 退出。")
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n对话结束。")
            break

        if user_input.lower() in ("exit", "quit", "q"):
            print("对话结束。")
            break
        if not user_input:
            continue

        # 将用户消息加入历史
        history.append({"role": "user", "content": user_input})

        print("AI: ", end="", flush=True)
        try:
            if stream:
                # 流式输出，同时收集完整回复用于更新历史
                full_reply = ""
                for chunk in chat_stream(
                    user_input,
                    sys_prompt=sys_prompt,
                    chat_history=history[:-1],  # 排除刚加入的用户消息，避免重复
                    model=model
                ):
                    full_reply += chunk
                    print(chunk, end="", flush=True)
                print()  # 换行
                history.append({"role": "assistant", "content": full_reply})
            else:
                # 非流式输出
                reply = chat(
                    user_input,
                    sys_prompt=sys_prompt,
                    chat_history=history[:-1],
                    model=model
                )
                print(reply)
                history.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"\n错误: {e}")
            # 出错时移除刚刚添加的用户消息，避免历史错乱
            if history and history[-1]["role"] == "user":
                history.pop()