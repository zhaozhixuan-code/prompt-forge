"""第五课：LangGraph 基础工作流。"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

CodeGenType = Literal["html", "multi-file", "vue_project"]


class CodegenState(TypedDict, total=False):
    """LangGraph 在节点之间传递的状态。"""

    # 判断生成类型
    user_prompt: str
    # 规划文件列表
    code_gen_type: CodeGenType
    # 检查文件路径安全
    planned_files: list[str]
    # 生成成功结果
    safety_passed: bool
    # 生成失败结果
    result: str


def route_codegen_type(state: CodegenState) -> CodegenState:
    """根据用户需求选择代码生成类型。"""

    user_prompt = state["user_prompt"]
    prompt_lower = user_prompt.lower()
    if "vue" in prompt_lower or "vue3" in prompt_lower:
        code_gen_type: CodeGenType = "vue_project"
    elif "多个文件" in user_prompt or "css" in prompt_lower or "javascript" in prompt_lower:
        code_gen_type = "multi-file"
    else:
        code_gen_type = "html"

    return {"code_gen_type": code_gen_type}


def plan_files(state: CodegenState) -> CodegenState:
    """根据代码生成类型规划文件列表。"""

    code_gen_type = state["code_gen_type"]
    if code_gen_type == "vue_project":
        planned_files = ["package.json", "index.html", "src/App.vue", "src/main.ts"]
    elif code_gen_type == "multi-file":
        planned_files = ["index.html", "style.css", "script.js"]
    else:
        planned_files = ["index.html"]

    return {"planned_files": planned_files}


def check_file_safety(state: CodegenState) -> CodegenState:
    """检查规划文件是否包含不安全路径。"""

    planned_files = state["planned_files"]
    safety_passed = all(
        ".." not in path and not path.startswith(("/", "\\")) for path in planned_files
    )
    return {"safety_passed": safety_passed}


def build_success_result(state: CodegenState) -> CodegenState:
    """生成成功结果说明。"""

    files = ", ".join(state["planned_files"])
    return {
        "result": (
            f"推荐生成类型：{state['code_gen_type']}；"
            f"计划生成文件：{files}"
        )
    }


def build_rejected_result(state: CodegenState) -> CodegenState:
    """生成安全检查失败说明。"""

    return {"result": "文件规划未通过安全检查，已停止生成。"}


def choose_after_safety_check(state: CodegenState) -> Literal["success", "rejected"]:
    """根据安全检查结果选择后续节点。"""

    return "success" if state["safety_passed"] else "rejected"


def create_codegen_graph():
    """创建代码生成规划工作流。"""

    graph_builder = StateGraph(CodegenState)
    graph_builder.add_node("route_codegen_type", route_codegen_type)
    graph_builder.add_node("plan_files", plan_files)
    graph_builder.add_node("check_file_safety", check_file_safety)
    graph_builder.add_node("build_success_result", build_success_result)
    graph_builder.add_node("build_rejected_result", build_rejected_result)

    graph_builder.add_edge(START, "route_codegen_type")
    graph_builder.add_edge("route_codegen_type", "plan_files")
    graph_builder.add_edge("plan_files", "check_file_safety")
    # 条件分支
    graph_builder.add_conditional_edges(
        "check_file_safety",
        choose_after_safety_check,
        {
            "success": "build_success_result",
            "rejected": "build_rejected_result",
        },
    )
    graph_builder.add_edge("build_success_result", END)
    graph_builder.add_edge("build_rejected_result", END)
    return graph_builder.compile()


def main() -> None:
    """运行本课 demo。"""

    graph = create_codegen_graph()
    initial_state: CodegenState = {
        "user_prompt": "帮我做一个 HTML番茄钟应用，需要开始、暂停、重置按钮。"
    }

    print("=== 节点流式执行结果 ===")
    for step in graph.stream(initial_state):
        print(step)

    print("\n=== 最终状态 ===")
    final_state = graph.invoke(initial_state)
    print(final_state["result"])


if __name__ == "__main__":
    main()
