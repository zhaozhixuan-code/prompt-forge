# PromptForge 项目说明

## 项目定位

PromptForge 是从现有 Java 单体后端逐步重构而来的 Python 后端项目。项目目标是在不重构前端和不重构 Java 微服务项目的前提下，使用 Python 后端逐步替代原 Java 单体后端，并保持现有前端可以正常交互。

当前重构策略是按模块逐步迁移，而不是一次性整体改造。每完成一个模块，都应优先通过前端真实交互验证兼容性。

## 项目根目录

```text
E:\python_code\PromptForge
```

## 重构范围

允许处理：

- PromptForge Python 后端项目代码。
- Python 后端配置文件。
- Python 后端文档。
- Python 后端测试代码。

不处理，除非用户明确要求：

- Java 微服务项目。
- 前端项目。
- 与本 Python 后端无关的旧 Java 工程文件。

## 技术栈

### 运行环境

- Python 3.12+
- uv，作为 Python 依赖和虚拟环境管理工具。
- MySQL，沿用原项目数据库。
- Redis，用于 Session、缓存和限流。

### Web 框架

- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings

### 数据访问

- SQLAlchemy 2.x
- Alembic
- PyMySQL

### 登录态与安全

- Redis Session
- Cookie 登录态
- passlib[bcrypt]，用于密码哈希。
- itsdangerous，用于签名 token 或 Session ID。

### AI 能力

第一阶段：

- OpenAI Python SDK，用于调用 OpenAI 兼容接口。
- httpx，用于异步 HTTP 请求。
- tenacity，用于重试。
- sse-starlette，用于 SSE 流式输出。

后续阶段：

- LangChain
- LangGraph
- DashScope
- 腾讯云 COS Python SDK
- Playwright，用于网页截图。

### 测试与质量

- pytest
- pytest-asyncio
- FastAPI TestClient 或 httpx

## 依赖管理

本项目推荐使用 `pyproject.toml` 管理依赖，使用 `uv` 安装和运行。

常用命令：

```powershell
uv add fastapi "uvicorn[standard]"
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123
```

`pyproject.toml` 类似 Java 项目中的 `pom.xml`，`dependencies` 字段用于声明第三方库。

## 推荐项目结构

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
  AGENTS.md
