from langchain_openai import ChatOpenAI

from app.core.config import Settings


def create_chat_model(settings: Settings) -> ChatOpenAI:
    """创建统一的聊天模型客户端。

    当前 DeepSeek 通过 OpenAI-compatible 接口接入，所以这里使用
    langchain-openai 的 ChatOpenAI；后续更换兼容服务商时只需要调整配置。
    """

    # 所有模型参数都从 Settings 读取，避免业务代码直接依赖 .env 字段名。
    return ChatOpenAI(
        model=settings.resolved_ai_model,
        api_key=settings.resolved_ai_api_key,
        base_url=settings.resolved_ai_base_url,
        temperature=settings.ai_routing_temperature,
        timeout=settings.ai_request_timeout_seconds,
        max_retries=settings.ai_max_retries,
        # DeepSeek V4 thinking mode rejects tool_choice, which LangChain uses
        # for structured output. Routing only needs classification, not CoT.
        extra_body={"thinking": {"type": "disabled"}},
    )
