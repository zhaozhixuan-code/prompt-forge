# LangChain 学习 demo

这个目录只放学习代码，不参与 PromptForge 主业务链路。

## 学习顺序

1. `lesson01_basic_chat.py`：Messages、PromptTemplate、Chain。
2. `lesson02_structured_output.py`：Pydantic schema、结构化输出、JSON 结果解析。
3. `lesson03_streaming.py`：流式输出、chunk、SSE data 包装。
4. `lesson04_tools.py`：工具定义、bind_tools、工具执行闭环。
5. 后续再加入 LangGraph。

## 运行方式

```powershell
uv run python -m demo.lesson01_basic_chat
uv run python -m demo.lesson02_structured_output
uv run python -m demo.lesson03_streaming
uv run python -m demo.lesson04_tools
uv run python -m demo.lesson05_langgraph
```

运行前需要在 `.env` 中配置 `AI_API_KEY`、`AI_BASE_URL` 和 `AI_MODEL`，模型配置会复用项目里的 `app.core.config.Settings`。
