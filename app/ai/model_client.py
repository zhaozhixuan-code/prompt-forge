from langchain_openai import ChatOpenAI

from app.core.config import Settings

"""
实例化模型对象
"""


def create_chat_model(settings: Settings) -> ChatOpenAI:
    # 只依赖 OpenAI-compatible 参数，方便后续切换模型服务商。
    return ChatOpenAI(
        model=settings.resolved_ai_model,
        api_key=settings.resolved_ai_api_key,
        base_url=settings.resolved_ai_base_url,
        temperature=settings.ai_routing_temperature,
        timeout=settings.ai_request_timeout_seconds,
        max_retries=settings.ai_max_retries,
    )
