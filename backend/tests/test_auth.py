"""
backend/app/utils/auth.py 中 _SlidingWindowCounter 的单元测试。

不依赖 Flask 应用。
"""

import time

from app.utils.auth import _SlidingWindowCounter


def test_allows_within_limit():
    c = _SlidingWindowCounter(max_requests=3, window_seconds=60)
    assert c.check_and_record('client1') is True
    assert c.check_and_record('client1') is True
    assert c.check_and_record('client1') is True


def test_blocks_when_exceeded():
    c = _SlidingWindowCounter(max_requests=2, window_seconds=60)
    assert c.check_and_record('client1') is True
    assert c.check_and_record('client1') is True
    assert c.check_and_record('client1') is False


def test_buckets_isolated_per_key():
    c = _SlidingWindowCounter(max_requests=1, window_seconds=60)
    assert c.check_and_record('a') is True
    assert c.check_and_record('a') is False
    # client b should still get its own quota
    assert c.check_and_record('b') is True


def test_disabled_when_max_zero():
    c = _SlidingWindowCounter(max_requests=0, window_seconds=60)
    for _ in range(100):
        assert c.check_and_record('x') is True


def test_window_recovers_after_expiry():
    c = _SlidingWindowCounter(max_requests=1, window_seconds=0.05)
    assert c.check_and_record('x') is True
    assert c.check_and_record('x') is False
    time.sleep(0.08)
    assert c.check_and_record('x') is True
