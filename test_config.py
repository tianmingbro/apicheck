import requests
r = requests.post("http://localhost:8000/auth/register", json={"username":"test","password":"test"})
print(r.status_code, r.text)