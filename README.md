# 实习招聘管理系统 API

一个基于 FastAPI + SQLAlchemy 的实习招聘系统后端，提供用户注册/登录、岗位发布、岗位投递与投递状态管理等接口。

## 技术栈

- **Web 框架**：FastAPI
- **ORM**：SQLAlchemy（异步）
- **数据库**：MySQL（生产）/ SQLite（测试）
- **认证**：JWT（python-jose）+ bcrypt 密码哈希
- **校验**：Pydantic v2
- **测试**：pytest + pytest-asyncio + httpx

## 目录结构

```
.
├── main.py            # 应用入口，注册路由与 CORS 中间件
├── config.py          # 环境变量加载与启动校验
├── database.py        # 异步引擎、会话工厂
├── models.py          # SQLAlchemy 模型（User / Job / Application）
├── schemas.py         # Pydantic 请求/响应模型
├── auth.py            # 注册、登录、JWT 签发
├── jobs.py            # 岗位 CRUD
├── applications.py    # 投递与状态管理
├── dependencies.py    # 依赖注入（当前用户、角色校验）
├── pagination.py      # 通用分页工具
├── tests/             # 单元测试
└── requirements.txt   # 锁定版本的依赖清单
```

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例文件并按需修改：

```bash
cp .env.example .env
```

需要配置的变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | 数据库连接地址（异步驱动） | `mysql+aiomysql://root:password@localhost/recruitment` |
| `SECRET_KEY` | JWT 签名密钥，**务必替换为随机长字符串** | 任意足够长的随机串 |
| `SQL_ECHO` | 是否打印 SQL 日志（`true`/`false`） | `false` |
| `CORS_ORIGINS` | CORS 允许来源白名单（逗号分隔） | `http://localhost:3000` |

> 注意：`DATABASE_URL` 与 `SECRET_KEY` 缺失时应用会在启动时报错并退出（fail-fast）。

### 3. 启动

应用启动时会自动建表（`create_all`），无需手动建库。

```bash
uvicorn main:app --reload
```

启动后访问：

- 接口文档（Swagger UI）：http://localhost:8000/docs
- 接口文档（ReDoc）：http://localhost:8000/redoc

## API 概览

### 认证 `/api/auth`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册（支持 `student` / `hr` 角色） | 公开 |
| POST | `/api/auth/login` | 登录，返回 JWT | 公开 |

登录采用 OAuth2 表单方式（`username` / `password`），成功后返回 `access_token`，后续请求通过 `Authorization: Bearer <token>` 携带。

### 岗位 `/api/jobs`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/jobs` | 发布岗位 | HR |
| GET | `/api/jobs` | 岗位列表（分页） | 公开 |
| GET | `/api/jobs/{job_id}` | 岗位详情 | 公开 |
| PUT | `/api/jobs/{job_id}` | 更新岗位 | 发布者 HR |
| DELETE | `/api/jobs/{job_id}` | 删除岗位 | 发布者 HR |

### 投递 `/api`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/jobs/{job_id}/apply` | 投递岗位 | 学生 |
| GET | `/api/my/applications` | 我的投递记录（分页） | 学生 |
| GET | `/api/jobs/{job_id}/applications` | 岗位投递列表（分页） | 发布者 HR |
| PUT | `/api/applications/{application_id}` | 更新投递状态 | 发布者 HR |

投递状态流转：`applied` → `screening` → `interview` → `offer` / `rejected`（`applied` 为投递初始态，HR 不可将其改回）。

### 分页约定

列表接口统一返回：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10,
  "pages": 0
}
```

通过查询参数 `page`（默认 1）、`page_size`（默认 10，最大 100）控制。

## 运行测试

```bash
pytest
```

测试使用 SQLite（aiosqlite）作为文件数据库，通过 `dependency_overrides` 注入测试会话，无需真实 MySQL 服务。

## 说明

- 密码强度校验：至少 8 位，且同时包含字母与数字。
- 同一学生对同一岗位仅可投递一次（数据库唯一约束 + 应用层校验双重保证）。
- CORS 默认允许本地开发端口；生产环境请在 `.env` 中将 `CORS_ORIGINS` 设为真实前端域名。
- 生产部署建议引入 Alembic 做数据库迁移（当前使用启动时 `create_all`，不会修改已有表结构）。
