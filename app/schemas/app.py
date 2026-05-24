from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.schemas.user import UserVO


class AppAddRequest(BaseModel):
    # 创建应用阶段先只要求 initPrompt，兼容 Java AppAddRequest。
    initPrompt: str = Field(min_length=1)


class AppUpdateRequest(BaseModel):
    # 普通用户只能更新自己的应用名称。
    id: int
    appName: str | None = None


class AppAdminUpdateRequest(BaseModel):
    # 管理员更新字段对齐 Java AppAdminUpdateRequest。
    id: int
    appName: str | None = None
    cover: str | None = None
    priority: int | None = None


class AppDeleteRequest(BaseModel):
    # 对齐 Java DeleteRequest。
    id: int


class AppQueryRequest(BaseModel):
    # 兼容 Java PageRequest，同时保留 current 方便前端分页组件使用。
    current: int = Field(default=1, ge=1)
    pageNum: int | None = Field(default=None, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    sortField: str | None = None
    sortOrder: str = "descend"

    id: int | None = None
    appName: str | None = None
    cover: str | None = None
    initPrompt: str | None = None
    codeGenType: str | None = None
    deployKey: str | None = None
    priority: int | None = None
    userId: int | None = None

    @model_validator(mode="after")
    def sync_java_page_num(self) -> "AppQueryRequest":
        # Java DTO 使用 pageNum；传入 pageNum 时同步到 current。
        if self.pageNum is not None:
            self.current = self.pageNum
        return self


class AppVO(BaseModel):
    # from_attributes 允许直接把 SQLAlchemy App 对象转换为 VO。
    model_config = ConfigDict(from_attributes=True)

    id: int
    appName: str | None = None
    cover: str | None = None
    initPrompt: str | None = None
    codeGenType: str | None = None
    deployKey: str | None = None
    deployedTime: datetime | None = None
    priority: int = 0
    userId: int
    createTime: datetime | None = None
    updateTime: datetime | None = None
    user: UserVO | None = None

    @field_serializer("id", "userId")
    def serialize_bigint(self, value: int) -> str:
        # MySQL bigint 可能超过 JavaScript 安全整数范围，对外统一序列化为字符串。
        return str(value)


class AppAdminVO(AppVO):
    # 管理端详情当前复用 AppVO 字段，后续可追加内部管理字段。
    editTime: datetime | None = None


class AppPageVO(BaseModel):
    # 同时返回 Python 当前字段和 Java Page 常见字段，降低前端适配成本。
    records: list[AppVO]
    total: int
    size: int
    current: int
    pages: int
    pageNum: int
    pageSize: int
    totalRow: int
