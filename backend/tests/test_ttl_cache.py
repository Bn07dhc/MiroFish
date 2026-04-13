"""
backend/app/utils/ttl_cache.py 的单元测试。
"""

import time

import pytest

from app.utils.ttl_cache import TTLCache


def test_get_returns_set_value():
    c = TTLCache(ttl_seconds=60, max_size=10)
    c.set('k', {'a': 1})
    assert c.get('k') == {'a': 1}


def test_missing_key_returns_none():
    c = TTLCache(ttl_seconds=60, max_size=10)
    assert c.get('missing') is None


def test_expired_entry_returns_none():
    c = TTLCache(ttl_seconds=0.05, max_size=10)
    c.set('k', 'v')
    time.sleep(0.08)
    assert c.get('k') is None


def test_invalidate_removes_entry():
    c = TTLCache(ttl_seconds=60, max_size=10)
    c.set('k', 'v')
    c.invalidate('k')
    assert c.get('k') is None


def test_get_or_load_caches_miss():
    c = TTLCache(ttl_seconds=60, max_size=10)
    calls = {'n': 0}

    def loader():
        calls['n'] += 1
        return 'loaded'

    assert c.get_or_load('k', loader) == 'loaded'
    assert c.get_or_load('k', loader) == 'loaded'
    assert calls['n'] == 1  # loader only called once


def test_eviction_when_over_max_size():
    c = TTLCache(ttl_seconds=60, max_size=4)
    for i in range(6):
        c.set(f'k{i}', i)
    # After eviction, at most max_size entries remain
    remaining = [c.get(f'k{i}') for i in range(6)]
    present = [r for r in remaining if r is not None]
    assert len(present) <= 4


def test_invalid_ttl_raises():
    with pytest.raises(ValueError):
        TTLCache(ttl_seconds=0)
    with pytest.raises(ValueError):
        TTLCache(ttl_seconds=-1)


def test_invalid_max_size_raises():
    with pytest.raises(ValueError):
        TTLCache(ttl_seconds=60, max_size=0)
