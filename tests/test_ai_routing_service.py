import pytest
from langchain_core.runnables import RunnableLambda

import app.ai.routing_service as routing_service
from app.ai import model_client
from app.ai.routing_service import CodeGenRoutingResult, route_code_gen_type
from app.core.config import Settings


def test_code_gen_routing_result_accepts_multi_file_name() -> None:
    result = CodeGenRoutingResult.model_validate(
        {
            "codeGenType": "multi-file",
            "reason": "用户要求多个文件",
        }
    )

    assert result.codeGenType == "multi-file"


def test_route_code_gen_type_falls_back_when_api_key_missing() -> None:
    settings = Settings(ai_api_key=None)

    result = route_code_gen_type("做一个博客首页", settings=settings)

    # print(type(result))
    # print(result)
    assert result.codeGenType == "html"


def test_route_code_gen_type_retries_then_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts: list[int] = []

    def fail(payload: object) -> CodeGenRoutingResult:
        attempts.append(1)
        raise RuntimeError("temporary model failure")

    class FakeModel:
        def with_structured_output(self, schema: object, **kwargs: object) -> RunnableLambda:
            return RunnableLambda(fail)

    monkeypatch.setattr(routing_service, "create_chat_model", lambda settings: FakeModel())
    settings = Settings(ai_api_key="test-key", ai_routing_max_attempts=3)

    result = route_code_gen_type("做一个博客首页", settings=settings)

    assert result.codeGenType == "html"
    assert len(attempts) == 3


def test_create_chat_model_disables_deepseek_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(model_client, "ChatOpenAI", FakeChatOpenAI)

    model_client.create_chat_model(Settings(ai_api_key="test-key"))

    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}
