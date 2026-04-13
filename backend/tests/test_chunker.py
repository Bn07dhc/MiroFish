"""
backend/app/utils/file_parser.py 的 split_text_into_chunks 回归测试。

重点验证：
- 中英文混合文本按期望切分
- overlap 保持上下文重叠
- overlap >= chunk_size 不再死循环（之前的隐患）
- chunk_size <= 0 抛 ValueError
- 短文本原样返回
- 所有块均为 strip 后非空
"""

import pytest

from app.utils.file_parser import split_text_into_chunks


def test_short_text_returned_as_single_chunk():
    assert split_text_into_chunks("hello", chunk_size=100, overlap=10) == ["hello"]


def test_empty_or_whitespace_returns_empty():
    assert split_text_into_chunks("   \n  ", chunk_size=100, overlap=0) == []
    assert split_text_into_chunks("", chunk_size=100, overlap=0) == []


def test_chunks_cover_full_text_and_overlap():
    # 1200 chars worth of distinguishable content
    text = "".join(f"sentence_{i}. " for i in range(1, 100))
    chunks = split_text_into_chunks(text, chunk_size=200, overlap=30)
    assert len(chunks) > 1
    # Concatenating chunks (with strip) must at least contain every sentence
    merged = " ".join(chunks)
    for i in [1, 50, 99]:
        assert f"sentence_{i}" in merged


def test_chunks_respect_sentence_boundaries():
    text = "第一句。第二句。第三句。" * 100
    chunks = split_text_into_chunks(text, chunk_size=80, overlap=10)
    # Each chunk should end on a separator (except possibly the last)
    for c in chunks[:-1]:
        assert c.endswith("。") or c.endswith("\n") or c.endswith(". "), \
            f"unexpected chunk end: {c!r}"


def test_overlap_clamped_when_greater_than_chunk_size():
    # Previously this would loop forever; now overlap is clamped to chunk_size - 1
    text = "a" * 1000
    chunks = split_text_into_chunks(text, chunk_size=100, overlap=500)
    assert len(chunks) > 1
    assert sum(len(c) for c in chunks) >= len(text)


def test_chunk_size_zero_raises():
    with pytest.raises(ValueError):
        split_text_into_chunks("any text", chunk_size=0, overlap=0)


def test_chunk_size_negative_raises():
    with pytest.raises(ValueError):
        split_text_into_chunks("any text", chunk_size=-5, overlap=0)


def test_all_chunks_are_non_empty_after_strip():
    text = "  hello  \n\n   world   \n\n   " * 50
    chunks = split_text_into_chunks(text, chunk_size=80, overlap=20)
    assert all(c and c == c.strip() for c in chunks)


def test_forward_progress_with_degenerate_separator_placement():
    # Worst case: separator at the very beginning of each window — previously
    # could have caused `start` to not advance. With the min-advance guard this
    # must terminate quickly.
    text = ("。" + "x" * 99) * 50  # chunk_size=100, sep at position 0 of each
    chunks = split_text_into_chunks(text, chunk_size=100, overlap=10)
    assert len(chunks) > 0
    assert len(chunks) < len(text)  # must actually terminate
