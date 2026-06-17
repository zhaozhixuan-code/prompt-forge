# LangChain 学习 demo

这个目录只放学习代码，不参与 PromptForge 主业务链路。

## 学习顺序

1. `lesson01_basic_chat.py`：Messages、PromptTemplate、Chain。
2. `lesson02_structured_output.py`：Pydantic schema、结构化输出、JSON 结果解析。
3. `lesson03_streaming.py`：流式输出、chunk、SSE data 包装。
4. `lesson04_tools.py`：工具定义、bind_tools、工具执行闭环。
5. `lesson05_langgraph.py`：StateGraph、节点、边、条件分支、工作流状态。
6. `lesson06_agents.py`：create_agent、工具自动选择、Agent 消息轨迹。
7. `lesson07_memory_checkpoint.py`：InMemorySaver、thread_id、短期记忆隔离。
8. `lesson08_rag_local_docs.py`：本地文档读取、切分、检索、上下文增强。
9. `lesson09_guardrails_retries.py`：结构化校验、重试、兜底、路径安全。
10. `lesson10_langgraph_streaming.py`：LangGraph 节点流式事件、类 SSE 包装。
11. `lesson11_human_in_loop.py`：人工审批、approve/reject 分支、dry-run 执行。
12. `lesson12_promptforge_codegen_workflow.py`：PromptForge 代码生成 dry-run 综合工作流。

## 运行方式

```powershell
uv run python -m demo.lesson01_basic_chat
uv run python -m demo.lesson02_structured_output
uv run python -m demo.lesson03_streaming
uv run python -m demo.lesson04_tools
uv run python -m demo.lesson05_langgraph
uv run python -m demo.lesson06_agents
uv run python -m demo.lesson07_memory_checkpoint
uv run python -m demo.lesson08_rag_local_docs
uv run python -m demo.lesson09_guardrails_retries
uv run python -m demo.lesson10_langgraph_streaming
uv run python -m demo.lesson11_human_in_loop
uv run python -m demo.lesson12_promptforge_codegen_workflow
```

第 1、2、3、4、6、7、8 课会调用模型，运行前需要在 `.env` 中配置 `AI_API_KEY`、`AI_BASE_URL` 和 `AI_MODEL`。
第 5、9、10、11、12 课不调用模型，可以直接运行。
模型配置会复用项目里的 `app.core.config.Settings`。

## 后续高级主题

完成 12 课后，当前项目所需的 LangChain / LangGraph 主干能力已经基本覆盖。后续不建议继续脱离项目无限扩展学习，建议在实际开发中按需补充：

1. LangSmith：trace、调试、评估和线上问题排查。
2. 生产级 RAG：向量数据库、混合检索、重排、RAG 评估。
3. Middleware：模型调用限流、fallback、重试、敏感信息处理。
4. 长期记忆：跨会话用户偏好、项目上下文和业务数据融合。
5. 多 Agent 协作：规划、执行、审查等角色拆分。
6. MCP 工具接入：把外部系统能力暴露给 Agent 使用。
7. 监控与安全：模型调用成本、失败率、工具调用审计和权限边界。

## 下一阶段项目实战

学完 12 课后，优先回到 PromptForge 主链路，把学习代码迁移为真实业务能力：

1. 整理 `app/ai/routing_service.py`，形成稳定的代码生成类型路由。
2. 实现 `/api/app/chat/gen/code` SSE 流式接口。
3. 实现 HTML 模式代码生成。
4. 实现生成文件路径安全校验和落盘。
5. 生成结束后写入 `chat_history`。
6. 通过前端真实聊天页面联调。
7. 再扩展多文件模式、Vue 工程模式和 LangGraph 工作流。
