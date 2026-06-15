"""第六课：LangChain Agent 基础。"""

import json

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from app.ai.model_client import create_chat_model
from app.core.config import get_settings


@tool
def classify_codegen_type(user_prompt: str) -> str:
    """根据用户需求推荐 PromptForge 代码生成类型。"""

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

    return json.dumps({"codeGenType": code_gen_type, "reason": reason}, ensure_ascii=False)


@tool
def estimate_complexity(user_prompt: str) -> str:
    """粗略估算生成需求复杂度。"""

    score = 1
    for keyword in ["登录", "数据库", "支付", "后台", "上传", "部署", "权限"]:
        if keyword in user_prompt:
            score += 1
    complexity = "high" if score >= 4 else "medium" if score >= 2 else "low"
    return json.dumps({"complexity": complexity, "score": score}, ensure_ascii=False)


@tool
def list_safety_notes(code_gen_type: str) -> str:
    """列出指定代码生成类型需要注意的安全事项。"""

    notes = {
        "html": ["限制输出目录", "禁止生成包含绝对路径的文件名"],
        "multi-file": ["校验每个相对路径", "禁止目录穿越"],
        "vue_project": ["构建命令必须由后端白名单控制", "package.json 依赖需要审查"],
    }
    return json.dumps({"notes": notes.get(code_gen_type, notes["html"])}, ensure_ascii=False)


TOOLS = [classify_codegen_type, estimate_complexity, list_safety_notes]


def run_agent_demo(user_prompt: str) -> str:
    """创建 Agent，让模型自动选择并调用工具。"""

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        return "请先在 .env 中配置 AI_API_KEY。"

    agent = create_agent(
        model=create_chat_model(settings),
        tools=TOOLS,
        system_prompt=(
            "你是 PromptForge 的课程演示 Agent。"
            "必须先调用工具分析用户需求，再给出简短结论。"
            "不要生成应用代码。"
        ),
    )
    # 创建 Agent
    result = agent.invoke({"messages": [HumanMessage(content=user_prompt)]})
    # 运行 Agent
    messages = result["messages"]

    trace_lines = ["=== Agent 消息轨迹 ==="]
    for message in messages:
        message_type = message.__class__.__name__
        content = str(getattr(message, "content", ""))
        if getattr(message, "tool_calls", None):
            trace_lines.append(f"{message_type}: tool_calls={message.tool_calls}")
        elif content:
            trace_lines.append(f"{message_type}: {content}")
    return "\n".join(trace_lines)


def _safe_console_text(text: str) -> str:
    """避免 Windows GBK 控制台遇到特殊字符时报错。"""

    return text.encode("gbk", errors="replace").decode("gbk")


def main() -> None:
    """运行本课 demo。"""

    user_prompt = "帮我做一个 Vue3 番茄钟应用，需要开始、暂停、重置按钮。"
    print(_safe_console_text(run_agent_demo(user_prompt)))


if __name__ == "__main__":
    main()
