import requests

# 1. 注册（JSON 格式，这个没问题）
reg = requests.post("http://localhost:8000/auth/register", json={"username": "pytest", "password": "pypass"})
print("Register:", reg.status_code, reg.text)

# 2. 登录 - 改为 data= 发送表单格式
login_data = {"username": "pytest", "password": "pypass"}
login = requests.post("http://localhost:8000/auth/login", data=login_data)   # 关键：data= 而不是 json=
print("Login:", login.status_code)
if login.status_code != 200:
    print("Login failed:", login.text)
    exit()

token = login.json()["access_token"]
print("Token:", token)

# 3. 添加 API Key（JSON 格式）
headers = {"Authorization": f"Bearer {token}"}
add_key = requests.post("http://localhost:8000/keys", headers=headers, json={"key_value": "sk-test456"})
print("Add Key:", add_key.status_code, add_key.text)