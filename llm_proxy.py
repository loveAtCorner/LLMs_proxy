import uuid
import requests
from functools import wraps
import threading


from flask import Flask, request, jsonify, Response

from log import make_log
from utils import *


lock = threading.Lock()


app = Flask(__name__)

# 生成新的token
@app.route("/generate_token", methods=["POST"])
def generate_token():
    request_data = request.json
    request_pwd = request_data.get("pwd", "")
    request_num = request_data.get("max_request_num", 5)
    max_mult_num = 10 # 每个用户设置的token最大请求数不能超过10

    assert request_pwd == token_params["MANAGER_PWD"], "PWD is wrong!"
    assert request_num <= max_mult_num, f"The maximum number of token requests set by each user cannot exceed {max_mult_num}."


    new_token = str(uuid.uuid4())
    token_limits[new_token] = request_num
    save_tokens(token_limits, token_params["TOKEN_FILE"])
    logger.info(f"Generated new token: {new_token}")
    return jsonify({"token": new_token, "max_request_num": request_num})


# 显示所有的token
@app.route("/list_tokens", methods=["POST"])
def list_tokens():
    request_data = request.json
    request_pwd = request_data.get("pwd", "")

    assert request_pwd == token_params["MANAGER_PWD"], "PWD is wrong!"

    # 返回所有 token 及其对应的请求数限制
    token_list = [{"token": token, "request_limit_num": limit} for token, limit in token_limits.items()]
    logger.info(f"Listed all tokens: {token_list}")

    return jsonify(token_list)


# 删除token
@app.route("/delete_token", methods=["POST"])
def delete_token():
    request_data = request.json
    request_pwd = request_data.get("pwd", "")
    token_to_delete = request_data.get("token", "")

    assert request_pwd == token_params["MANAGER_PWD"], "PWD is wrong!"
    assert token_to_delete in token_limits, "Token not found!"

    # 删除 token
    del token_limits[token_to_delete]
    save_tokens(token_limits, token_params["TOKEN_FILE"])
    logger.info(f"Deleted token: {token_to_delete}")

    return jsonify({"message": "Token deleted successfully"})




# Token认证装饰器
def token_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        authorization = request.headers.get("Authorization")
        token = authorization.split()[1] if len(authorization.split()) > 1 else None
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        if token not in token_limits.keys():
            return jsonify({"message": "Invalid Token!"}), 403

        with lock:
            if token_counts[token] >= token_limits[token]:
                return jsonify({f"message": f"Too many concurrent requests\n token: {token}, current_request_num:{token_counts[token]}, request_limit:{token_limits[token]}\n"}), 429
            else:
                token_counts[token] += 1
        try:
            return func(*args, **kwargs)
        finally:
            with lock:
                token_counts[token] -= 1
    return decorated_function


@app.route("/v1/chat/completions", methods=["POST"])
@token_required
def proxy():
    data = request.json
    logger.info(f'Received request data: {data}')

    authorization = request.headers.get("Authorization", "")
    is_stream: bool = data.get("stream", False)

    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json'
    }
    try:
        if is_stream:
            response = requests.post(llm_params["OPENAI_URL"], json=data, headers=headers, stream=is_stream)
            return Response(response)
        else:
            response = requests.post(llm_params["OPENAI_URL"], json=data, headers=headers)
            return Response(json.dumps(response.json(), ensure_ascii=False), content_type='application/json')
    except requests.exceptions.RequestException as e:
        logger.error(f'Error during request: {e}')
        return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    log_params, server_params, llm_params, token_params = return_config()
    logger = make_log(log_params)
    token_limits = load_tokens(token_params["TOKEN_FILE"])
    token_counts = {token: 0 for token in token_limits}

    app.run(host=server_params["IP"], port=server_params["PORT"])