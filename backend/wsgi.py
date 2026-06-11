"""
MiroFish Backend - 生产环境 WSGI 入口

通过 WSGI 服务器（如 waitress）启动：
    waitress-serve --host=0.0.0.0 --port=5001 --threads=8 wsgi:app

注意：应用使用进程内的单例状态（任务管理器、模拟运行器等），
因此必须以单进程多线程方式部署，不要启用多 worker/多进程。
"""

import os
import sys

# 解决 Windows 控制台中文乱码问题：在所有导入之前设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 确保 app 包可被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config

# 启动前校验必要配置
_errors = Config.validate()
if _errors:
    sys.stderr.write("配置错误:\n")
    for _err in _errors:
        sys.stderr.write(f"  - {_err}\n")
    sys.stderr.write("\n请检查 .env 文件中的配置\n")
    sys.exit(1)

# WSGI 应用对象
app = create_app()


if __name__ == '__main__':
    # 允许 `python wsgi.py` 直接以 waitress 启动（生产模式）
    from waitress import serve

    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    threads = int(os.environ.get('WAITRESS_THREADS', 8))
    # channel-timeout 适当放大，避免长耗时的 LLM 同步请求被中断
    channel_timeout = int(os.environ.get('WAITRESS_CHANNEL_TIMEOUT', 600))

    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        channel_timeout=channel_timeout,
        ident='MiroFish',
    )
