"""
配置管理
统一从项目根目录的 .env 文件加载配置
"""

import os
import secrets
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
# 路径: MiroFish/.env (相对于 backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # 如果根目录没有 .env，尝试加载环境变量（用于生产环境）
    load_dotenv(override=True)


def _resolve_secret_key() -> str:
    """解析 SECRET_KEY 配置。

    生产环境必须显式设置 SECRET_KEY；若仅用于本地开发（FLASK_DEBUG=True）且
    未提供，则生成一个进程内的临时随机密钥并发出警告，避免用户沿用可预测的
    默认值（曾经的 'mirofish-secret-key'）。
    """
    key = os.environ.get('SECRET_KEY')
    if key:
        return key

    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if debug:
        # 开发模式下生成临时密钥（每次进程启动都不同），避免使用公开的硬编码默认值
        import warnings
        warnings.warn(
            "SECRET_KEY 未设置，已在开发模式下生成临时随机密钥。"
            "请在 .env 中显式设置 SECRET_KEY 用于生产部署。",
            RuntimeWarning,
            stacklevel=2,
        )
        return secrets.token_urlsafe(48)

    raise RuntimeError(
        "SECRET_KEY 环境变量必须显式设置（生产环境禁止使用默认值）。"
        "请在 .env 中配置 SECRET_KEY。"
    )


class Config:
    """Flask配置类"""

    # Flask配置 - DEBUG 默认 False，避免生产环境意外暴露调试器与堆栈信息
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = _resolve_secret_key()

    # CORS 配置：逗号分隔的允许来源列表；默认仅允许本地开发端口
    # 例如：ALLOWED_ORIGINS=https://app.example.com,https://staging.example.com
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            'ALLOWED_ORIGINS',
            'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000'
        ).split(',')
        if origin.strip()
    ]
    
    # JSON配置 - 禁用ASCII转义，让中文直接显示（而不是 \uXXXX 格式）
    JSON_AS_ASCII = False
    
    # LLM配置（统一使用OpenAI格式）
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep配置
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # 文本处理配置
    DEFAULT_CHUNK_SIZE = 500  # 默认切块大小
    DEFAULT_CHUNK_OVERLAP = 50  # 默认重叠大小
    
    # OASIS模拟配置
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS平台可用动作配置
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent配置
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    @classmethod
    def validate(cls):
        """验证必要配置"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 未配置")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY 未配置")
        return errors

