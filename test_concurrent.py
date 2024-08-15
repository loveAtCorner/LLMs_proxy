from typing import Any, Dict, Optional, List
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
import random
from utils import return_config

# 设置日志记录，日志将被写入 'test_success_rate.log' 文件
logging.basicConfig(filename='test_success_rate.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 设置请求头，包括授权信息和内容类型
headers = {
    "Authorization": "Bearer q7r8s9t0-u1v2-w3x4-y5z6-a7b8c9d0e1f2",
    "User-Agent": "Apifox/1.0.0(https://apifox.com)",
    "Content-Type": "application/json"
}

# 请求体示例1：包含 stream 参数，表示流式输出
stream_body = {
    "model": "qwen1.5-32b-chat-int4",
    "messages": [
        {"role": "system", "content": "你是一个乐于助人的助手"},
        {"role": "user", "content": "你好,请给我讲一个故事"}
    ],
    "temperature": 0.9,
    "stream": True
}

# 请求体示例2：不包含 stream 参数，表示非流式输出
body = {
    "model": "qwen1.5-32b-chat-int4",
    "messages": [
        {"role": "system", "content": "你是一个乐于助人的助手"},
        {"role": "user", "content": "你好,请给我讲一个故事"}
    ],
    "temperature": 0.9
}

# 发送 POST 请求，根据是否流式处理选择不同的请求方式
def post(url: str, json: Dict, headers: Dict, stream: bool) -> Any:
    if stream:
        return requests.post(url, json=json, headers=headers, stream=True)
    return requests.post(url, json=json, headers=headers)

# 解析 OpenAI API 的流式输出内容
def analy_openai_stream(response) -> str:
    full_text = ""  # 用于存储完整的返回文本
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
                    print("本次回答使用 token 数:", data["usage"]["completion_tokens"])
                    print("提问和回答总共使用 token 数:", data["usage"]["total_tokens"])
                    break
            except Exception as e:
                print(line_str)
    print("大模型完整回答：\n", full_text)
    return full_text

# 处理单个请求，并根据是否为流式输出选择不同的处理方式
def handle_request(url: str, body: Dict, stream: bool) -> Optional[str]:
    try:
        response = post(url, json=body, headers=headers, stream=stream)
        if stream:
            return analy_openai_stream(response)
        return response.text
    except Exception as e:
        logging.error(f"Request failed: {str(e)}")
        return None

# 并发测试函数，用于逐步增加并发请求数量
def test_concurrency_increasing(url: str, max_concurrency: int, mode: str = "mixed"):
    for concurrent_requests in range(1, max_concurrency + 1):
        run_concurrency_test(url, concurrent_requests, mode)

# 并发测试函数，用于固定并发请求数量
def test_concurrency_fix(url: str, concurrent_requests: int, mode: str = "mixed"):
    run_concurrency_test(url, concurrent_requests, mode)

# 运行并发测试，通用函数
def run_concurrency_test(url: str, concurrent_requests: int, mode: str):
    start_time = time.time()
    success_count = 0
    responses = []

    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = []
        for _ in range(concurrent_requests):
            if mode == "stream":
                futures.append(executor.submit(handle_request, url, stream_body, True))
            elif mode == "non-stream":
                futures.append(executor.submit(handle_request, url, body, False))
            else:  # mixed mode
                if random.choice([True, False]):
                    futures.append(executor.submit(handle_request, url, stream_body, True))
                else:
                    futures.append(executor.submit(handle_request, url, body, False))

        for future in as_completed(futures):
            result = future.result()
            """
            报文内容如下，表示请求失败
            ```txt
            {"message":"Too many concurrent requests\n token: q7r8s9t0-u1v2-w3x4-y5z6-a7b8c9d0e1f2, current_request_num:8, request_limit:8\n"}
            ```

            报文内容满足openai的接口响应格式，表示请求成功
            ```txt
            {"id": "cmpl-387ed060141a4b0886e82f9de7546356", "object": "chat.completion", "created": 2321295, "model": "qwen1.5-32b-chat-int4", "choices": [{"index": 0, "message": {"role": "assistant", "content": "当然，下面是一个简短却寓意深刻的故事：\n\n在浩渺的森林中，有一只骄傲的孔雀，它的羽毛五彩斑斓，美得令人惊叹。每天，孔雀都会在森林里展示自己的羽毛，希望得到其他动物的赞美。所有的动物都为它的美丽而惊叹，但都默默欣赏，偶尔轻声赞叹。\n\n有一天，森林里来了一只平凡的乌鸦。孔雀看到乌鸦，嘲笑它全身漆黑，毫无美丽可言。乌鸦并没有生气，它只是飞到孔雀身边，说：“孔雀，你的羽毛确实美丽，可是我听说，真正美丽的是那些乐于助人的心。在这个世界上，外表的美丽固然重要，但是内心的善良和乐于助人，才是永恒的美。”\n\n孔雀听后，感到惭愧。从那以后，孔雀不仅以它的羽毛为傲，更以帮助其他动物，传递善良和爱心为荣。它明白了，真正的美丽，不仅仅是外在的璀璨，更是内心的善良和对他人的关爱。\n\n这个故事告诉我们，美并不仅仅在于外表，更重要的是内在的品质和对他人的关爱。"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 27, "total_tokens": 259, "completion_tokens": 232}}
            ```
            """
            try:
                response = json.loads(result)
                if "id" in response and "object" in response and response["object"] == "chat.completion":
                    success_count += 1
                else:
                    # Handle the failure case if needed
                    pass
            except json.JSONDecodeError:
                # Handle the case where the result is not a valid JSON
                pass

            responses.append(result)


    duration = time.time() - start_time
    success_rate = (success_count / concurrent_requests) * 100

    logging.info(f"Concurrent requests: {concurrent_requests}, "
                 f"Duration: {duration:.2f} seconds, "
                 f"Success Rate: {success_rate:.2f}%")

    print(f"Concurrent requests: {concurrent_requests}, Duration: {duration:.2f} seconds, Success Rate: {success_rate:.2f}%")

    # 将所有响应内容写入 test_response.txt 文件
    with open('test_response.txt', 'w', encoding='utf-8') as f:
        for response in responses:
            f.write(f"{response}\n\n")

# 主程序入口
if __name__ == "__main__":
    _, server_params, llm_params, _ = return_config()
    ip = "20.20.136.251"
    port = server_params["PORT"]

    url = f"http://{ip}:{port}/v1/chat/completions"
    max_concurrency = 12
    test_mode = "non-stream"  # 可选: "stream", "non-stream", "mixed"
    test_concurrency_fix(url, max_concurrency, test_mode)  # 进行并发测试
