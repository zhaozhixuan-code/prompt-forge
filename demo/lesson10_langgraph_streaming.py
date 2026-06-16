"""第十课：LangGraph 流式事件。

本课演示的是“工作流节点状态流”，不是模型 token 流。

对比：
- 第三课 `chain.stream(...)`：模型生成文本时，一段一段吐 token/chunk。
- 本课 `graph.stream(...)`：LangGraph 每执行完一个节点，吐出该节点更新的状态。

这类事件适合映射到 PromptForge 后续 `/api/workflow` 或代码生成进度 SSE。
"""

import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class WorkflowState(TypedDict, total=False):
    """工作流状态。"""

    # 用户输入的原始需求。
    user_prompt: str
    # 路由节点判断出来的生成模式。
    route: str
    # 文件规划节点输出的文件列表。
    files: list[str]
    # 汇总节点输出的最终摘要。
    summary: str


def route(state: WorkflowState) -> WorkflowState:
    """选择生成模式。"""

    # 这里用关键词模拟路由。真实项目里可以替换为结构化模型调用。
    prompt_lower = state["user_prompt"].lower()
    route_name = "vue_project" if "vue" in prompt_lower else "html"
    # 节点只返回自己新增/更新的字段，LangGraph 会合并进全局 state。
    return {"route": route_name}


def plan(state: WorkflowState) -> WorkflowState:
    """规划文件。"""

    # plan 节点依赖 route 节点已经写入的 state["route"]。
    files = ["package.json", "src/App.vue"] if state["route"] == "vue_project" else ["index.html"]
    return {"files": files}


def summarize(state: WorkflowState) -> WorkflowState:
    """生成摘要。"""

    # summarize 节点依赖前两个节点的输出。
    return {"summary": f"{state['route']} -> {', '.join(state['files'])}"}


def create_streaming_graph():
    """创建可流式观察的 LangGraph。"""

    graph_builder = StateGraph(WorkflowState)

    # 注册节点：节点名用于 stream 输出和边连接。
    graph_builder.add_node("route", route)
    graph_builder.add_node("plan", plan)
    graph_builder.add_node("summarize", summarize)

    # 定义固定顺序：START -> route -> plan -> summarize -> END。
    graph_builder.add_edge(START, "route")
    graph_builder.add_edge("route", "plan")
    graph_builder.add_edge("plan", "summarize")
    graph_builder.add_edge("summarize", END)
    return graph_builder.compile()


def format_sse_event(event: dict) -> str:
    """把 LangGraph 节点更新包装成类 SSE data。"""

    # PromptForge 前端后续可以用类似格式接收工作流进度。
    # 这里不是标准接口实现，只是展示 SSE data 的文本形态。
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def main() -> None:
    """运行本课 demo。"""

    graph = create_streaming_graph()
    initial_state: WorkflowState = {"user_prompt": "做一个 Vue3 番茄钟应用"}

    print("=== LangGraph 节点事件 ===")
    # 每个 event 都是“某个节点刚刚返回的 state patch”。
    for event in graph.stream(initial_state):
        print(event)

    print("\n=== 类 SSE 输出 ===")
    # 同一条 graph 可以再次 stream。这里把每个节点事件包装成 SSE 文本。
    for event in graph.stream(initial_state):
        print(format_sse_event(event), end="")
    print("event: done\ndata:\n")


if __name__ == "__main__":
    main()
