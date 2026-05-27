"""第一课：LangChain 最小聊天调用。"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.ai.model_client import create_chat_model
from app.core.config import get_settings


def ask_with_messages(topic: str) -> str:
    """直接用 Message 调模型，适合理解聊天模型的输入结构。"""

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        return "请先在 .env 中配置 AI_API_KEY。"

    # 获得对象
    model = create_chat_model(settings)

    # SystemMessage 用来约束模型角色，HumanMessage 表示用户输入。
    messages = [
        SystemMessage(content="你是一个耐心的 Python LangChain 教练。"),
        HumanMessage(content=f"请用三句话解释：{topic}"),
    ]

    # 调用模型
    response = model.invoke(messages)
    return str(response.content)


def ask_with_prompt_template(topic: str) -> str:
    """用 PromptTemplate 组织提示词，适合后续做可复用业务链路。"""

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        return "请先在 .env 中配置 AI_API_KEY。"

    model = create_chat_model(settings)

    # 模板负责把变量填进提示词，减少手写字符串拼接。
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个耐心的 Python LangChain 教练。"),
            ("human", "请用三句话解释：{topic}"),
        ]
    )

    # 管道符会把 prompt 的输出交给 model，形成一个最小 chain。
    chain = prompt | model
    response = chain.invoke({"topic": topic})
    return str(response.content)


def main() -> None:
    """运行本课 demo。"""

    topic = "LangChain 里的 Message 和 PromptTemplate 有什么区别"

    print("=== 直接使用 messages ===")
    print(ask_with_messages(topic))
    #
    # print("\n=== 使用 prompt template + chain ===")
    # print(ask_with_prompt_template(topic))


if __name__ == "__main__":
    main()
