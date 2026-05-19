"""AI Provider Router — 按配置选择 Provider，无 API Key 时降级"""
import logging
from app.services.providers.base import AIProvider
from app.services.providers.deepseek import DeepSeekProvider
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
_provider: AIProvider | None = None
_provider_initialized = False


def get_provider() -> AIProvider | None:
    """获取 AI Provider；无 API Key 返回 None"""
    global _provider, _provider_initialized

    if not _provider_initialized:
        _provider_initialized = True
        if settings.DEEPSEEK_API_KEY:
            _provider = DeepSeekProvider(
                api_key=settings.DEEPSEEK_API_KEY,
                model=settings.DEEPSEEK_MODEL,
            )
            logger.info(f"AI Provider 初始化成功: model={settings.DEEPSEEK_MODEL}")
        else:
            logger.warning("DEEPSEEK_API_KEY 未设置，AI 降级为规则引擎模式")

    return _provider
