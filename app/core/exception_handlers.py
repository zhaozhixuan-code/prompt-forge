import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import BusinessException, ErrorCode
from app.core.response import error

logger = logging.getLogger(__name__)


def _error_response(error_code: ErrorCode, message: str | None = None) -> JSONResponse:
    # Java 后端业务异常通常仍返回 HTTP 200，具体失败原因放在 code/message 中。
    return JSONResponse(
        status_code=200,
        content=error(error_code, message).model_dump(),
    )


def _map_http_exception(exc: StarletteHTTPException) -> ErrorCode:
    # 将框架级 HTTP 异常映射成项目业务错误码。
    if exc.status_code == 401:
        return ErrorCode.NOT_LOGIN_ERROR
    if exc.status_code == 403:
        return ErrorCode.NO_AUTH_ERROR
    if exc.status_code == 404:
        return ErrorCode.NOT_FOUND_ERROR
    return ErrorCode.OPERATION_ERROR


def _http_exception_message(
    exc: StarletteHTTPException,
    error_code: ErrorCode,
) -> str:
    # 框架默认英文提示不暴露给前端，保持和 Java ErrorCode 的中文 message 一致。
    default_details = {
        "Unauthorized",
        "Forbidden",
        "Not Found",
        "Method Not Allowed",
    }
    if isinstance(exc.detail, str) and exc.detail not in default_details:
        return exc.detail
    return error_code.message


def register_exception_handlers(app: FastAPI) -> None:
    # 统一注册 FastAPI 全局异常处理器。
    @app.exception_handler(BusinessException)
    async def business_exception_handler(
        request: Request,
        exc: BusinessException,
    ) -> JSONResponse:
        logger.warning("BusinessException: %s %s", request.url.path, exc.message)
        return _error_response(exc.error_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning("RequestValidationError: %s %s", request.url.path, exc)
        return _error_response(ErrorCode.PARAMS_ERROR)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        logger.warning("HTTPException: %s %s", request.url.path, exc.detail)
        error_code = _map_http_exception(exc)
        return _error_response(error_code, _http_exception_message(exc, error_code))

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unexpected exception: %s", request.url.path, exc_info=exc)
        return _error_response(ErrorCode.SYSTEM_ERROR, "系统错误")
