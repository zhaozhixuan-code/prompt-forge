from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    # 保持和原 Java 前端协议一致，字段继续使用驼峰命名。
    userAccount: str = Field(min_length=1)
    userPassword: str = Field(min_length=1)
    checkPassword: str = Field(min_length=1)


class UserVO(BaseModel):
    # from_attributes 允许直接把 SQLAlchemy User 对象转换为响应 VO。
    model_config = ConfigDict(from_attributes=True)

    id: int
    userAccount: str
    userName: str | None = None
    userAvatar: str | None = None
    userProfile: str | None = None
    userRole: str
