"""
生产环境 WSGI 入口。

gunicorn/uwsgi 等生产 WSGI 服务器需要一个模块级的 app 对象，而 run.py 的
main() 会调用 app.run()（Flask 开发服务器），不适合用于生产。
本文件只负责创建应用实例并暴露 `app`，供 `gunicorn wsgi:app` 使用。
"""

import os
import sys

# 确保 app 包可被导入（与 run.py 保持一致的 sys.path 处理）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config

# 启动前校验必填配置（失败时让 gunicorn 启动器直接看到错误）
_errors = Config.validate()
if _errors:
    raise RuntimeError(
        "配置错误，生产启动终止:\n  - " + "\n  - ".join(_errors)
    )

app = create_app()
