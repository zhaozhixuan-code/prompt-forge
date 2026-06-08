"""第三课：LangChain 流式输出。"""

import json
from collections.abc import Iterator

from langchain_core.messages import AIMessageChunk
from langchain_core.prompts import ChatPromptTemplate

from app.ai.model_client import create_chat_model
from app.core.config import get_settings


def _chunk_to_text(chunk: AIMessageChunk) -> str:
    """从模型流式 chunk 中提取文本内容。"""

    content = chunk.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(item) for item in content)
    return ""


def stream_lesson_reply(user_prompt: str) -> Iterator[str]:
    """逐段返回模型生成的文本。"""

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        yield "请先在 .env 中配置 AI_API_KEY。"
        return

    model = create_chat_model(settings)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个耐心的 LangChain 教练，请用简洁中文回答。"),
            ("human", "请用 5 句话解释这个问题：{user_prompt}"),
        ]
    )

    chain = prompt | model
    for chunk in chain.stream({"user_prompt": user_prompt}):
        text = _chunk_to_text(chunk)
        if text:
            yield text


def format_sse_data(text: str) -> str:
    """把文本片段包装成 PromptForge 前端兼容的 SSE data 行。"""

    payload = json.dumps({"d": text}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def format_sse_done() -> str:
    """生成一次 SSE 结束事件。"""

    return "event: done\ndata:\n\n"


def main() -> None:
    """运行本课 demo。"""

    user_prompt = "LangChain 的 stream 和 invoke 有什么区别"
    chunks: list[str] = []

    print("=== 直接流式打印 ===")
    for text in stream_lesson_reply(user_prompt):
        chunks.append(text)
        print(text, end="", flush=True)

    print("\n\n=== SSE 包装示例 ===")
    for text in chunks[:5]:
        print(format_sse_data(text), end="")
    print(format_sse_done(), end="")


if __name__ == "__main__":
    main()
