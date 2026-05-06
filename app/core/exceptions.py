from enum import Enum


class ErrorCode(Enum):
    # 业务状态码定义，保持和原 Java ErrorCode 枚举一致。
    SUCCESS = (0, "ok")
    PARAMS_ERROR = (40000, "请求参数错误")
    NOT_LOGIN_ERROR = (40100, "未登录")
    NO_AUTH_ERROR = (40101, "无权限")
    NOT_FOUND_ERROR = (40400, "请求数据不存在")
    FORBIDDEN_ERROR = (40300, "禁止访问")
    SYSTEM_ERROR = (50000, "系统内部异常")
    OPERATION_ERROR = (50001, "操作失败")

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message


class BusinessException(Exception):
    # 自定义业务异常，对应 Java BusinessException。
    def __init__(self, error_code: ErrorCode, message: str | None = None) -> None:
        self.error_code = error_code
        self.code = error_code.code
        self.message = message or error_code.message
        super().__init__(self.message)


def throw_if(
    condition: bool,
    error_code: ErrorCode,
    message: str | None = None,
) -> None:
    # 条件成立时抛出业务异常，对应 Java ThrowUtils.throwIf。
    if condition:
        raise BusinessException(error_code, message)
