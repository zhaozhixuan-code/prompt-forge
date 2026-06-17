# PromptForge Python 后端逐步重构设计文档

## 1. 文档目标

本文档用于指导将现有 Java 后端单体项目逐步重构为 `PromptForge` Python 后端项目。

目标目录：

```text
E:\python_code\PromptForge
```

重构方式：

- 按模块逐步重构。
- 不一次性整体改造。
- 每迁移一个模块，都要尽量保持前端可以继续交互。

本次重构范围：

- Java 单体后端能力迁移到 Python 后端。
- 保持现有前端 API 交互协议兼容。

本次不重构：

- Java 微服务项目。
- 前端项目。

重构完成后，Python 后端应能替代原 Java 单体后端，为现有前端提供接口服务。

## 2. 总体技术选型

建议 Python 后端采用 FastAPI 单体架构。

推荐核心技术栈：

```text
FastAPI + Uvicorn + SQLAlchemy + Alembic + MySQL + Redis + OpenAI SDK + SSE
```

选择原因：

- FastAPI 适合构建 REST API，自动生成 OpenAPI 文档。
- FastAPI 原生适合异步场景，便于处理 AI 流式生成。
- SQLAlchemy 是 Python 主流 ORM，适合替代 MyBatis-Flex。
- Alembic 用于数据库版本管理。
- Redis 可承接登录态、缓存和限流。
- SSE 可兼容前端现有 AI 生成流式交互。

## 3. 第三方库清单

### 3.1 第一阶段建议安装

第一阶段目标是先让 Python 后端启动，并完成用户、应用基础接口和前端联调。

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
sqlalchemy
alembic
pymysql
redis
passlib[bcrypt]
itsdangerous
sse-starlette
openai
httpx
tenacity
aiofiles
pytest
pytest-asyncio
```

用途说明：

| 库 | 用途 |
|---|---|
| `fastapi` | Web 框架 |
| `uvicorn[standard]` | ASGI 服务启动器 |
| `pydantic` | 请求、响应和配置数据校验 |
| `pydantic-settings` | 环境变量配置管理 |
| `python-dotenv` | 本地 `.env` 配置读取 |
| `sqlalchemy` | ORM，替代 MyBatis-Flex |
| `alembic` | 数据库迁移管理 |
| `pymysql` | MySQL 驱动 |
| `redis` | Redis 客户端 |
| `passlib[bcrypt]` | 密码哈希 |
| `itsdangerous` | 签名 Cookie / Session token |
| `sse-starlette` | SSE 流式响应 |
| `openai` | OpenAI 兼容模型调用 |
| `httpx` | 异步 HTTP 请求 |
| `tenacity` | 重试机制 |
| `aiofiles` | 异步文件读取 |
| `pytest` | 测试框架 |
| `pytest-asyncio` | 异步测试支持 |

### 3.2 第二阶段建议安装

第二阶段用于增强 AI 工作流、监控、截图和对象存储能力。

```text
langchain
langgraph
prometheus-fastapi-instrumentator
structlog
cos-python-sdk-v5
playwright
dashscope
```

用途说明：

| 库 | 用途 |
|---|---|
| `langchain` | Prompt、模型调用和工具调用抽象 |
| `langgraph` | 替代 Java LangGraph4j 工作流 |
| `prometheus-fastapi-instrumentator` | Prometheus 指标 |
| `structlog` | 结构化日志 |
| `cos-python-sdk-v5` | 腾讯云 COS |
| `playwright` | 页面截图，替代 Selenium |
| `dashscope` | 阿里云 DashScope 调用 |

### 3.3 暂不建议第一阶段引入

```text
celery
rq
apscheduler
sqlmodel
```

原因：

- 当前目标是单体后端逐步替换，不需要一开始引入任务队列。
- 定时任务不是前端交互主链路。
- `SQLModel` 上手简单，但复杂查询和迁移生态不如直接使用 SQLAlchemy。

## 4. Python 项目整体结构设计

建议 `PromptForge` 作为 Python 后端项目根目录，结构如下：

```text
PromptForge/
  app/
    main.py
    api/
    core/
    db/
    models/
    schemas/
    repositories/
    services/
    ai/
    codegen/
    middlewares/
    utils/
  alembic/
  docs/
  tests/
  scripts/
  .env.example
  alembic.ini
  pyproject.toml
  README.md
