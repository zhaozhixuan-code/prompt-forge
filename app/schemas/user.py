from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    # 保持和原 Java 前端协议一致，字段继续使用驼峰命名。
    userAccount: str = Field(min_length=1)
    userPassword: str = Field(min_length=1)
    checkPassword: str = Field(min_length=1)


class UserLoginRequest(BaseModel):
    # 登录接口字段名保持驼峰，兼容现有前端和原 Java DTO。
    userAccount: str = Field(min_length=1)
    userPassword: str = Field(min_length=1)


class UserAddRequest(BaseModel):
    # 管理员创建用户使用；字段保持驼峰，兼容原 Java 前端 DTO。
    userAccount: str = Field(min_length=1)
    userPassword: str | None = None
    userName: str | None = None
    userAvatar: str | None = None
    userProfile: str | None = None
    userRole: str = "user"


class UserUpdateRequest(BaseModel):
    # 管理员更新用户使用；None 表示该字段不更新。
    id: int
    userAccount: str | None = None
    userPassword: str | None = None
    userName: str | None = None
    userAvatar: str | None = None
    userProfile: str | None = None
    userRole: str | None = None


class UserDeleteRequest(BaseModel):
    # 沿用原 Java 项目常见的按 id 删除请求体。
    id: int


class UserQueryRequest(BaseModel):
    # 管理端分页查询参数；current/pageSize 命名保持和前端分页组件一致。
    current: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    id: int | None = None
    userAccount: str | None = None
    userName: str | None = None
    userProfile: str | None = None
    userRole: str | None = None


class UserVO(BaseModel):
    # from_attributes 允许直接把 SQLAlchemy User 对象转换为响应 VO。
    model_config = ConfigDict(from_attributes=True)

    id: int
    userAccount: str
    userName: str | None = None
    userAvatar: str | None = None
    userProfile: str | None = None
    userRole: str
    createTime: datetime | None = None


class UserAdminVO(UserVO):
    # 管理端可额外查看更新时间，但仍不暴露密码、逻辑删除标记等内部字段。
    updateTime: datetime | None = None


class UserPageVO(BaseModel):
    # 兼容 MyBatis-Plus Page 常见响应字段，方便现有前端直接消费。
    records: list[UserVO]
    total: int
    size: int
    current: int
    pages: int
