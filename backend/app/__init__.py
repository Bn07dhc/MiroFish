"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # 设置日志
    logger = setup_logger('mirofish')
    
    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)
    
    # 启用CORS - 仅允许 ALLOWED_ORIGINS 中显式列出的来源
    # 之前默认 origins="*" 允许任意域名访问 API，存在 CSRF 与凭据滥用风险
    allowed_origins = app.config.get('ALLOWED_ORIGINS') or ['http://localhost:5173']
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    if should_log_startup:
        logger.info(f"CORS 允许的来源: {allowed_origins}")
    
    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")
    
    # 敏感字段名（大小写不敏感子串匹配）；命中后在日志中以 *** 替代
    _SENSITIVE_KEY_FRAGMENTS = (
        'password', 'token', 'secret', 'api_key', 'apikey',
        'authorization', 'auth', 'cookie', 'session',
    )

    def _sanitize_for_log(value, depth: int = 0):
        """递归地脱敏字典/列表中的敏感字段，并截断过长字符串。"""
        if depth > 4:
            return '<truncated:depth>'
        if isinstance(value, dict):
            return {
                k: ('***'
                    if isinstance(k, str) and any(f in k.lower() for f in _SENSITIVE_KEY_FRAGMENTS)
                    else _sanitize_for_log(v, depth + 1))
                for k, v in value.items()
            }
        if isinstance(value, list):
            # 仅记录前 20 项，避免日志被超长列表淹没
            return [_sanitize_for_log(v, depth + 1) for v in value[:20]]
        if isinstance(value, str) and len(value) > 500:
            return value[:500] + f'...<truncated {len(value) - 500} chars>'
        return value

    # 请求日志中间件
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            body = request.get_json(silent=True)
            if body is not None:
                logger.debug(f"请求体: {_sanitize_for_log(body)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"响应: {response.status_code}")
        return response
    
    # 注册蓝图
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')

    # 在蓝图注册之后挂载 API 认证 + 速率限制（仅对 /api/* 生效，/health 除外）
    from .utils.auth import install_auth_and_rate_limit
    install_auth_and_rate_limit(app)

    # 全局错误处理：兜底任何未被捕获的异常，避免堆栈/路径泄漏到客户端
    from .utils.errors import register_error_handlers
    register_error_handlers(app)
    
    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app

