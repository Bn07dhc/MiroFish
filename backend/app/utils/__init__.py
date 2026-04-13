"""
工具模块

提供按需懒加载的 re-export，避免在测试或仅使用部分工具时强制导入
重依赖（例如 LLMClient 依赖 openai SDK）。
"""

from .locale import t, get_locale, set_locale, get_language_instruction

__all__ = ['FileParser', 'LLMClient', 't', 'get_locale', 'set_locale', 'get_language_instruction']


def __getattr__(name):
    """PEP 562 懒加载。仅在被显式访问时才导入对应子模块。"""
    if name == 'FileParser':
        from .file_parser import FileParser
        return FileParser
    if name == 'LLMClient':
        from .llm_client import LLMClient
        return LLMClient
    raise AttributeError(f"module 'app.utils' has no attribute {name!r}")

