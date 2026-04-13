"""
backend/app/utils/errors.py 的单元测试 — 仅校验 safe_response 的纯函数行为，
不启动 Flask 应用。
"""

from app.utils.errors import ApiError, safe_response


def test_api_error_passes_message_through():
    body, status = safe_response(ApiError("invalid graph", status_code=422))
    assert status == 422
    assert body == {"success": False, "error": "invalid graph"}


def test_value_error_returns_400_with_message():
    body, status = safe_response(ValueError("bad input"))
    assert status == 400
    assert body == {"success": False, "error": "bad input"}


def test_file_not_found_returns_404_generic():
    body, status = safe_response(FileNotFoundError("/tmp/secret/path"))
    assert status == 404
    assert body == {"success": False, "error": "Resource not found"}
    # The sensitive file path must not leak to the client body
    assert "/tmp/secret/path" not in body["error"]


def test_permission_error_returns_403_generic():
    body, status = safe_response(PermissionError("denied: /etc/shadow"))
    assert status == 403
    assert "/etc/shadow" not in body["error"]


def test_unexpected_exception_does_not_leak_internals():
    class WeirdInternal(RuntimeError):
        pass

    body, status = safe_response(WeirdInternal("connstr=postgres://user:pw@host/db"))
    assert status == 500
    assert body == {"success": False, "error": "Internal server error"}
    # Sensitive details must stay in logs only
    assert "postgres://" not in body["error"]
    assert "WeirdInternal" not in body["error"]
