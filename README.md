# 实习招聘管理系统

一个基于 FastAPI + SQLAlchemy 的实习招聘系统，后端提供用户注册/登录、岗位发布、岗位投递与投递状态管理等接口，前端基于 Streamlit 实现登录注册、岗位浏览与发布、投递管理。

## 技术栈

- **后端框架**：FastAPI（异步）
- **ORM**：SQLAlchemy 2.0（异步，aiomysql / aiosqlite）
- **数据库迁移**：Alembic（async 模板）
- **数据库**：MySQL（生产）/ SQLite（测试）
- **认证**：JWT（python-jose）+ bcrypt 密码哈希
- **校验**：Pydantic v2
- **前端**：Streamlit + requests
- **测试**：pytest + pytest-asyncio + httpx

## 目录结构

```
.
├── app/                    # 后端包
│   ├── main.py             # 应用入口，注册路由与 CORS 中间件（不含建表逻辑）
│   ├── core/               # config.py（环境变量加载与启动校验）
│   ├── db/                 # database.py（异步引擎/会话工厂）、base.py（声明式基类）
│   ├── models/             # SQLAlchemy 模型（user.py / job.py / application.py）
│   ├── schemas/            # Pydantic 模型（common.py / user.py / job.py / application.py）
│   ├── api/                # auth.py（注册/登录/JWT）、jobs.py（岗位 CRUD）、
│   │                       # applications.py（投递与状态管理）、dependencies.py（依赖注入）
│   └── utils/              # pagination.py（通用分页工具）
├── migrations/             # Alembic 迁移环境与版本脚本
├── frontend/               # Streamlit 前端
│   ├── streamlit_app.py    # 入口页（登录 / 注册）
│   ├── api_client.py       # 后端 API 封装
│   └── pages/              # 岗位浏览/发布、投递管理等页面
├── tests/                  # 单元测试
├── alembic.ini             # Alembic 配置（连接串由 env.py 从 .env 注入）
└── requirements.txt        # 锁定版本的依赖清单
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

### 3. 初始化数据库（Alembic 迁移）

表结构统一由 Alembic 管理，应用启动时**不再自动建表**：

```bash
# 全新空库：执行迁移，从零建出全部表
alembic upgrade head

# 已有数据的老库（升级前已用 create_all 建过表）：只需标记基线版本，
# 不会改动任何数据，之后即可正常使用增量迁移
alembic stamp head
```

### 4. 启动

```bash
# 后端 API
uvicorn app.main:app --reload

# Streamlit 前端（新开终端，在 frontend/ 目录下）
cd frontend
streamlit run streamlit_app.py
```

启动后访问：

- 接口文档（Swagger UI）：http://localhost:8000/docs
- 接口文档（ReDoc）：http://localhost:8000/redoc
- Streamlit 前端：http://localhost:8501

## 数据库迁移（Alembic）

表结构的演进流程：

```bash
# 1. 修改 app/models/ 下的模型后，自动生成增量迁移脚本
alembic revision --autogenerate -m "描述本次改动"

# 2. 人工检查 migrations/versions/ 下新生成的脚本（确认无误后再执行）

# 3. 应用到数据库
alembic upgrade head

# 其他常用命令
alembic history              # 查看迁移历史
alembic current              # 查看当前库所在的版本
alembic downgrade -1         # 回滚上一个版本
alembic stamp head           # 已有库（非迁移建出）标记基线，不动数据
```

说明：

- 数据库连接串复用 `.env` 中的 `DATABASE_URL`，由 `migrations/env.py` 注入，`alembic.ini` 中不存放密码。
- 迁移连接与项目一致使用异步驱动（async 模板）。
- 测试库（`tests/conftest.py`）有意继续使用 `create_all`：建表快、与业务代码同步，且规避 SQLite/MySQL 方言差异对迁移脚本的干扰；迁移脚本正确性以真实 MySQL 的验证为准。
- 修改 `alembic.ini` 时请保持纯 ASCII：Alembic 按系统区域编码（中文 Windows 为 GBK）读取该文件，写中文注释会导致解码失败。

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
| GET | `/api/my/applications` | 我的投递记录（分页，含岗位/投递人摘要） | 学生 |
| GET | `/api/jobs/{job_id}/applications` | 岗位投递列表（分页，含投递人姓名/邮箱） | 发布者 HR |
| PUT | `/api/applications/{application_id}` | 更新投递状态 | 发布者 HR |

投递状态流转：`applied` → `screening` → `interview` → `offer` / `rejected`（`applied` 为投递初始态，HR 不可将其改回，非法状态值由枚举校验拦截返回 422）。

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

通过查询参数 `page`（默认 1）、`page_size`（默认 10，最大 100）控制，非法值返回 422。

## Docker 部署（一键启动）

项目提供完整的容器化方案：MySQL、后端 API、Streamlit 前端各一个容器，由 Docker Compose 编排。

```bash
# 1. 在 .env 中设置两个变量（缺少时 compose 会拒绝启动）：
#    SECRET_KEY=xxx                    # JWT 签名密钥
#    MYSQL_ROOT_PASSWORD=xxx           # MySQL 容器 root 密码（仅容器内新库使用）

# 2. 构建并启动全部三个服务
docker compose up -d --build

