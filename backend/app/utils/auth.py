"""
API 认证 + 速率限制中间件

设计目标：
- 零额外依赖：不引入 flask-limiter / Redis，单进程内存计数即可覆盖单实例部署
- 默认安全 + 兼容：若 API_KEYS 未配置则放行（保留本地开发体验），但日志会
  提示风险；生产部署时配置 API_KEYS 即立刻启用强制认证。
- 健康检查 (/health) 与 OPTIONS 预检不受限。

如需横向扩展或更精细策略（按路由限流、滑动窗口共享），后续应替换为
flask-limiter + 共享存储；本模块的接口保持不变。
"""

from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from flask import Flask, request, jsonify

from .logger import get_logger

logger = get_logger('mirofish.auth')

# 在全部认证检查中豁免的路径前缀
_EXEMPT_PATHS = ('/health',)

# 60 秒滑动窗口
_WINDOW_SECONDS = 60.0


class _SlidingWindowCounter:
    """按 key 维护的简单滑动窗口计数器。线程安全。"""

    def __init__(self, max_requests: int, window_seconds: float = _WINDOW_SECONDS):
        self._max = max_requests
        self._window = window_seconds
        self._lock = threading.Lock()
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def check_and_record(self, key: str) -> bool:
        """如果未超限则记录一次访问并返回 True；否则返回 False。"""
        if self._max <= 0:
            return True  # 限流被禁用
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            bucket = self._buckets[key]
            # 移除超出窗口的旧记录
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max:
                return False
            bucket.append(now)
            return True


def _extract_api_key() -> Optional[str]:
    """从 X-API-Key 头或 Authorization: Bearer xxx 提取 key。"""
    key = request.headers.get('X-API-Key')
    if key:
        return key.strip()
    auth = request.headers.get('Authorization', '')
    if auth.lower().startswith('bearer '):
        return auth[7:].strip()
    return None


def _client_identifier() -> str:
    """用于限流的客户端标识：优先 API key（命中即可信任），否则远端地址。"""
    key = _extract_api_key()
    if key:
        # 仅使用前 8 字符作为标识，避免日志泄漏完整密钥
        return f"key:{key[:8]}"
    # X-Forwarded-For 可被伪造；只在配置受信代理时才使用，此处只用 remote_addr
    return f"ip:{request.remote_addr or 'unknown'}"


def install_auth_and_rate_limit(app: Flask) -> None:
    """在 Flask 应用上注册 API 认证 + 速率限制 before_request 钩子。

    必须在蓝图注册之后调用。
    """
    api_keys = set(app.config.get('API_KEYS') or [])
    rate_limit = app.config.get('RATE_LIMIT_PER_MINUTE', 0) or 0
    debug_mode = bool(app.config.get('DEBUG', False))

    if not api_keys:
        if debug_mode:
            logger.warning(
                "API_KEYS 未配置，/api/* 端点对所有调用方开放。仅适合本地开发。"
            )
        else:
            logger.error(
                "API_KEYS 未配置且 DEBUG=False，/api/* 端点将无认证保护！"
                "强烈建议在 .env 中设置 API_KEYS。"
            )

    counter = _SlidingWindowCounter(max_requests=rate_limit)

    @app.before_request
    def _enforce_auth_and_rate_limit():
        path = request.path or ''
        # 仅对 /api/ 前缀生效
        if not path.startswith('/api/'):
            return None
        # 豁免健康检查与 CORS 预检
        if request.method == 'OPTIONS':
            return None
        if any(path.startswith(p) for p in _EXEMPT_PATHS):
            return None

        # 1) 认证（仅当配置了 API_KEYS 时）
        if api_keys:
            provided = _extract_api_key()
            if not provided or provided not in api_keys:
                logger.warning(
                    f"未授权访问被拒绝: {request.method} {path} from {request.remote_addr}"
                )
                return jsonify({
                    "success": False,
                    "error": "Unauthorized: missing or invalid API key"
                }), 401

        # 2) 限流
        client = _client_identifier()
        if not counter.check_and_record(client):
            logger.warning(f"速率限制触发: {client} on {path}")
            return jsonify({
                "success": False,
                "error": "Too Many Requests",
                "retry_after_seconds": int(_WINDOW_SECONDS),
            }), 429

        return None
