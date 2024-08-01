import os
import json
import uuid
from flask import Flask, request, jsonify, abort
import requests
import logging
from functools import wraps

app = Flask(__name__)

# 配置日志
log_file = 'service.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

TOKEN_FILE = 'tokens.json'

# 读取token文件
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# 保存token文件
def save_tokens(tokens):
    with open(TOKEN_FILE, 'w', encoding='utf-8') as file:
        json.dump(tokens, file, ensure_ascii=False)

# 生成新的token
@app.route('/generate_token', methods=['POST'])
def generate_token():
    new_token = str(uuid.uuid4())
    tokens = load_tokens()
    tokens[new_token] = True
    save_tokens(tokens)
    logging.info(f'Generated new token: {new_token}')
    return jsonify({'token': new_token})

# Token认证装饰器
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            logging.warning('Token is missing!')
            return jsonify({'message': 'Token is missing!'}), 401
        tokens = load_tokens()
        if token not in tokens:
            logging.warning('Invalid Token!')
            return jsonify({'message': 'Invalid Token!'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/proxy', methods=['POST'])
@token_required
def proxy():
    data = request.json
    logging.info(f'Received request data: {data}')

    headers = {
        # 'Authorization': f'Bearer {your_openai_api_key}', # 请替换成你的实际OpenAI API key
        'Content-Type': 'application/json'
    }
    try:
        # response = requests.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
        response = requests.post('http://www.loveatcorner.com.cn/interface', json=data, headers=headers)
        logging.info(f'Response status: {response.status_code}')
        logging.info(f'Response data: {response.json()}')
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        logging.error(f'Error during request: {e}')
        return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