```

## 模块职责

- `app/main.py`：FastAPI 应用入口。
- `app/api/`：接口路由层，只处理 HTTP 入参、出参、依赖注入和权限声明。
- `app/core/`：配置、常量、异常、统一响应、安全、日志。
- `app/db/`：数据库连接、Session、ORM Base。
- `app/models/`：SQLAlchemy ORM 模型。
- `app/schemas/`：请求 DTO 和响应 VO。
- `app/repositories/`：数据库访问层。
- `app/services/`：业务逻辑层。
- `app/ai/`：模型调用、Prompt、AI 工具、guardrail。
- `app/codegen/`：代码解析、保存、构建、SSE 流处理和工作流。
- `app/middlewares/`：CORS、Session、限流等中间件。
- `app/utils/`：通用工具函数。
- `tests/`：测试代码。
- `docs/`：项目文档。

## 开发阶段

### 阶段 0：项目骨架

目标：

- 创建 FastAPI 基础项目。
- 配置统一 API 前缀 `/api`。
- 配置 CORS。
- 配置统一响应结构。
- 配置统一异常处理。
- 配置 MySQL 和 Redis 连接。
- 实现 `/api/health`。

验收标准：

- Python 后端可以在 `8123` 端口启动。
- `GET /api/health` 正常返回。

### 阶段 1：用户模块

目标：

- 注册。
- 登录。
- 获取当前登录用户。
- 退出登录。
- 管理员用户管理接口。

验收标准：

- 前端可以正常注册、登录、刷新登录态和退出。

### 阶段 2：应用基础模块

目标：

- 创建应用。
- 更新应用名称。
- 删除应用。
- 查询我的应用。
- 查询精选应用。
- 管理员应用管理。

验收标准：

- 前端首页可以创建应用。
- 我的应用列表和管理端应用列表可以正常展示。

### 阶段 3：聊天历史模块

目标：

- 查询应用聊天历史。
- 保存用户消息。
- 保存 AI 消息。
- 管理员查询聊天历史。

验收标准：

- 进入应用聊天页可以加载历史消息。
- AI 生成后聊天历史可回显。

### 阶段 4：AI 代码生成主链路

目标：

- 代码生成类型路由。
- HTML 模式生成。
- 多文件模式生成。
- SSE 流式返回。
- AI 输出解析。
- 代码文件保存。
- 生成结束后写入聊天历史。

验收标准：

- 前端聊天页可以收到流式输出。
- 生成文件能落盘。
- iframe 可以预览生成结果。

### 阶段 5：静态资源、下载、部署

目标：

- `/api/static/**`
- `/api/app/download/{appId}`
- `/api/app/deploy`

验收标准：

- 生成应用可预览。
- 用户可下载自己的应用源码。
- 部署后可访问部署 URL。

### 阶段 6：Vue 工程模式

目标：

- Vue 项目生成。
- AI 工具调用写文件。
- 调用 Node 构建。
- 预览 `dist/index.html`。

验收标准：

- `vue_project` 类型应用可以生成、构建和预览。

### 阶段 7：工作流增强

目标：

- 图片收集。
- Prompt 增强。
- 路由。
- 代码质量检查。
- 失败后重新生成。
- 构建节点。

验收标准：

- `/api/workflow` 相关接口可用。
- 工作流状态可以通过 SSE 返回。

### 阶段 8：监控、截图、对象存储

目标：

- Prometheus 指标。
- AI 模型调用监控。
- 截图服务。
- 腾讯云 COS。
- DashScope / Pexels 图片能力。

验收标准：

- 指标可抓取。
- 截图功能可用。
- 对象存储上传可用。

## 前端兼容原则

Python 后端需要优先兼容现有前端，不要轻易修改接口协议。

保持兼容：

- 服务端口默认使用 `8123`。
- API 前缀使用 `/api`。
- 统一响应结构类似：

```json
{
  "code": 0,
  "data": {},
  "message": "ok"
}
```

- JSON 字段第一阶段尽量保持原 Java 项目的驼峰命名。
- 登录态使用 Cookie，前端不应感知内部 Session 实现。
- SSE 代码生成接口保持：

```text
GET /api/app/chat/gen/code?appId=1&message=xxx
```

- SSE 数据格式尽量保持：

```text
data: {"d":"..."}
event: done
data:
```

- 静态资源访问路径保持：

```text
/api/static/{codeGenType}_{appId}/
/api/static/vue_project_{appId}/dist/index.html
```

## 数据库原则

第一阶段建议沿用原 MySQL 表结构，不主动改表。

核心表：

- `user`
- `app`
- `chat_history`
- `chat_group`
- `chat_group_member`

字段命名：

- 数据库列名可继续使用原 Java 项目的驼峰字段。
- Python 对外 JSON 字段第一阶段也保持驼峰，减少前端改动。

## 编码规范

- 优先使用类型标注。
- API 层不要堆业务逻辑，业务逻辑放到 `services`。
- 数据库查询封装到 `repositories`。
- 统一使用 `pathlib.Path` 处理文件路径。
- 所有用户输入路径都必须做根目录限制和目录穿越检查。
- 异常统一通过业务异常和全局异常处理返回。
- 对外响应统一走 `BaseResponse` 风格。
- 新增复杂逻辑时补充必要测试。

## 文件安全规范

### 删除安全

严禁执行任何批量删除操作，包括但不限于：

- `del /s`
- `rd /s`
- `rmdir /s`
- `Remove-Item -Recurse`
- `rm -rf`
- 任何具有递归或批量删除效果的命令或脚本

仅允许删除单个文件，且必须满足：

- 提供明确、完整的文件路径。
- 删除操作一次只针对一个文件。

允许示例：

```powershell
Remove-Item "C:\path\to\file.txt"
```

遇到以下情况必须停止删除：

- 用户请求删除多个文件。
- 用户请求删除目录。
- 删除范围不明确。
- 使用通配符。

不得通过循环、脚本拼接或其他变通方式规避删除限制。

### 生成代码安全

- AI 生成文件只能写入配置的代码输出目录。
- 部署文件只能写入配置的部署目录。
- 禁止写入项目根目录外的任意路径。
- 禁止覆盖 `.env`、`pyproject.toml`、源码文件等关键项目文件，除非用户明确要求。

## 运行命令

开发启动：

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123
```

运行测试：

```powershell
uv run pytest
```

同步依赖：

```powershell
uv sync
```

添加依赖：

```powershell
uv add package-name
```

## 当前优先级

当前优先级是先完成 Python 后端第一阶段最小可运行链路：

1. 项目骨架。
2. `/api/health`。
3. 统一响应。
4. 统一异常。
5. 配置管理。
6. MySQL / Redis 连接。
7. 用户登录态。
8. 应用基础接口。

在这些完成之前，不优先处理复杂工作流、截图、对象存储和完整 Vue 工程生成。
