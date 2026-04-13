"""
backend/app/utils/validators.py 的单元测试

覆盖目标：
- safe_join 阻止路径穿越（'../', 绝对路径，混合分隔符）
- validate_safe_identifier 拒绝危险输入
- validate_int_range 边界处理
"""

import os

import pytest

from app.utils.validators import (
    safe_join,
    validate_int_range,
    validate_safe_identifier,
    validate_upload_content,
)


class TestValidateSafeIdentifier:
    def test_accepts_normal_id(self):
        assert validate_safe_identifier('sim_abc-123.v2') == 'sim_abc-123.v2'

    @pytest.mark.parametrize('bad', [
        '',          # empty
        '../etc',    # traversal
        '..',        # bare dot-dot
        '.',         # bare dot
        'a..b',      # embedded ..
        'a/b',       # slash
        'a\\b',      # backslash
        'foo\x00bar',  # null byte
        'has space',
    ])
    def test_rejects_bad_identifiers(self, bad):
        with pytest.raises(ValueError):
            validate_safe_identifier(bad)

    def test_enforces_max_length(self):
        with pytest.raises(ValueError):
            validate_safe_identifier('a' * 200, max_length=128)


class TestSafeJoin:
    def test_joins_normal_path(self, tmp_path):
        result = safe_join(str(tmp_path), 'sim_abc')
        assert result.endswith(os.path.join(str(tmp_path), 'sim_abc'))

    def test_blocks_parent_traversal(self, tmp_path):
        with pytest.raises(ValueError):
            safe_join(str(tmp_path), '../etc/passwd')

    def test_blocks_absolute_paths(self, tmp_path):
        with pytest.raises(ValueError):
            safe_join(str(tmp_path), '/etc/passwd')

    def test_does_not_treat_prefix_match_as_inside(self, tmp_path):
        # /tmp/foo and /tmp/foo-bar should NOT be considered the same root
        base = tmp_path / 'foo'
        base.mkdir()
        sibling = tmp_path / 'foo-bar'
        sibling.mkdir()
        # join base + '../foo-bar' is escape; must error
        with pytest.raises(ValueError):
            safe_join(str(base), '../foo-bar/secret.txt')


class TestValidateIntRange:
    def test_in_range(self):
        assert validate_int_range('5', 'limit', minimum=1, maximum=10) == 5

    def test_default_when_empty(self):
        assert validate_int_range(None, 'limit', default=20) == 20
        assert validate_int_range('', 'limit', default=20) == 20

    def test_below_min(self):
        with pytest.raises(ValueError):
            validate_int_range('0', 'limit', minimum=1, maximum=10)

    def test_above_max(self):
        with pytest.raises(ValueError):
            validate_int_range('1000', 'limit', minimum=1, maximum=100)

    def test_non_integer(self):
        with pytest.raises(ValueError):
            validate_int_range('abc', 'limit')


class TestValidateUploadContent:
    def test_accepts_real_pdf_magic_number(self):
        validate_upload_content(b'%PDF-1.7\n%\xe2\xe3\xcf\xd3', 'pdf')

    def test_rejects_elf_disguised_as_pdf(self):
        # ELF magic = 0x7F 'E' 'L' 'F'
        with pytest.raises(ValueError):
            validate_upload_content(b'\x7fELF\x02\x01\x01\x00', 'pdf')

    def test_rejects_zip_disguised_as_pdf(self):
        with pytest.raises(ValueError):
            validate_upload_content(b'PK\x03\x04', 'pdf')

    def test_accepts_plain_text_md(self):
        validate_upload_content(b'# Heading\n\nhello world\n', 'md')

    def test_rejects_binary_disguised_as_text(self):
        with pytest.raises(ValueError):
            validate_upload_content(b'# Heading\x00\x00not text', 'txt')

    def test_rejects_unknown_extension(self):
        with pytest.raises(ValueError):
            validate_upload_content(b'any content', 'exe')

    def test_rejects_empty_extension(self):
        with pytest.raises(ValueError):
            validate_upload_content(b'any content', '')
