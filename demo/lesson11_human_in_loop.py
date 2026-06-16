"""第十一课：Human-in-the-loop 审批。

本课演示真正的 LangGraph interrupt/resume 流程：
1. 工作流规划一次 dry-run 写文件操作。
2. 到达审批节点时调用 `interrupt(...)` 暂停。
3. 外部“人工审批”通过 `Command(resume=...)` 把决定传回图。
4. 图从中断点继续执行 approve 或 reject 分支。

注意：本课不真实写文件，只演示高风险操作前的审批控制。
"""

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

ApprovalDecision = Literal["approve", "reject"]


class ApprovalState(TypedDict, total=False):
    """人工审批工作流状态。"""

    user_prompt: str
    # 计划写入的文件列表。真实项目里必须先做路径安全校验。
    planned_files: list[str]
    # 给人工审批界面展示的说明。
    approval_message: str
    # 人工审批结果：approve 或 reject。
    approval_decision: ApprovalDecision
    # 最终执行结果。
    result: str


def plan_write_operation(state: ApprovalState) -> ApprovalState:
    """规划一次 dry-run 写文件操作。"""

    # 这里固定规划 index.html，避免真实写文件。
    # 真实 PromptForge 中，这一步会来自 AI 生成计划或文件解析结果。
    return {
        "planned_files": ["index.html"],
        "approval_message": "准备写入 index.html，等待人工审批。",
    }


def request_human_approval(state: ApprovalState) -> ApprovalState:
    """暂停工作流，等待人工审批后继续。"""

    # interrupt 会让 graph.invoke(...) 立即返回一个 __interrupt__ 结果。
    # 这相当于告诉外部系统：“流程暂停了，需要人类给出决定”。
    decision = interrupt(
        {
            "message": state["approval_message"],
            "planned_files": state["planned_files"],
            "allowed_decisions": ["approve", "reject"],
        }
    )
    # 当外部使用 Command(resume="approve") 或 Command(resume="reject")
    # 恢复流程时，interrupt(...) 的返回值就是 resume 传入的值。
    return {"approval_decision": decision}


def route_by_approval(state: ApprovalState) -> Literal["execute", "reject"]:
    """根据审批结果选择路径。"""

    # 这是条件边的路由函数。它只负责返回分支名，不执行具体业务。
    return "execute" if state["approval_decision"] == "approve" else "reject"


def execute_dry_run(state: ApprovalState) -> ApprovalState:
    """审批通过后执行 dry-run，不真实写文件。"""

    # 即使审批通过，本课也只输出 dry-run 结果，不做任何文件写入。
    return {"result": f"审批通过，dry-run 计划写入：{', '.join(state['planned_files'])}"}


def reject_operation(state: ApprovalState) -> ApprovalState:
    """审批拒绝后停止流程。"""

    return {"result": "审批拒绝，已停止写入。"}


def create_approval_graph():
    """创建带 checkpointer 的人工审批工作流。"""

    graph_builder = StateGraph(ApprovalState)
    graph_builder.add_node("plan_write_operation", plan_write_operation)
    graph_builder.add_node("request_human_approval", request_human_approval)
    graph_builder.add_node("execute_dry_run", execute_dry_run)
    graph_builder.add_node("reject_operation", reject_operation)
    graph_builder.add_edge(START, "plan_write_operation")
    graph_builder.add_edge("plan_write_operation", "request_human_approval")

    # 审批节点恢复后，根据 approval_decision 选择继续执行还是拒绝。
    graph_builder.add_conditional_edges(
        "request_human_approval",
        route_by_approval,
        {"execute": "execute_dry_run", "reject": "reject_operation"},
    )
    graph_builder.add_edge("execute_dry_run", END)
    graph_builder.add_edge("reject_operation", END)
    # interrupt/resume 必须配合 checkpointer。
    # checkpointer 用来保存“暂停时的图状态”，这样 resume 才知道从哪里继续。
    return graph_builder.compile(checkpointer=InMemorySaver())


def run_approval_path(decision: ApprovalDecision, thread_id: str) -> str:
    """运行一次暂停、审批、恢复流程。"""

    graph = create_approval_graph()
    # 每条审批流程必须有 thread_id，否则 checkpointer 无法区分不同执行实例。
    config = {"configurable": {"thread_id": thread_id}}
    initial_state: ApprovalState = {"user_prompt": "生成一个 HTML 首页"}

    # 第一次 invoke 会执行到 interrupt，然后返回 __interrupt__。
    interrupted = graph.invoke(initial_state, config=config)

    # 模拟外部审批系统把人工决定传回图。
    resume_payload = Command(resume=decision)

    # 第二次 invoke 使用同一个 thread_id，LangGraph 从中断点继续执行。
    resumed = graph.invoke(resume_payload, config=config)

    # __interrupt__[0].value 是 request_human_approval 传给 interrupt 的审批信息。
    interrupt_value = interrupted["__interrupt__"][0].value
    return "\n".join(
        [
            f"暂停请求：{interrupt_value}",
            f"人工审批：{decision}",
            resumed["result"],
        ]
    )


def main() -> None:
    """运行本课 demo。"""

    print("=== approve 路径 ===")
    print(run_approval_path("approve", "lesson11-approve"))

    print("\n=== reject 路径 ===")
    print(run_approval_path("reject", "lesson11-reject"))


if __name__ == "__main__":
    main()
