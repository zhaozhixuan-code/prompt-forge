"""第二课：让模型返回结构化结果。"""

import json
from typing import Literal

from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError

from app.ai.model_client import create_chat_model
from app.core.config import get_settings

CodeGenType = Literal["html", "multi-file", "vue_project"]


class RouteDecision(BaseModel):
    """代码生成类型判断结果。"""

    codeGenType: CodeGenType = Field(description="最适合当前需求的代码生成类型")
    reason: str = Field(description="选择该生成类型的简短原因")
    confidence: float = Field(ge=0, le=1, description="判断置信度，范围 0 到 1")


ROUTING_SYSTEM_PROMPT = """
你是 PromptForge 的代码生成路由器。

你必须返回一个 json 对象。
不要返回 Markdown。
不要返回代码块。
不要返回解释性文字。

必须严格返回下面这些字段：

{{
  "codeGenType": "html",
  "reason": "普通单页面网页，HTML 模式足够完成",
  "confidence": 0.9
}}

字段规则：
- codeGenType 只能是 "html"、"multi-file"、"vue_project" 三者之一。
- reason 必须是简短中文字符串。
- confidence 必须是 0 到 1 之间的数字。
- 禁止返回 {{"type": "..."}}, 字段名必须使用 codeGenType。

选择规则：
- 普通单页面网页、小游戏、简单工具，返回 "html"。
- 需要多个静态文件但不是 Vue 工程，返回 "multi-file"。
- 用户明确要求 Vue、Vue3、组件化工程，返回 "vue_project"。
""".strip()


def _fallback_route_decision(reason: str) -> RouteDecision:
    """模型结构化解析失败时返回默认 HTML 路由。"""

    return RouteDecision(codeGenType="html", reason=reason, confidence=0)


def _to_pretty_json(value: BaseModel) -> str:
    """把 Pydantic 对象打印成适合阅读的 JSON。"""

    return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, indent=2)


def classify_code_gen_type(user_prompt: str) -> RouteDecision | str:
    """把用户需求分类成 PromptForge 支持的代码生成类型。"""

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        return "请先在 .env 中配置 AI_API_KEY。"

    model = create_chat_model(settings)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ROUTING_SYSTEM_PROMPT),
            ("human", "请判断这个需求适合哪种代码生成类型：{user_prompt}"),
        ]
    )

    # json_mode 对 OpenAI-compatible 接口更友好。
    structured_model = model.with_structured_output(RouteDecision, method="json_mode")
    chain = prompt | structured_model
    try:
        result = chain.invoke({"user_prompt": user_prompt})
        if isinstance(result, RouteDecision):
            return result
        return RouteDecision.model_validate(result)
    except (OutputParserException, ValidationError, ValueError) as exc:
        # demo 不直接崩溃，方便观察结构化输出失败后的兜底策略。
        return _fallback_route_decision(f"模型未返回符合 schema 的 json，已兜底为 html：{exc}")


def main() -> None:
    """运行本课 demo。"""

    user_prompt = "做一个番茄钟网页，有开始、暂停、重置按钮，并显示当前专注轮次。要求生成项目为VUE"

    print("=== 代码生成类型判断 ===")
    route_result = classify_code_gen_type(user_prompt)
    print(_to_pretty_json(route_result) if isinstance(route_result, BaseModel) else route_result)


if __name__ == "__main__":
    main()
