"""
    ====== modules/chat.py ======
    LLM service
        by spinner-bot
"""

import json
import urllib.request
import urllib.error

OLLAMA_API_URL = "http://localhost:11434/api/chat"


def chat(model: str, prompt: str) -> str:
    """
    发送单条消息给本地 Ollama 模型，返回助手回复内容。

    参数:
        model (str): 模型名称，例如 "llama3:8b"
        prompt (str): 用户输入内容

    返回:
        str: 模型回复文本

    异常:
        ConnectionError: 无法连接到 Ollama 服务
        RuntimeError: 调用出错（例如模型不存在、内存不足等）
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False  # 关闭流式响应，一次性返回完整结果
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
        raise ConnectionError(f"无法连接到Ollama服务: {e}")
    except Exception as e:
        raise RuntimeError(f"调用Ollama出错: {e}")


def chat_loop(model: str):
    """
    简单的命令行对话循环，输入 exit/quit/q 退出。

    参数:
        model (str): 模型名称
    """
    print(f"开始与模型 {model} 对话，输入 'exit' 退出。")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ('exit', 'quit', 'q'):
            break
        if not user_input:
            continue
        try:
            reply = chat(model, user_input)
            print(f"AI: {reply}")
        except Exception as e:
            print(f"错误: {e}")