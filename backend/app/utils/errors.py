"""
统一错误处理工具

问题背景：API 端点中存在 60+ 处 `except Exception as e:` 直接把
`str(e)` 与 `traceback.format_exc()` 通过 JSON 返回给客户端，会泄漏
内部实现细节（文件路径、第三方库异常、潜在凭据片段等）。

本模块提供：
- ApiError：业务层可主动抛出的、面向客户端的友好错误
- safe_response：把异常转成不泄漏堆栈的 JSON 响应（堆栈仅写入服务器日志）
- register_error_handlers：注册 Flask 全局兜底处理器，确保任何未被捕获的
  异常都不会把 traceback 透传到前端
"""

from __future__ import annotations

import traceback
from typing import Tuple

from flask import Flask, jsonify

from .logger import get_logger

_logger = get_logger('mirofish.errors')


class ApiError(Exception):
    """业务层主动抛出的、面向客户端的可控错误。

    与未捕获的 Exception 不同：ApiError 的 message 会原样返回给客户端，
    因此调用方应保证消息中不含敏感信息。
    """

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def safe_response(exc: BaseException, *, log_prefix: str = '') -> Tuple[dict, int]:
    """把异常转成 (json_dict, status_code)，堆栈只入日志。"""
    if isinstance(exc, ApiError):
        # 业务异常：原文返回
        return {"success": False, "error": exc.message}, exc.status_code
    if isinstance(exc, ValueError):
        # 参数校验类异常：可以把消息透传（来源是开发者编写的校验代码）
        return {"success": False, "error": str(exc)}, 400
    if isinstance(exc, FileNotFoundError):
        return {"success": False, "error": "Resource not found"}, 404
    if isinstance(exc, PermissionError):
        return {"success": False, "error": "Permission denied"}, 403

    # 兜底：记录详细日志，仅返回通用消息给客户端
    _logger.error(
        f"{log_prefix}未处理异常: {type(exc).__name__}: {exc}\n"
        f"{traceback.format_exc()}"
    )
    return {"success": False, "error": "Internal server error"}, 500


def register_error_handlers(app: Flask) -> None:
    """注册全局错误处理器。

    覆盖三类：
    1. ApiError 显式业务异常 → 客户端可信任的错误消息
    2. HTTPException → 保留 Werkzeug 的状态码，但用统一 JSON 格式
    3. 其它一切异常 → 通用 500，堆栈只入日志
    """
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(ApiError)
    def _handle_api_error(e: ApiError):
        body, status = safe_response(e)
        return jsonify(body), status

    @app.errorhandler(HTTPException)
    def _handle_http_exception(e: HTTPException):
        # 不泄漏 Werkzeug 的默认 HTML 错误页；保留状态码
        return jsonify({
            "success": False,
            "error": e.name or "HTTP error",
        }), e.code or 500

    @app.errorhandler(Exception)
    def _handle_unexpected(e: Exception):
        body, status = safe_response(e, log_prefix='[global] ')
        return jsonify(body), status
