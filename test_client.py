import requests
import yaml

# 从配置文件中读取配置
def load_config(config_file='config.yaml'):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

config = load_config()
BASE_URL = config['base_url']
data = config['data']

def test_generate_token():
    print("Testing /generate_token route...")
    response = requests.post(f'{BASE_URL}/generate_token')
    if response.status_code == 200:
        token = response.json().get('token')
        print(f'Successfully generated token: {token}')
        return token
    else:
        print(f'Failed to generate token: {response.status_code} - {response.text}')
        return None

def test_proxy_with_valid_token(token):
    print("\nTesting /proxy route with valid token...")
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    response = requests.post(f'{BASE_URL}/proxy', json=data, headers=headers)
    if response.status_code == 200:
        print('Successfully accessed proxy route with valid token:')
        print('Response:', response.json())
    else:
        print(f'Failed to access proxy with valid token: {response.status_code} - {response.text}')

def test_proxy_with_no_token():
    print("\nTesting /proxy route with no token...")
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(f'{BASE_URL}/proxy', json=data, headers=headers)
    if response.status_code == 401:
        print('Correctly handled missing token:')
        print('Response:', response.json())
    else:
        print(f'Failed to handle missing token: {response.status_code} - {response.text}')

def test_proxy_with_invalid_token():
    print("\nTesting /proxy route with invalid token...")
    headers = {
        'Authorization': 'invalid-token',
        'Content-Type': 'application/json'
    }
    response = requests.post(f'{BASE_URL}/proxy', json=data, headers=headers)
    if response.status_code == 403:
        print('Correctly handled invalid token:')
        print('Response:', response.json())
    else:
        print(f'Failed to handle invalid token: {response.status_code} - {response.text}')

if __name__ == '__main__':
    # 测试生成Token的路由
    token = test_generate_token()
    if token:
        # 使用生成的Token测试代理路由
        test_proxy_with_valid_token(token)
    else:
        print("Cannot test /proxy route without a valid token.")
    
    # 测试没有Token的情况
    test_proxy_with_no_token()
    
    # 测试错误Token的情况
    test_proxy_with_invalid_token()
