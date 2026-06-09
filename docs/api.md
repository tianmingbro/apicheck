API Key 管理

所有端点需要认证。
GET /keys/

列出当前用户的所有 API Key（脱敏显示）。

响应：
json

[
  {
    "id": 1,
    "key": "sk-proj***********abc123",
    "base_url": null,
    "is_enabled": true,
    "created_at": "2025-01-01T00:00:00",
    "total_calls": 42,
    "last_used_at": "2025-01-02T10:00:00"
  }
]

POST /keys/

添加新的 API Key（加密存储）。

请求体：
json

{
  "key_value": "sk-xxxxxxxxxxxx",
  "base_url": "https://api.openai.com/v1"   // 可选
}

响应：同 GET 返回的单个对象。
DELETE /keys/{key_id}

删除指定 API Key。

响应：
json

{
  "message": "API Key deleted successfully"
}

聊天代理
POST /chat/completions

代理请求到上游大模型 API（OpenAI 兼容格式）。

请求体（示例）：
json

{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 150
}

响应（上游返回格式）：
json

{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hi there!"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}

可能的状态码：

    200：成功

    401：未认证或 token 无效

    402：配额不足

    503：无可用的 API Key

    504：上游超时

    4xx/5xx：上游返回的错误

健康检查
GET /health

检查服务状态。

响应：
json

{
  "status": "ok",
  "version": "0.1.0"
}

错误响应格式

所有错误响应均符合以下格式：
json

{
  "detail": "具体的错误描述"
}

限流说明

（如已实现）API 限流信息通过响应头返回：

    X-RateLimit-Limit

    X-RateLimit-Remaining

    X-RateLimit-Reset

更多信息

完整的交互式文档请访问 /docs 或 /redoc。