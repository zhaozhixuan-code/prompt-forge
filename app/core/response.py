from typing import Generic, TypeVar

from pydantic import BaseModel

from app.core.exceptions import ErrorCode

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    # 兼容原 Java 后端的统一响应结构。
    code: int = 0
    data: T | None = None
    message: str = "ok"

    @classmethod
    def ok(cls, data: T | None = None, message: str = "ok") -> "BaseResponse[T]":
        # 成功响应的快捷构造方法，对应 Java ResultUtils.success(data)。
        return cls(code=ErrorCode.SUCCESS.code, data=data, message=message)

    @classmethod
    def error(
        cls,
        error_code: ErrorCode,
        message: str | None = None,
    ) -> "BaseResponse[None]":
        # 失败响应的快捷构造方法，对应 Java ResultUtils.error(errorCode, message)。
        return cls(
            code=error_code.code,
            data=None,
            message=message or error_code.message,
        )


def success(data: T | None = None) -> BaseResponse[T]:
    # 函数形式的成功响应，方便接口层直接 return success(data)。
    return BaseResponse.ok(data)


def error(error_code: ErrorCode, message: str | None = None) -> BaseResponse[None]:
    # 函数形式的失败响应，方便异常处理器统一构造错误返回。
    return BaseResponse.error(error_code, message)
