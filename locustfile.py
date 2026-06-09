from locust import HttpUser, task, between, events
import random
import uuid

class ApiFarmUser(HttpUser):
    wait_time = between(0.5, 2)   # 模拟用户思考时间
    
    def on_start(self):
        # 每个虚拟用户独立注册并登录
        self.username = f"perf_{uuid.uuid4().hex[:8]}"
        self.password = "test123"
        # 注册
        self.client.post("/auth/register", json={"username": self.username, "password": self.password})
        # 登录
        resp = self.client.post("/auth/login", data={"username": self.username, "password": self.password})
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        # 添加一个测试 API Key（使用随机值）
        self.client.post("/keys/", json={"key_value": f"sk-perf-{uuid.uuid4()}"}, headers=self.headers)
    
    @task(10)
    def chat_completion(self):
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        with self.client.post("/chat/completions", json=payload, headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 429:
                # 限流符合预期，标记为成功
                resp.success()
            elif resp.status_code != 200:
                resp.failure(f"Unexpected status code: {resp.status_code}")
    
    @task(1)
    def list_keys(self):
        self.client.get("/keys/", headers=self.headers)
    
    @task(2)
    def create_order(self):
        # 先获取有效计划
        plans = self.client.get("/plans").json()
        if plans:
            plan_id = plans[0]["id"]
            self.client.post("/orders/create", params={"plan_id": plan_id}, headers=self.headers)
    
    @task(0)
    def trigger_failure(self):
        # 模拟调用一个会返回 500 的上游（需要后端支持，这里仅占位）
        pass

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=== Performance test started ===")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=== Performance test finished ===")