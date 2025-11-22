from openai import AsyncOpenAI
import itertools
import asyncio
import json
import asyncio
import random
from typing import Any, List, Sequence, Tuple
import asyncio
import nest_asyncio


class MultiKeyClientPool:
    def __init__(self, api_keys, base_url="https://integrate.api.nvidia.com/v1"):
        self.clients = [
            AsyncOpenAI(base_url=base_url, api_key=k)
            for k in api_keys
        ]
        self._cycle = itertools.cycle(self.clients)

    def get(self):
        return next(self._cycle)


import asyncio
from typing import Any, Iterable, List, Sequence, Tuple, Optional
from threading import Thread

class AllKeysFailed(RuntimeError):
    pass

async def _safe_ask_one(
    client_pool,
    model: str,
    messages: Sequence[dict],
    temperature: float = 1.0,
    top_p: float = 0.95,
    max_tokens: int = 1024,
) -> Any:
    """
    单条请求的容错发送。按 client_pool 轮询，直到有一个成功为止。
    """
    n = len(client_pool.clients)
    last_err: Optional[Exception] = None
    for _ in range(n):
        client = client_pool.get()
        try:
            tmp = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            return tmp
        except Exception as e:
            last_err = e
            # 失败就试下一个 key
            continue
    raise AllKeysFailed(f"All API keys failed. last_error={last_err}")

async def safe_ask_batch(
    client_pool,
    batch_messages: Sequence[Sequence[dict]],
    model: str,
    temperature: float = 1.0,
    top_p: float = 0.95,
    max_tokens: int = 1024,
    concurrency: int = 8,
) -> List[Any]:
    """
    批量发送。保持结果顺序与 batch_messages 一致。
    """
    sem = asyncio.Semaphore(concurrency)
    results: List[Optional[Any]] = [None] * len(batch_messages)

    async def _runner(idx: int, msgs: Sequence[dict]) -> None:
        async with sem:
            resp = await _safe_ask_one(
                client_pool=client_pool,
                model=model,
                messages=msgs,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            results[idx] = resp.choices[0].message.content

    tasks = [asyncio.create_task(_runner(i, msgs)) for i, msgs in enumerate(batch_messages)]
    # 如果你希望任何一个失败就立刻抛出，可以不捕获异常
    await asyncio.gather(*tasks)
    # 类型收窄
    return [r for r in results]  # type: ignore

# ---------------- 同步封装 ----------------

def _run_coro_in_new_loop(coro):
    """
    在新线程里起一个全新的事件循环。适用于当前线程已经有运行中的事件循环的场景
    比如在 Jupyter 或其他异步环境中。
    """
    out: dict = {}
    exc: dict = {}

    def _target():
        try:
            out["value"] = asyncio.run(coro)
        except Exception as e:
            exc["error"] = e

    t = Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if "error" in exc:
        raise exc["error"]
    return out.get("value")

def ask_batch(
    client_pool,
    batch_messages: Sequence[Sequence[dict]],
    model: str,
    temperature: float = 1.0,
    top_p: float = 0.95,
    max_tokens: int = 2048,
    concurrency: int = 8,
) -> List[Any]:
    """
    同步函数。可在普通函数里直接调用。内部自动处理是否已有事件循环在运行。
    """
    coro = safe_ask_batch(
        client_pool=client_pool,
        batch_messages=batch_messages,
        model=model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        concurrency=concurrency,
    )
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 已在异步环境中。使用新线程创建独立事件循环
        return _run_coro_in_new_loop(coro)
    else:
        # 普通同步环境
        return asyncio.run(coro)


# async def safe_ask(client_pool, model, messages, temperature=1.0, top_p=0.95, max_tokens=1024):
#     for _ in range(len(client_pool.clients)):
#         client = client_pool.get()
#         # print(f"Using client with API key: {client.api_key}, {client.base_url}")
#         try:
#             return await client.chat.completions.create(
#                 model=model,
#                 messages=messages,
#                 temperature=temperature,
#                 top_p=top_p,
#                 max_tokens=max_tokens,
#             )
#         except Exception as e:
#             print(f"Key failed, try next. error={e}")
#     raise RuntimeError("All API keys failed")


def safe_ask(client_pool, model, messages, temperature=1.0, top_p=0.95, max_tokens=1024):
    for _ in range(len(client_pool.clients)):
        client = client_pool.get()
        # print(f"Using client with API key: {client.api_key}, {client.base_url}")
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
        except Exception as e:
            print(f"Key failed, try next. error={e}")
    raise RuntimeError("All API keys failed")


async def safe_embed(client_pool, model="baai/bge-m3", messages=None, temperature=1.0, top_p=0.95, max_tokens=1024):
    for _ in range(len(client_pool.clients)):
        client = client_pool.get()
        try:
            return await client.embeddings.create(
                input=messages,
                model=model,
                encoding_format="float",
                extra_body={"input_type": "query", "truncate": "NONE"}
            )
        except Exception as e:
            print(f"Key failed, try next. error={e}")
    raise RuntimeError("All API keys failed")


if __name__ == "__main__":
    with open("api.json") as f:
        api_data = json.load(f)
    client_pool = MultiKeyClientPool(api_data["api_keys"])
    # Example usage of safe_ask and safe_embed can be added here for testing purposes.
    safe_ask_example = ask_batch(
        client_pool,
        model="qwen/qwen2-7b-instruct",
        batch_messages=[[{"role": "user", "content": "Hello, world!"}], [{"role": "user", "content": "fuvk you ass!"}]],
    )
    print(safe_ask_example)
    # for i, r in enumerate(safe_ask_example):
    #     print(i, r.choices[0].message.content)