# 3. 访问
#    前端：http://localhost:8501
#    接口文档：http://localhost:8000/docs

# 停止（数据保留在卷里，下次 up 继续用）
docker compose down
```

说明：

- **自动迁移**：后端容器启动时先执行 `alembic upgrade head` 再启动 uvicorn，空库自动建表；迁移带 2 秒间隔的有界重试（最多 30 次），规避 MySQL 首次初始化重启窗口的连接竞态。
- **数据持久化**：MySQL 数据存在命名卷 `mysql_data` 中，`docker compose down` 不丢数据（`down -v` 才会删除）。
- **网络安全**：MySQL 容器不向宿主机暴露端口，只在 compose 内网供后端访问；如需用数据库客户端连接，在 `docker-compose.yml` 中取消 ports 注释。
- **容器互联**：前端通过 `API_BASE_URL=http://backend:8000` 访问后端（compose 服务名即内网域名），后端通过 `mysql:3306` 访问数据库。
- 容器里的 MySQL 是全新空库，与你本机安装的 MySQL、现有数据互不影响；两种方式可以并存（本地开发用本机库，演示用 Docker）。

## 运行测试

```bash
pytest
```

测试使用 SQLite（aiosqlite）作为文件数据库，通过 `dependency_overrides` 注入测试会话，无需真实 MySQL 服务。

## 更新记录

### 2026-08-31

- **引入 Alembic 数据库迁移**（改进 15）：移除启动时 `create_all` 自动建表，表结构统一由 `migrations/` 版本脚本管理，支持增量升级与回滚；生成基线迁移 `02767e84e64c`，已有库通过 `alembic stamp head` 标记基线。详见《后端问题修复记录.txt》。
- **一批安全与健壮性修复**（问题 16-20）：JWT `exp` 改用 UTC（此前东八区下 token 实际有效期约为配置的 9 倍）；删除有投递记录的岗位返回 400（此前 500）；注册与更新岗位补并发唯一约束兜底（此前 500）；全部字符串字段补长度上限、密码补 72 字节上限（超长此前均为 500，现 422）。
- **工程化**（改进 21）：全局异常兜底（堆栈进日志、客户端只见统一 500 文案）+ logging 配置；新增 GitHub Actions CI（全量测试 + Alembic 空库迁移/一致性检查）；清理未使用的 `UserLogin` 模型。
- **项目结构重构**（改进 22）：后端 13 个平铺文件包化为 `app/`（core / db / models / schemas / api / utils，模型与 schema 按业务实体拆分），`git mv` 保留文件历史；CI 的 actions 版本升至 v5/v6。60 个测试 + 迁移一致性检查全绿。
- **Docker 容器化部署**（改进 23）：新增后端/前端 Dockerfile 与 `docker-compose.yml`（mysql + backend + frontend 三服务），MySQL 数据卷持久化、健康检查编排、后端启动时自动执行 Alembic 迁移（带连接竞态重试）；`docker compose up -d --build` 一键启动全栈并完成全链路功能验证。

### 2026-08-26 前后（问题修复批次，详见《后端问题修复记录.txt》）

- **新增 Streamlit 前端**：登录/注册入口页与岗位浏览、岗位发布、投递管理等页面；后端岗位发布增加 `(hr_id, title)` 数据库唯一约束（`uq_job_hr_title`）兜底并发防重。
- **投递与用户模型完善**（问题 13/14）：投递增加 `(job_id, student_id)` 唯一约束 `uq_application_job_student` 修复并发重复投递竞态，外键列补索引；投递列表返回岗位/投递人摘要（relationship 预加载），User 增加 `name` / `email` 字段。
- **分页功能**（问题 6/7）：三个列表接口统一分页（`Page[T]` 响应结构 + 通用分页工具），并修复非法分页参数返回 500 的问题（现返回 422）。
- **安全加固**（问题 1/4/5/8/11/12）：修复 JWT 缺 `sub` 时 500 错误（现返回 401）；新增 CORS 中间件并将来源白名单环境变量化；`DATABASE_URL` / `SECRET_KEY` 启动时 fail-fast 校验；注册密码强度校验（至少 8 位、含字母和数字）；依赖补齐 `python-multipart`。
- **工程规范**（问题 2/3/9/10）：投递状态枚举化校验；清理死代码；新增 `.env.example` 模板；requirements.txt 锁定全部依赖版本。

## 说明

- 密码强度校验：8~72 字节，且同时包含字母与数字；各字符串字段有长度上限（与数据库列宽一致），超限返回 422。
- 同一学生对同一岗位仅可投递一次（数据库唯一约束 + 应用层校验双重保证）；同一 HR 不能发布同名岗位。
- JWT 过期时间按 UTC 编码，默认 60 分钟。
- CORS 默认允许本地开发端口；生产环境请在 `.env` 中将 `CORS_ORIGINS` 设为真实前端域名。
- 数据库表结构变更必须走 Alembic 迁移（见上文「数据库迁移」章节），不要再用删表重建的方式。
- 未处理的异常会记录完整堆栈到日志，客户端只收到统一的 `{"detail": "服务器内部错误"}`。
- push / PR 会触发 GitHub Actions CI：全量 pytest + Alembic 迁移一致性检查（见 `.github/workflows/ci.yml`）。