```

设计原则：

- `api` 只负责 HTTP 入参、出参和路由。
- `services` 负责业务逻辑。
- `repositories` 负责数据库访问。
- `models` 负责 ORM 模型。
- `schemas` 负责请求 DTO 和响应 VO。
- `ai` 负责模型调用、Prompt、工具调用。
- `codegen` 负责代码解析、保存、构建和流式处理。
- `core` 负责配置、异常、统一响应、安全等基础能力。

## 5. 推荐目录结构

```text
PromptForge/
  app/
    main.py                         # FastAPI 入口
    api/
      __init__.py
      deps.py                       # 登录用户、数据库会话、权限依赖
      router.py                     # 汇总所有 API 路由，统一挂载 /api
      v1/
        __init__.py
        user.py                     # /api/user
        app.py                      # /api/app
        chat_history.py             # /api/chatHistory
        chat_group.py               # /api/chatGroup
        chat_group_member.py        # /api/chatGroupMember
        static_resource.py          # /api/static
        workflow.py                 # /api/workflow
        health.py                   # /api/health
    core/
      __init__.py
      config.py                     # 配置管理
      constants.py                  # 常量
      exceptions.py                 # 错误码、业务异常
      responses.py                  # BaseResponse / success / error
      security.py                   # 密码、Session、Cookie
      logging.py                    # 日志配置
    db/
      __init__.py
      base.py                       # SQLAlchemy Base
      session.py                    # engine 和 session
    models/
      __init__.py
      user.py
      app.py
      chat_history.py
      chat_group.py
      chat_group_member.py
    schemas/
      __init__.py
      common.py
      user.py
      app.py
      chat_history.py
      chat_group.py
      chat_group_member.py
    repositories/
      __init__.py
      user_repository.py
      app_repository.py
      chat_history_repository.py
      chat_group_repository.py
      chat_group_member_repository.py
    services/
      __init__.py
      user_service.py
      app_service.py
      chat_history_service.py
      chat_group_service.py
      chat_group_member_service.py
      project_download_service.py
      screenshot_service.py
    ai/
      __init__.py
      model_client.py               # OpenAI 兼容接口客户端
      routing_service.py            # 代码生成类型路由
      generator_service.py          # AI 代码生成
      prompts.py                    # Prompt 加载
      guardrails.py                 # 输入输出保护
      tools/
        __init__.py
        file_read.py
        file_write.py
        file_modify.py
        file_delete.py
        file_dir_read.py
        exit_tool.py
    codegen/
      __init__.py
      enums.py                      # 代码生成类型枚举
      parser.py                     # AI 输出解析
      saver.py                      # 代码保存
      stream_handler.py             # 流式处理和聊天记录写入
      vue_builder.py                # Vue 项目构建
      workflow.py                   # LangGraph 工作流
    middlewares/
      __init__.py
      cors.py
      session.py
      rate_limit.py
    utils/
      __init__.py
      path_utils.py
      time_utils.py
      pagination.py
  alembic/
  docs/
  tests/
  scripts/
  .env.example
  alembic.ini
  pyproject.toml
  README.md
