"""第七课：短期记忆和 Checkpointer。

本课演示的是 Agent/Graph 层面的“运行状态记忆”，不是业务聊天记录。

关键点：
1. `InMemorySaver` 会把同一个 `thread_id` 下的消息历史保存到内存里。
2. 下一次使用相同 `thread_id` 调用 Agent 时，Agent 能看到前面的上下文。
3. 不同 `thread_id` 的上下文互相隔离。
4. 生产项目里，用户可见的聊天历史仍然应该写入数据库，例如 PromptForge 的
   `chat_history` 表；checkpointer 更适合保存 Agent/Graph 执行状态。
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ai.model_client import create_chat_model
from app.core.config import get_settings


def _last_text(result: dict) -> str:
    """取出 Agent 最后一条消息文本。"""

    # `create_agent().invoke(...)` 返回的是一个状态字典，其中 `messages`
    # 是本次会话累计下来的消息列表，通常包含 HumanMessage、AIMessage、
    # ToolMessage 等。这里为了 demo 输出简洁，只取最后一条 AI 回复。
    messages = result["messages"]
    return str(messages[-1].content)


def run_memory_demo() -> str:
    """演示同一 thread_id 能保留短期上下文。"""

    # 所有模型配置仍然复用项目统一配置，避免 demo 里散落 API Key、base_url 等细节。
    settings = get_settings()
    if not settings.resolved_ai_api_key:
        return "请先在 .env 中配置 AI_API_KEY。"

    # InMemorySaver 是最小可运行的 checkpointer。
    # 它只把状态放在当前 Python 进程内存里：
    # - 适合学习、测试、demo。
    # - 不适合生产长期保存，因为进程重启后记忆会丢失。
    checkpointer = InMemorySaver()

    # 给 Agent 传入 checkpointer 后，Agent 每次执行都会按 thread_id
    # 保存和恢复消息状态。这里不注册工具，因为本课只关注“记忆”。
    agent = create_agent(
        model=create_chat_model(settings),
        tools=[],
        system_prompt="你是 PromptForge 学习助手，回答必须简短。",
        checkpointer=checkpointer,
    )

    # thread_id 可以理解成一次对话线程的 ID。
    # 相同 thread_id：共享上下文。
    # 不同 thread_id：上下文隔离。
    thread_a = {"configurable": {"thread_id": "lesson07-a"}}
    thread_b = {"configurable": {"thread_id": "lesson07-b"}}

    # 第一轮：在 lesson07-a 线程里告诉 Agent 一个应用名称。
    # 这条消息和模型回复会被 checkpointer 保存到 lesson07-a。
    first = agent.invoke(
        {"messages": [HumanMessage(content="请记住我的应用名称是番茄钟 Pro。")]},
        config=thread_a,
    )

    # 第二轮：仍然使用 lesson07-a。
    # 因为 thread_id 相同，Agent 能恢复上一轮上下文，所以可以回答出应用名称。
    second = agent.invoke(
        {"messages": [HumanMessage(content="我刚才说的应用名称是什么？")]},
        config=thread_a,
    )

    # 第三轮：换成 lesson07-b。
    # 这是另一个独立线程，没有第一轮的上下文，所以模型不应该知道“番茄钟 Pro”。
    isolated = agent.invoke(
        {"messages": [HumanMessage(content="我刚才说的应用名称是什么？")]},
        config=thread_b,
    )

    return "\n".join(
        [
            "=== thread_id=lesson07-a 第一轮 ===",
            _last_text(first),
            "\n=== thread_id=lesson07-a 第二轮 ===",
            _last_text(second),
            "\n=== thread_id=lesson07-b 隔离会话 ===",
            _last_text(isolated),
        ]
    )


def main() -> None:
    """运行本课 demo。"""

    print(run_memory_demo())


if __name__ == "__main__":
    main()
