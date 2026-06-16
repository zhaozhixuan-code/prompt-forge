"""第九课：可靠结构化输出、重试和安全校验。

本课不调用模型，而是用模拟的模型输出来演示生产代码必须做的事情：
1. 使用 Pydantic 校验 AI 输出结构。
2. 字段缺失、枚举错误、危险路径都必须被拒绝。
3. 校验失败后允许有限次数重试。
4. 多次失败后返回明确兜底结果，而不是让业务崩溃。
"""

from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

CodeGenType = Literal["html", "multi-file", "vue_project"]


class GeneratedFile(BaseModel):
    """AI 计划生成的文件。"""

    # path 必须是相对路径，不能是绝对路径，也不能包含目录穿越。
    path: str = Field(description="相对文件路径")
    # content 在真实代码生成中会是文件正文。这里不写入磁盘，只做校验演示。
    content: str = Field(description="文件内容")

    @model_validator(mode="after")
    def validate_safe_path(self) -> "GeneratedFile":
        """拒绝目录穿越和绝对路径。"""

        # 同时用 Windows 和 POSIX 规则检查，是因为项目运行在 Windows，
        # 但 AI 可能返回 Linux 风格路径。两种都要防。
        windows_path = PureWindowsPath(self.path)
        posix_path = PurePosixPath(self.path)
        if (
            # 拒绝 C:\temp\a.txt、/tmp/a.txt、\server\share\a.txt 等绝对路径。
            windows_path.is_absolute()
            or posix_path.is_absolute()
            # `PureWindowsPath("C:foo").is_absolute()` 不一定覆盖所有 drive 场景，
            # 所以单独检查 drive，避免模型写到盘符路径。
            or windows_path.drive
            # 拒绝 ../secret.txt 或 a/../secret.txt。
            or ".." in windows_path.parts
            or ".." in posix_path.parts
        ):
            raise ValueError("文件路径必须是安全相对路径")
        return self


class CodegenPlan(BaseModel):
    """代码生成计划。"""

    # Literal 会拒绝模型发明的新类型，例如 react、web_app。
    codeGenType: CodeGenType
    # 嵌套模型会逐个校验文件路径安全。
    files: list[GeneratedFile]
    summary: str


def _fallback_plan(reason: str) -> CodegenPlan:
    """多次解析失败后的兜底结果。"""

    # 兜底结果也必须满足同一套 schema。
    # 这样调用方永远拿到 CodegenPlan，而不是 None 或异常。
    return CodegenPlan(
        codeGenType="html",
        files=[GeneratedFile(path="index.html", content="<!-- fallback -->")],
        summary=reason,
    )


def parse_with_retries(candidates: list[dict], max_retries: int = 2) -> tuple[CodegenPlan, list[str]]:
    """依次校验候选输出，失败后重试下一个候选。"""

    errors: list[str] = []
    # max_retries=2 表示：首次尝试 + 2 次重试，共 3 次候选。
    attempts = max_retries + 1
    # enumerate 用于同时获得下标和元素
    for attempt, candidate in enumerate(candidates[:attempts], start=1):
        try:
            # Pydantic 会同时校验：
            # - 必填字段是否存在。
            # - codeGenType 是否在 Literal 枚举内。
            # - files 内每个 GeneratedFile 是否通过路径安全校验。
            return CodegenPlan.model_validate(candidate), errors
        except ValidationError as exc:
            # demo 中把错误收集起来打印，真实服务里通常会记录日志，
            # 并把错误摘要加入下一次模型重试 prompt。
            errors.append(f"第 {attempt} 次失败：{exc.errors()}")

    return _fallback_plan("模型多次返回无效结构，已兜底为 html。"), errors


def main() -> None:
    """运行本课 demo。"""

    simulated_model_outputs = [
        # 第一次：字段完全不符合 schema。
        {"type": "web_app"},
        # 第二次：枚举值错误，同时路径包含目录穿越。
        {
            "codeGenType": "react",
            "files": [{"path": "../secret.txt", "content": "bad"}],
            "summary": "错误枚举和危险路径",
        },
        # 第三次：结构、枚举、路径都合法，应该被接受。
        {
            "codeGenType": "html",
            "files": [{"path": "index.html", "content": "<h1>Hello</h1>"}],
            "summary": "第三次返回合法结构",
        },
    ]

    plan, errors = parse_with_retries(simulated_model_outputs)
    print("=== 校验失败记录 ===")
    for error in errors:
        print(error)
    print("\n=== 最终可用计划 ===")
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