```

## 6. Java 模块到 Python 模块映射

| Java 单体后端模块 | Python 模块 | 说明 |
|---|---|---|
| `controller` | `app/api/v1` | FastAPI 路由层 |
| `service` / `service.impl` | `app/services` | 业务逻辑 |
| `mapper` | `app/repositories` | 数据访问层 |
| `model/po` | `app/models` | SQLAlchemy ORM |
| `model/dto` | `app/schemas` | 请求模型 |
| `model/vo` | `app/schemas` | 响应模型 |
| `common/BaseResponse` | `app/core/responses.py` | 统一响应 |
| `exception` | `app/core/exceptions.py` | 错误码和业务异常 |
| `annotation/AuthCheck` | `app/api/deps.py` | 权限依赖 |
| `aop/AuthInterceptor` | `app/api/deps.py` 或 middleware | 鉴权 |
| `ratelimter` | `app/middlewares/rate_limit.py` | Redis 限流 |
| `ai` | `app/ai` | AI 模型、Prompt、工具 |
| `core/parser` | `app/codegen/parser.py` | 代码解析 |
| `core/saver` | `app/codegen/saver.py` | 代码保存 |
| `core/handler` | `app/codegen/stream_handler.py` | 流式处理 |
| `core/builder` | `app/codegen/vue_builder.py` | Vue 构建 |
| `langgraph4j` | `app/codegen/workflow.py` | Python LangGraph |
| `manager/CosManager` | `app/services/cos_service.py` | COS 对象存储 |
| `monitor` | `app/core/metrics.py` | Prometheus 指标 |

## 7. 接口兼容要求

为了让现有前端可以正常交互，Python 后端应优先保持以下兼容点。

### 7.1 服务地址

建议 Python 后端仍监听：

```text
http://localhost:8123
```

API 前缀仍为：

```text
/api
```

这样前端默认配置可以继续使用：

```text
http://localhost:8123/api
```

### 7.2 统一响应结构

建议保持类似 Java `BaseResponse` 的结构：

```json
{
  "code": 0,
  "data": {},
  "message": "ok"
}
```

错误响应也应保持同样结构，避免前端解析失败。

### 7.3 登录态

需要优先兼容：

```text
POST /api/user/register
POST /api/user/login
GET  /api/user/get/login
POST /api/user/logout
```

建议：

- 使用 Cookie 保存 Session ID。
- 使用 Redis 保存 Session 内容。
- 前端无需感知 Python 后端内部 Session 结构。

### 7.4 SSE 代码生成接口

必须优先兼容：

```text
GET /api/app/chat/gen/code?appId=1&message=xxx
```

响应头：

```text
Content-Type: text/event-stream
```

数据格式建议保持：

```text
data: {"d":"..."}
```

结束事件建议保持：

```text
event: done
data:
```

### 7.5 静态资源预览

前端通常会访问：

```text
/api/static/{codeGenType}_{appId}/
/api/static/vue_project_{appId}/dist/index.html
```

Python 后端需要保持生成目录命名规则：

```text
html_{appId}
multi-file_{appId}
vue_project_{appId}
```

注意：

- Java 后端多文件类型是 `multi-file`。
- Python 后端统一使用 `multi-file`，不再使用 `multi_file`。

## 8. 数据库设计

第一阶段建议沿用原 MySQL 表结构，不急于改表。

原因：

- 降低迁移风险。
- 方便 Java 后端和 Python 后端对照测试。
- 减少前端字段变更。

当前数据库名称：

```text
zzx_ai_code
```

当前数据库表设计文件：

```text
sql/zzx_ai_code.sql
```

该 SQL 文件是 Python 后端 ORM 模型、Schema、Repository 和 Alembic 初始迁移的主要依据。后续实现数据库层时，应优先参考该文件中的：

- 表名。
- 字段名。
- 字段类型。
- 默认值。
- 主键。
- 唯一索引。
- 普通索引。
- 逻辑删除字段。

需要迁移的核心表：

```text
user
app
chat_history
chat_group
chat_group_member
```

建议：

- ORM 字段可以先保持驼峰命名，例如 `userAccount`、`createTime`。
- JSON 响应字段也先保持驼峰命名。
- 等前端完全稳定后，再考虑 Python 风格字段转换。
- SQLAlchemy 模型字段应与 `sql/zzx_ai_code.sql` 保持一致，避免前端和数据库字段映射出现额外转换成本。

## 9. 按模块逐步重构计划

### 阶段 0：项目骨架

目标：

- 创建 FastAPI 项目基础结构。
- 配置 CORS。
- 配置统一响应。
- 配置统一异常。
- 配置 MySQL 和 Redis。
- 实现健康检查接口。

验收：

```text
GET /api/health
```

可以正常返回。

### 阶段 1：用户模块

迁移内容：

- 注册
- 登录
- 当前登录用户
- 退出
- 管理员用户管理接口

验收：

- 前端可以登录。
- 前端刷新后仍能获取当前用户。
- 退出后登录态清除。

### 阶段 2：应用基础模块

迁移内容：

- 创建应用
- 更新应用名称
- 删除应用
- 我的应用分页
- 精选应用分页
- 管理员应用分页和管理

验收：

- 前端首页可以创建应用。
- 我的应用列表可以展示。
- 管理端应用列表可以展示。

### 阶段 3：聊天历史模块

迁移内容：

- 查询应用聊天历史。
- 保存用户消息。
- 保存 AI 消息。
- 管理员查询聊天历史。

验收：

- 进入应用聊天页可以加载历史消息。
- AI 生成完成后聊天历史可回显。

### 阶段 4：AI 代码生成主链路

迁移内容：

- 代码生成类型路由。
- HTML 模式生成。
- 多文件模式生成。
- SSE 流式响应。
- AI 输出解析。
- 代码文件保存。
- 生成结束后写入聊天历史。

验收：

- 前端聊天页能收到 AI 流式输出。
- 生成文件能落盘。
- iframe 可以预览生成结果。

### 阶段 5：静态资源、下载、部署

迁移内容：

- `/api/static/**`
- `/api/app/download/{appId}`
- `/api/app/deploy`

验收：

- 生成应用可预览。
- 用户可下载自己的应用源码。
- 部署后可访问部署 URL。

### 阶段 6：Vue 工程模式

迁移内容：

- Vue 项目生成。
- AI 工具调用写文件。
- 执行 Node 构建。
- 预览 `dist/index.html`。

验收：

- `vue_project` 类型应用可以生成并构建。
- 前端 iframe 能正常访问。

### 阶段 7：工作流增强

迁移内容：

- 图片收集。
- Prompt 增强。
- 代码生成类型路由。
- 代码质量检查。
- 失败后重新生成。
- 构建节点。

验收：

- `/api/workflow` 相关接口可用。
- 工作流状态可以通过 SSE 返回。

### 阶段 8：监控、截图、对象存储

迁移内容：

- Prometheus 指标。
- AI 模型调用监控。
- 截图服务。
- 腾讯云 COS。
- DashScope / Pexels 图片能力。

验收：

- 指标可抓取。
- 截图功能可用。
- 对象存储上传可用。

## 10. 代码生成目录设计

建议配置：

```text
CODE_OUTPUT_ROOT_DIR=tmp/code_output
CODE_DEPLOY_ROOT_DIR=tmp/deploy
```

目录示例：

```text
PromptForge/
  tmp/
    code_output/
      html_1/
        index.html
      multi-file_2/
        index.html
        style.css
        script.js
      vue_project_3/
        package.json
        src/
        dist/
          index.html
    deploy/
      abc123/
        index.html
```

安全要求：

- 所有代码生成路径必须限制在 `CODE_OUTPUT_ROOT_DIR` 下。
- 所有部署路径必须限制在 `CODE_DEPLOY_ROOT_DIR` 下。
- 禁止用户输入直接拼接任意文件路径。
- 禁止目录穿越。
- 删除文件必须遵守本项目删除安全规范：只允许一次删除一个明确完整路径的单个文件。

## 11. Prompt 迁移设计

建议目录：

```text
PromptForge/
  app/
    ai/
      prompts/
        codegen_html_system_prompt.txt
        codegen_multi_file_system_prompt.txt
        codegen_vue_project_system_prompt.txt
        codegen_routing_system_prompt.txt
        code_quality_check_system_prompt.txt
        image_collection_plan_system_prompt.txt
        image_collection_system_prompt.txt
```

建议第一阶段直接复制原 Java 项目的 Prompt 文本，减少生成行为变化。

## 12. 配置文件设计

建议创建 `.env.example`：

```text
APP_ENV=local
SERVER_HOST=0.0.0.0
SERVER_PORT=8123

DATABASE_URL=mysql+pymysql://root:password@localhost:3306/zzx_ai_code
REDIS_URL=redis://:password@localhost:6379/0

SESSION_COOKIE_NAME=PF_SESSION
SESSION_EXPIRE_SECONDS=2592000

AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=replace-me
AI_MODEL=deepseek-chat
AI_ROUTING_TEMPERATURE=0
AI_ROUTING_MAX_ATTEMPTS=3
AI_REQUEST_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=0

CODE_OUTPUT_ROOT_DIR=tmp/code_output
CODE_DEPLOY_ROOT_DIR=tmp/deploy

COS_HOST=
COS_SECRET_ID=
COS_SECRET_KEY=
COS_BUCKET=
COS_REGION=

PEXELS_API_KEY=
DASHSCOPE_API_KEY=
DASHSCOPE_IMAGE_MODEL=
```

## 13. 异常和错误码设计

建议保持与 Java 项目类似的错误码：

```text
SUCCESS = 0
PARAMS_ERROR = 40000
NOT_LOGIN_ERROR = 40100
NO_AUTH_ERROR = 40101
NOT_FOUND_ERROR = 40400
FORBIDDEN_ERROR = 40300
SYSTEM_ERROR = 50000
OPERATION_ERROR = 50001
```

建议实现：

- `BusinessException`
- `ErrorCode`
- `throw_if`
- FastAPI 全局异常处理器

统一错误响应：

```json
{
  "code": 40000,
  "data": null,
  "message": "请求参数错误"
}
```

## 14. 权限设计

建议实现以下依赖函数：

```text
get_login_user
require_login
require_admin
require_app_owner
```

权限原则：

- 未登录用户不能访问需要登录的接口。
- 普通用户只能管理自己的应用。
- 管理员可以访问管理接口。
- 下载应用源码时必须校验创建者。
- 删除应用优先逻辑删除，不物理删除生成目录。

## 15. 前端兼容检查清单

每迁移一个模块，都要检查：

- API 路径是否一致。
- HTTP 方法是否一致。
- 请求参数位置是否一致。
- JSON 字段是否保持驼峰。
- 响应是否保持 `BaseResponse`。
- 分页结构是否兼容前端。
- Cookie 是否能被浏览器保存和发送。
- SSE 数据格式是否能被前端解析。
- 静态资源 URL 是否能 iframe 预览。
- CORS 是否允许前端开发端口访问。

## 16. 第一阶段最小可运行目标

第一阶段不要追求完整替代 Java 后端，先跑通主流程。

最小目标：

- Python 后端可以启动。
- `/api/health` 可用。
- MySQL 可连接。
- Redis 可连接。
- 用户注册、登录、获取当前用户、退出可用。
- 应用创建和查询可用。
- 前端可以连接 Python 后端完成登录和创建应用。

## 17. 主要风险点

### 17.1 SSE 格式风险

前端可能强依赖 Java 后端 SSE 数据格式。迁移前应查看前端 SSE 解析逻辑，Python 输出必须兼容。

### 17.2 Session 风险

不建议强行兼容 Java Spring Session 的 Redis 数据结构。Python 可以使用自己的 Session 结构，但 Cookie 行为要对前端透明。

### 17.3 文件写入风险

AI 工具调用写文件时，必须限制在生成目录内，不能覆盖项目源码或系统文件。

### 17.4 多文件枚举风险

Python 后端统一使用 `multi-file`，前端也应使用 `multi-file`，避免同一生成类型出现多套命名。

### 17.5 Vue 构建风险

Vue 工程模式依赖本机 Node.js 和 npm，建议后置迁移。

## 18. 不建议第一阶段做的事情

- 不重构微服务。
- 不重构前端。
- 不修改数据库表结构。
- 不一开始引入复杂任务队列。
- 不一开始完整复刻所有工作流。
- 不改变 API 路径。
- 不改变前端依赖的 JSON 字段。

## 19. 推荐推进顺序

```text
项目骨架
  -> 用户模块
  -> 应用基础模块
  -> 聊天历史模块
  -> AI SSE 代码生成主链路
  -> 静态资源预览
  -> 下载和部署
  -> Vue 工程模式
  -> 工作流增强
  -> 监控、截图、对象存储
```

每完成一个阶段，都用前端实际联调一次。只要前端能继续正常使用，就可以继续迁移下一个模块。

## 20. 总结

`PromptForge` 的 Python 重构应先服务于一个目标：让现有前端稳定接入 Python 后端。

建议先搭建 FastAPI 单体项目，保持原 Java 后端的 API 路径、响应结构、Cookie 登录态、SSE 格式和静态资源访问规则。数据库第一阶段沿用原 MySQL 表结构，不急于改表。

当登录、创建应用、AI 流式生成、生成结果预览这条链路跑通后，再逐步迁移下载、部署、Vue 工程模式、工作流、监控和对象存储。
