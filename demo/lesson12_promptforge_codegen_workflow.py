"""第十二课：PromptForge 代码生成工作流综合演示。

本课把前面课程的核心思想组合成一个 PromptForge 风格 dry-run 工作流：
1. 判断代码生成类型。
2. 根据类型规划文件。
3. 做路径安全校验。
4. 模拟生成文件内容。
5. 用 graph.stream(...) 输出节点进度。
6. 返回最终状态。

本课明确不真实写文件、不执行构建、不部署，只展示工作流骨架。
"""

import json
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

CodeGenType = Literal["html", "multi-file", "vue_project"]


class CapstoneState(TypedDict, total=False):
    """综合代码生成 dry-run 状态。"""

    user_prompt: str
    # 对外字段沿用 PromptForge/Java 侧常见的 camelCase 命名。
    codeGenType: CodeGenType
    plannedFiles: list[str]
    safetyPassed: bool
    # generatedPreview 只是内存预览，不会落盘。
    generatedPreview: dict[str, str]
    # streamEvents 用来模拟后续 SSE 可发送的进度事件。
    streamEvents: list[str]
    finalSummary: str


def append_event(state: CapstoneState, event: str) -> list[str]:
    """追加工作流事件。"""

    # LangGraph 节点通常返回 state patch。
    # 为了保留已有事件，需要读取旧列表并返回一个新列表。
    return [*state.get("streamEvents", []), event]


def is_safe_relative_path(path: str) -> bool:
    """校验路径必须是安全相对路径。"""

    # 同时检查 Windows 和 POSIX 风格路径，防止模型输出跨平台危险路径。
    windows_path = PureWindowsPath(path)
    posix_path = PurePosixPath(path)
    return not (
        # 拒绝绝对路径，例如 /tmp/a.txt 或 \server\share\a.txt。
        windows_path.is_absolute()
        or posix_path.is_absolute()
        # 拒绝 Windows 盘符路径，例如 C:\temp\a.txt。
        or windows_path.drive
        # 拒绝目录穿越，例如 ../a.txt 或 src/../a.txt。
        or ".." in windows_path.parts
        or ".." in posix_path.parts
    )


def classify_request(state: CapstoneState) -> CapstoneState:
    """结构化判断代码生成类型。"""

    # 这里用关键词模拟结构化路由。真实项目中可以替换为 Lesson 02 的
    # with_structured_output 或 app/ai/routing_service.py。
    prompt_lower = state["user_prompt"].lower()
    if "vue" in prompt_lower or "vue3" in prompt_lower:
        code_gen_type: CodeGenType = "vue_project"
    elif "多个文件" in state["user_prompt"] or "css" in prompt_lower or "javascript" in prompt_lower:
        code_gen_type = "multi-file"
    else:
        code_gen_type = "html"
    return {
        "codeGenType": code_gen_type,
        # 每个节点都追加一条事件，便于后续通过 SSE 展示进度。
        "streamEvents": append_event(state, f"classified:{code_gen_type}"),
    }


def plan_files(state: CapstoneState) -> CapstoneState:
    """根据生成类型规划文件。"""

    # 这一步只规划文件名，不生成内容、不写磁盘。
    if state["codeGenType"] == "vue_project":
        files = ["package.json", "index.html", "src/App.vue", "src/main.ts"]
    elif state["codeGenType"] == "multi-file":
        files = ["index.html", "style.css", "script.js"]
    else:
        files = ["index.html"]
    return {"plannedFiles": files, "streamEvents": append_event(state, "planned_files")}


def validate_paths(state: CapstoneState) -> CapstoneState:
    """校验规划文件路径安全。"""

    # 任何一个路径不安全，都应该阻止后续生成/写入流程。
    safety_passed = all(is_safe_relative_path(path) for path in state["plannedFiles"])
    return {
        "safetyPassed": safety_passed,
        "streamEvents": append_event(state, f"safety:{safety_passed}"),
    }


def simulate_generation(state: CapstoneState) -> CapstoneState:
    """模拟生成文件内容，不写入磁盘。"""

    # 真实项目里这里会调用模型生成文件内容。
    # 本课只生成内存里的占位内容，保证 demo 没有文件系统副作用。
    generated = {
        path: f"// dry-run generated content for {path}" for path in state["plannedFiles"]
    }
    return {
        "generatedPreview": generated,
        "streamEvents": append_event(state, "generated_preview"),
    }


def build_final_summary(state: CapstoneState) -> CapstoneState:
    """生成最终 dry-run 摘要。"""

    # finalSummary 是给调用方快速阅读的摘要。
    # 详细结构仍然保留在 final_state 其他字段中。
    summary = (
        f"codeGenType={state['codeGenType']}; "
        f"plannedFiles={state['plannedFiles']}; "
        f"safetyPassed={state['safetyPassed']}"
    )
    return {
        "finalSummary": summary,
        "streamEvents": append_event(state, "done"),
    }


def choose_after_safety(state: CapstoneState) -> Literal["generate", "finish"]:
    """安全检查通过才进入生成模拟。"""

    # 条件边只返回分支名：
    # - generate：继续模拟生成。
    # - finish：跳过生成，直接收尾。
    return "generate" if state["safetyPassed"] else "finish"


def create_capstone_graph():
    """创建 PromptForge dry-run 代码生成工作流。"""

    graph_builder = StateGraph(CapstoneState)

    # 注册节点。每个节点对应 PromptForge 代码生成链路中的一个明确步骤。
    graph_builder.add_node("classify_request", classify_request)
    graph_builder.add_node("plan_files", plan_files)
    graph_builder.add_node("validate_paths", validate_paths)
    graph_builder.add_node("simulate_generation", simulate_generation)
    graph_builder.add_node("build_final_summary", build_final_summary)
    graph_builder.add_edge(START, "classify_request")
    graph_builder.add_edge("classify_request", "plan_files")
    graph_builder.add_edge("plan_files", "validate_paths")

    # 安全检查后做条件分支。安全失败时不会进入 simulate_generation。
    graph_builder.add_conditional_edges(
        "validate_paths",
        choose_after_safety,
        {"generate": "simulate_generation", "finish": "build_final_summary"},
    )
    graph_builder.add_edge("simulate_generation", "build_final_summary")
    graph_builder.add_edge("build_final_summary", END)
    return graph_builder.compile()


def format_stream_event(event: dict) -> str:
    """把工作流节点输出包装成类 SSE data。"""

    # 这里复用 PromptForge 前端兼容的 SSE 思路：每个节点事件一条 data。
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def main() -> None:
    """运行本课 demo。"""

    graph = create_capstone_graph()
    initial_state: CapstoneState = {
        "user_prompt": "做一个 Vue3 番茄钟应用，需要开始、暂停、重置按钮。",
        "streamEvents": [],
    }

    print("=== dry-run 流式事件 ===")
    # stream 用于展示每个节点的状态更新，适合映射到前端进度条或日志。
    for event in graph.stream(initial_state):
        print(format_stream_event(event), end="")

    print("event: done\ndata:\n")
    print("=== 最终状态 ===")
    # invoke 用于一次性拿到完整最终状态，适合后端内部处理。
    final_state = graph.invoke(initial_state)
    print(json.dumps(final_state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
