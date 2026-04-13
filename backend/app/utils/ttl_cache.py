"""
轻量的线程安全 TTL 缓存

为 Zep / 数据库等慢速外部调用提供短周期的结果缓存，避免同一实体 / 图谱
在短时间内被前端多次拉取时产生 N 倍的后端往返。

设计原则：
- 纯 Python，无第三方依赖（不引入 cachetools / Redis）
- 按 key 粒度可单独失效，便于写入后立即 invalidate
- 最大条目数上限防止缓存无限增长（LRU 近似——满时按插入顺序淘汰一半）
- 所有操作带锁；单进程多线程场景下安全
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional


class TTLCache:
    def __init__(self, *, ttl_seconds: float = 30.0, max_size: int = 512):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds 必须大于 0")
        if max_size <= 0:
            raise ValueError("max_size 必须大于 0")
        self._ttl = ttl_seconds
        self._max = max_size
        self._lock = threading.RLock()
        # key -> (expires_at_monotonic, value)
        self._store: dict = {}

    def _now(self) -> float:
        return time.monotonic()

    def get(self, key: Any) -> Optional[Any]:
        """返回缓存值；过期或不存在则返回 None（命中但 None 值使用 get_or_load）。"""
        now = self._now()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires, value = entry
            if expires <= now:
                # 过期：清理后返回 None
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: Any, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self._max and key not in self._store:
                # 超容量：近似 LRU 地砍掉最旧的一半
                # dict 在 Python 3.7+ 保序，所以前面的 key 就是较早插入的
                victims = list(self._store.keys())[: self._max // 2]
                for k in victims:
                    self._store.pop(k, None)
            self._store[key] = (self._now() + self._ttl, value)

    def invalidate(self, key: Any) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def get_or_load(self, key: Any, loader: Callable[[], Any]) -> Any:
        """经典 cache-aside：命中直接返回；未命中调 loader() 并缓存结果。

        注意：loader 在锁外调用，以避免慢速下游阻塞其它 key 的访问。同一
        key 短时间内并发穿透会触发重复加载（'dogpile'），这是可接受的
        简化——如需严格去重可替换为 per-key lock；当前预期访问模式
        （前端轮询同一 graph_id）不会造成显著放大。
        """
        cached = self.get(key)
        if cached is not None:
            return cached
        value = loader()
        # 允许缓存 None/empty 值以避免反复请求失败的下游
        self.set(key, value)
        return value
