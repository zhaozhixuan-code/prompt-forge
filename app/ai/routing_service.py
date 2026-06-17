"""代码生成类型路由服务。

这层只负责一件事：根据用户的初始需求，判断后续代码生成应该走
HTML、multi-file 还是 vue_project。路由结果会在创建应用时落库，
后续生成链路直接按这个类型选择对应处理器。
"""

import logging
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, model_validator

from app.ai.model_client import create_chat_model
from app.ai.prompts import CODEGEN_ROUTING_SYSTEM_PROMPT, load_prompt
from app.core.config import Settings, get_settings
from app.core.exceptions import ErrorCode, throw_if

logger = logging.getLogger(__name__)

# 路由层只允许这三种生成类型，避免模型返回任意字符串后写入数据库。
CodeGenType = Literal["html", "multi-file", "vue_project"]
# 路由失败时默认回退到 HTML，因为它是当前最稳定、最容易兜底的链路。
DEFAULT_CODE_GEN_TYPE: CodeGenType = "html"

# 类型别名表用于承接历史命名或模型返回的等价写法。
CODE_GEN_TYPE_ALIASES = {
    "html": "html",
    "multi-file": "multi-file",
    "vue_project": "vue_project",
}


class CodeGenRoutingResult(BaseModel):
    # codeGenType 是后续生成流程真正依赖的主字段。
    codeGenType: CodeGenType = Field(description="代码生成类型")
    # reason 只用于排查和日志，不参与业务分支判断。
    reason: str = Field(default="", description="选择该类型的简短原因")

    @model_validator(mode="before")
    @classmethod
    def normalize_code_gen_type(cls, data: object) -> object:
        # 先把历史命名归一，再交给 Pydantic 校验，避免老数据或旧 prompt 直接报错。
        if isinstance(data, dict) and "codeGenType" in data:
            raw_type = str(data["codeGenType"]).strip()
            normalized_type = CODE_GEN_TYPE_ALIASES.get(raw_type)
            if normalized_type is not None:
                data = {**data, "codeGenType": normalized_type}
        return data


def _default_route_result(reason: str) -> CodeGenRoutingResult:
    # 路由失败不能阻断创建应用，因此返回一个稳定的 HTML 兜底结果。
    return CodeGenRoutingResult(codeGenType=DEFAULT_CODE_GEN_TYPE, reason=reason)


def route_code_gen_type(
    user_prompt: str,
    settings: Settings | None = None,
) -> CodeGenRoutingResult:
    """根据用户初始需求判断后续生成类型。

    这一步属于“智能路由”，不是代码生成本身。它的职责是把自然语言需求
    变成可落库、可分支的生成类型，并且在失败时始终返回可用结果。
    """
    current_settings = settings or get_settings()
    init_prompt = user_prompt.strip()

    # 创建应用前必须有有效需求文本，否则后续 prompt 和路由都没有输入基础。
    throw_if(not init_prompt, ErrorCode.PARAMS_ERROR, "initPrompt 不能为空")
    if not current_settings.resolved_ai_api_key:
        # 没有 API Key 时直接兜底，保证创建应用不会被环境配置卡住。
        logger.warning("AI API Key 未配置，代码生成类型路由兜底为 html")
        return _default_route_result("AI API Key 未配置，默认使用 HTML 模式")

    # 路由 prompt 独立放在文件里，便于直接替换为原 Java 项目的提示词。
    system_prompt = load_prompt(CODEGEN_ROUTING_SYSTEM_PROMPT)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{user_prompt}"),
        ]
    )

    # 路由阶段允许有限重试，只处理临时性模型失败，不改变业务结果约束。
    max_attempts = max(1, current_settings.ai_routing_max_attempts)
    for attempt in range(1, max_attempts + 1):
        try:
            # 每次调用都复用统一的模型配置，避免路由和后续生成出现两套参数。
            model = create_chat_model(current_settings)
            # 结构化输出要求模型直接产出符合 schema 的结果，减少手写 JSON 解析。
            chain = prompt | model.with_structured_output(CodeGenRoutingResult, method="function_calling")
            result = chain.invoke({"user_prompt": init_prompt})
            if isinstance(result, CodeGenRoutingResult):
                return result
            if isinstance(result, dict):
                # 某些运行时会返回 dict，这里统一再做一次模型校验。
                return CodeGenRoutingResult.model_validate(result)
            raise ValueError("AI 路由结果类型无效")
        except Exception as exc:
            # 单次失败先重试；但最终必须给出兜底结果，不能让创建流程中断。
            logger.warning("AI 路由第 %s/%s 次调用失败：%s", attempt, max_attempts, exc)

    return _default_route_result("AI 路由多次失败，默认使用 HTML 模式")
