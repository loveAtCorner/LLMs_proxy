import uuid
import requests
from functools import wraps
import threading

from flask import Flask, request, jsonify, Response

from log import make_log
from utils import *

# 使用线程锁来保护token请求计数的并发安全性
lock = threading.Lock()

# 创建Flask应用实例
app = Flask(__name__)

# 生成新的token
@app.route("/generate_token", methods=["POST"])
def generate_token():
    # 从请求中获取数据
    request_data = request.json
    request_pwd = request_data.get("pwd", "")
    request_num = request_data.get("max_request_num", 5)
    max_mult_num = 10  # 每个用户设置的token最大请求数不能超过10

    # 验证管理员密码是否正确
    assert request_pwd == token_params["MANAGER_PWD"], "PWD is wrong!"
    # 验证请求数是否超过最大限制
    assert request_num <= max_mult_num, f"The maximum number of token requests set by each user cannot exceed {max_mult_num}."

    # 生成新的UUID作为token
    new_token = str(uuid.uuid4())
    # 将token和请求数限制存储在token_limits字典中
    token_limits[new_token] = request_num
    # 保存更新后的token_limits到文件中
    save_tokens(token_limits, token_params["TOKEN_FILE"])
    # 记录生成的token
    logger.info(f"Generated new token: {new_token}")
    # 返回生成的token和请求数限制
    return jsonify({"token": new_token, "max_request_num": request_num})

# 显示所有的token
@app.route("/list_tokens", methods=["POST"])
def list_tokens():
    # 从请求中获取数据
    request_data = request.json
    request_pwd = request_data.get("pwd", "")

    # 验证管理员密码是否正确
    assert request_pwd == token_params["MANAGER_PWD"], "PWD is wrong!"

    # 返回所有 token 及其对应的请求数限制
    token_list = [{"token": token, "request_limit_num": limit} for token, limit in token_limits.items()]
    # 记录列出的token信息
    logger.info(f"Listed all tokens: {token_list}")

    # 返回token列表
    return jsonify(token_list)

# 删除token
@app.route("/delete_token", methods=["POST"])
def delete_token():
    # 从请求中获取数据
    request_data = request.json
    request_pwd = request_data.get("pwd", "")
    token_to_delete = request_data.get("token", "")

    # 验证管理员密码是否正确
    assert request_pwd == token_params["MANAGER_PWD"], "PWD is wrong!"
    # 验证要删除的token是否存在
    assert token_to_delete in token_limits, "Token not found!"

    # 删除指定的token
    del token_limits[token_to_delete]
    # 保存更新后的token_limits到文件中
    save_tokens(token_limits, token_params["TOKEN_FILE"])
    # 记录删除的token信息
    logger.info(f"Deleted token: {token_to_delete}")

    # 返回删除成功的消息
    return jsonify({"message": "Token deleted successfully"})

# Token认证装饰器，用于验证请求中的token并控制请求次数
def token_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 从请求头中获取Authorization信息
        authorization = request.headers.get("Authorization")
        token = authorization.split()[1] if len(authorization.split()) > 1 else None
        # 如果没有token，则返回401错误
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        # 如果token无效，则返回403错误
        if token not in token_limits.keys():
            return jsonify({"message": "Invalid Token!"}), 403

        with lock:
            # 如果token的并发请求数超过限制，则返回429错误
            if token_counts[token] >= token_limits[token]:
                return jsonify({f"message": f"Too many concurrent requests\n token: {token}, current_request_num:{token_counts[token]}, request_limit:{token_limits[token]}\n"}), 429
            else:
                # 增加当前token的请求计数
                token_counts[token] += 1
        try:
            # 执行被装饰的函数
            return func(*args, **kwargs)
        finally:
            with lock:
                # 在请求处理完成后，减少当前token的请求计数
                token_counts[token] -= 1
    return decorated_function

# 请求代理，用于代理请求到外部API
@app.route("/v1/chat/completions", methods=["POST"])
@token_required
def proxy():
    # 获取请求体中的数据
    data = request.json
    # 记录收到的请求数据
    logger.info(f'Received request data: {data}')

    # 从请求头中获取Authorization信息
    authorization = request.headers.get("Authorization", "")
    # 判断是否为流式请求
    is_stream: bool = data.get("stream", False)

    # 设置请求头
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }
    try:
        # 如果是流式请求，直接代理请求并返回响应
        if is_stream:
            response = requests.post(llm_params["OPENAI_URL"], json=data, headers=headers, stream=is_stream)
            return Response(response)
        else:
            # 否则，代理请求并将响应转换为JSON格式返回
            response = requests.post(llm_params["OPENAI_URL"], json=data, headers=headers)
            return Response(json.dumps(response.json(), ensure_ascii=False), content_type='application/json')
    except requests.exceptions.RequestException as e:
        # 捕获请求异常并记录日志
        logger.error(f'Error during request: {e}')
        # 返回500错误
        return jsonify({'message': 'Internal server error'}), 500

# 启动Flask应用
if __name__ == '__main__':
    # 加载配置文件中的参数
    log_params, server_params, llm_params, token_params = return_config()
    # 创建日志记录器
    logger = make_log(log_params)
    # 加载token信息
    token_limits = load_tokens(token_params["TOKEN_FILE"])
    # 初始化token请求计数为0
    token_counts = {token: 0 for token in token_limits}

    # 启动Flask应用
    app.run(host=server_params["IP"], port=server_params["PORT"])
