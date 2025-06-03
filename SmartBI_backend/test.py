import requests
import json

def test_create_user():
    url = "http://localhost:8000/api/v1/users/"
    
    # 测试数据
    user_data = {
        "username": "测试用户",
        "userAccount": "testuser",
        "userPassword": "testpassword123",
        "email": "test@example.com",
        "phone": "13800138000",
        "gender": 1,
        "avatarUrl": "https://example.com/avatar.jpg"
    }
    
    # 发送POST请求
    response = requests.post(url, json=user_data)
    
    # 打印响应
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_get_users():
    url = "http://localhost:8000/api/v1/users/"
    
    # 发送GET请求
    response = requests.get(url)
    
    # 打印响应
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("测试用户创建:")
    test_create_user()
    
    print("\n测试获取用户列表:")
    test_get_users() 