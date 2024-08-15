from typing import (
    Any,
    Dict
)
import requests
import json

from utils import return_config

headers = {
    "Authorization": "Bearer q7r8s9t0-u1v2-w3x4-y5z6-a7b8c9d0e1f2",
    "User-Agent": "Apifox/1.0.0(https://apifox.com)",
    "Content-Type": "application/json"
}

stream_body = {
    "model": "qwen1.5-32b-chat-int4",
    "messages": [
        {"role": "system", "content": "你是一个乐于助人的助手"},
        {"role": "user", "content": "你好,请给我讲一个故事"}
    ],
    "temperature": 0.9,
    "stream": True
}

body = {
    "model": "qwen1.5-32b-chat-int4",
    "messages": [
        {"role": "system", "content": "你是一个乐于助人的助手"},
        {"role": "user", "content": "你好,请给我讲一个故事"}
    ],
    "temperature": 0.9
}

def post(
    url: str,
    json: Dict,
    headers: Dict,
    stream: bool
) -> Any:
    if stream:
        response = requests.post(url, json=json, headers=headers, stream=True)
    else:
        response = requests.post(url, json=json, headers=headers)
    return response

# 解析openai流式输出内容
def analy_openai_stream(response) -> None:
    full_text = ""
    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")
            print(line_str)
            try:
                data = json.loads(line_str.split(": ", 1)[1])
                if data["choices"][0]["finish_reason"] != "stop":
                    if "content" in data["choices"][0]["delta"]:
                        full_text += data["choices"][0]["delta"]["content"]
                else:
                    print("本次回答使用token数:", data["usage"]["completion_tokens"])
                    print("提问和回答总共使用token数:", data["usage"]["total_tokens"])
                    break
            except Exception as e:
                print(line_str)
    print("大模型完整回答：\n", full_text)



if __name__ == "__main__":
    _, server_params, llm_params, _ = return_config()
    ip = "localhost"
    port = server_params["PORT"]

    response = post(f"http://{ip}:{port}/v1/chat/completions", json=stream_body, headers=headers, stream=True)
    analy_openai_stream(response)

    response = post(f"http://{ip}:{port}/v1/chat/completions", json=body, headers=headers, stream=False)
    print(response.text)

