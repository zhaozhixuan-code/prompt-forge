"""第四课：LangChain 工具调用。"""

import json

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from app.ai.model_client import create_chat_model
from app.core.config import get_settings


@tool
def analyze_codegen_request(user_prompt: str) -> str:
    """分析用户需求，返回 PromptForge 推荐的代码生成类型。"""

    prompt_lower = user_prompt.lower()
    if "vue" in prompt_lower or "vue3" in prompt_lower:
        code_gen_type = "vue_project"
        reason = "用户明确要求 Vue 工程。"
    elif "多个文件" in user_prompt or "css" in prompt_lower or "javascript" in prompt_lower:
        code_gen_type = "multi-file"
        reason = "需求更适合拆分为多个静态文件。"
    else:
        code_gen_type = "html"
        reason = "普通单页面需求，HTML 模式足够。"

    # 工具返回字符串，便于模型继续读取和总结。
    return json.dumps(
        {
            "codeGenType": code_gen_type,
            "reason": reason,
        },
        ensure_ascii=False,
    )


TOOLS = [analyze_codegen_request]
TOOLS_BY_NAME = {current_tool.name: current_tool for current_tool in TOOLS}


def run_tool_calling(user_prompt: str) -> str:
    """让模型先调用工具，再根据工具结果生成最终回答。"""

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        return "请先在 .env 中配置 AI_API_KEY。"

    model_with_tools = create_chat_model(settings).bind_tools(TOOLS)
    messages = [
        SystemMessage(
            content=(
                "你是 PromptForge 的代码生成助手。"
                "回答前必须调用 analyze_codegen_request 工具，"
                "然后根据工具结果说明推荐的代码生成类型。"
                "不要生成任何应用代码。"
                "最终回答只需要说明工具返回值和推荐原因。"
            )
        ),
        HumanMessage(content=user_prompt),
    ]

    ai_message = model_with_tools.invoke(messages)
    if not ai_message.tool_calls:
        return f"模型没有发起工具调用，直接回答：{ai_message.content}"

    tool_messages: list[ToolMessage] = []
    trace_lines: list[str] = ["=== 工具调用记录 ==="]
    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        selected_tool = TOOLS_BY_NAME[tool_name]
        tool_result = selected_tool.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
        )
        trace_lines.append(f"{tool_name}({tool_call['args']}) -> {tool_result}")

    final_message = create_chat_model(settings).invoke(
        [*messages, ai_message, *tool_messages]
    )
    trace_lines.append("\n=== 最终回答 ===")
    trace_lines.append(str(final_message.content))
    return "\n".join(trace_lines)


def _safe_console_text(text: str) -> str:
    """避免 Windows GBK 控制台遇到特殊字符时报错。"""

    console_encoding = "gbk"
    return text.encode(console_encoding, errors="replace").decode(console_encoding)


def main() -> None:
    """运行本课 demo。"""

    user_prompt = "帮我做一个 Vue3 番茄钟应用，需要开始、暂停、重置按钮。"
    print(_safe_console_text(run_tool_calling(user_prompt)))


if __name__ == "__main__":
    main()
