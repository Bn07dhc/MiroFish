"""
通用输入校验工具

集中处理 API 边界上的常见校验需求：
- 防止路径穿越（path traversal）：例如把不可信的 simulation_id 拼接到磁盘路径
- 数值边界限制：例如 limit/offset/chunk_size 等参数
- 标识符格式校验：仅允许安全字符集

设计原则：
- 失败时抛 ValueError，由 API 层统一捕获并返回 400
- 不依赖具体框架，便于在 service / script 中复用
"""

from __future__ import annotations

import os
import re
from typing import Optional

# 允许的标识符字符集：字母、数字、下划线、连字符、点
# 显式拒绝 '/'、'\\'、空字节、'..' 等可能用于路径穿越的字符序列
_SAFE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_.\-]+$')


def validate_safe_identifier(value: str, field_name: str = 'id', max_length: int = 128) -> str:
    """校验一个标识符仅包含安全字符且不为路径穿越载荷。

    Args:
        value: 待校验的字符串
        field_name: 字段名（用于错误消息）
        max_length: 最大长度

    Returns:
        校验通过的原值

    Raises:
        ValueError: 校验失败
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} 不能为空")
    if len(value) > max_length:
        raise ValueError(f"{field_name} 长度不能超过 {max_length}")
    if '\x00' in value:
        raise ValueError(f"{field_name} 包含非法字符")
    if value in ('.', '..') or '..' in value:
        raise ValueError(f"{field_name} 包含非法路径片段")
    if not _SAFE_ID_PATTERN.match(value):
        raise ValueError(
            f"{field_name} 仅允许字母、数字、下划线、连字符与点"
        )
    return value


def safe_join(base_dir: str, *parts: str) -> str:
    """以路径穿越安全的方式拼接路径。

    确保最终路径仍位于 base_dir 之内。任何企图通过 '..' 或绝对路径
    跳出 base_dir 的输入都会被拒绝。

    Args:
        base_dir: 必须存在或可被解析为绝对路径的根目录
        *parts: 用户提供的子路径片段

    Returns:
        拼接并解析后的绝对路径

    Raises:
        ValueError: 路径越界或包含非法字符
    """
    base_abs = os.path.realpath(os.path.abspath(base_dir))
    joined = os.path.realpath(os.path.abspath(os.path.join(base_abs, *parts)))

    # 末尾添加分隔符确保前缀比较不会把 /tmp/foo-bar 误判为 /tmp/foo 子目录
    base_with_sep = base_abs.rstrip(os.sep) + os.sep
    if joined != base_abs and not joined.startswith(base_with_sep):
        raise ValueError("路径越界，禁止访问 base_dir 之外的位置")
    return joined


def clamp_int(
    value,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """把输入钳制到 [minimum, maximum]；非法值回退到 default。

    设计用于在请求参数层做 DoS 防护：上游可能传入负数、巨大值或非数字字符串，
    服务端应当保持响应稳定并给出安全边界，不因此抛错中断。

    注意：若调用方希望对越界拒绝，请使用 validate_int_range。
    """
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    if parsed < minimum:
        return minimum
    if parsed > maximum:
        return maximum
    return parsed


def validate_int_range(
    value,
    field_name: str,
    *,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
    default: Optional[int] = None,
) -> int:
    """将值解析为 int 并校验范围。"""
    if value is None or value == '':
        if default is not None:
            return default
        raise ValueError(f"{field_name} 不能为空")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field_name} 必须为整数") from e
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} 不能小于 {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{field_name} 不能大于 {maximum}")
    return parsed


# ---------------------------------------------------------------------------
# 文件内容校验（magic number / MIME）
# ---------------------------------------------------------------------------
#
# 仅靠文件扩展名无法防止攻击者上传伪装的可执行 / polyglot 文件。这里对允许
# 的扩展名额外做一层首字节签名比对；未列出的扩展名直接拒绝。
#
# 如需更全面的检测，可以改用 python-magic（libmagic 绑定），但那会引入
# 二进制依赖，与当前 requirements 的 pure-Python 约束不符，故先提供轻量版。

# 每个扩展名允许的 magic-number 前缀集合。文本类（md/txt/markdown）允许任意
# 字节但要求通过 UTF-8 可解码（尝试常用编码）。
_BINARY_MAGIC = {
    'pdf': (b'%PDF-',),
}
_TEXT_EXTENSIONS = frozenset({'md', 'txt', 'markdown'})


def validate_upload_content(
    head_bytes: bytes,
    extension: str,
    *,
    sample_bytes_for_text: int = 4096,
) -> None:
    """校验上传文件的首字节与扩展名一致。

    Args:
        head_bytes: 已读取的首部字节（至少 ~16 字节即可；文本类按需更多用于
            编码检测，调用方若仅读取 16 字节需传入一个足够长的样本）
        extension: 小写扩展名（不含点）
        sample_bytes_for_text: 文本文件用于编码嗅探的最小样本长度；未达到此
            长度仍会尝试校验，只是覆盖度较低

    Raises:
        ValueError: 扩展名不在白名单，或首字节与扩展名不符
    """
    ext = (extension or '').lower().lstrip('.')

    if ext in _BINARY_MAGIC:
        expected = _BINARY_MAGIC[ext]
        if not any(head_bytes.startswith(sig) for sig in expected):
            raise ValueError(
                f"文件内容与扩展名 .{ext} 不符（首字节不匹配已知签名）"
            )
        return

    if ext in _TEXT_EXTENSIONS:
        # 文本类：拒绝包含空字节（强信号为二进制内容）。非 UTF-8 文件由
        # chardet/charset-normalizer 在 FileParser 中进一步处理。
        sample = head_bytes[:sample_bytes_for_text]
        if b'\x00' in sample:
            raise ValueError(
                f"文件扩展名 .{ext} 声明为文本，但内容含空字节（疑似二进制伪装）"
            )
        return

    raise ValueError(f"不支持的文件类型: .{ext}")
