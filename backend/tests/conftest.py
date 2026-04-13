"""
pytest 引导：把 backend/ 加入 sys.path，使 `import app.utils.xxx` 可用。

测试用例只覆盖纯工具模块（validators / errors / safe_html 的后端镜像、
auth 的窗口计数器），避免引入 Flask/LLM/OASIS 等重依赖。
"""

import os
import sys

# 必须在任何 `from app...` 导入之前设置：app/__init__.py 触发 Config 加载，
# Config 现在要求 SECRET_KEY（除非 DEBUG=True），否则抛 RuntimeError。
# 这里给测试一个固定的占位密钥，使导入图谱可正常解析。
os.environ.setdefault('SECRET_KEY', 'pytest-fixture-secret-key-not-for-prod')
os.environ.setdefault('FLASK_DEBUG', 'False')

# 把 backend/ 加入 sys.path，对应 `import app.*`
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
