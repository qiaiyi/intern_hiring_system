from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from app.core.config import CORS_ORIGINS
from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.applications import router as applications_router
from app.db.database import engine  # 【Alembic迁移】不再需要 Base，仅保留 engine 用于释放连接池

# 【新增】全局日志：此前整个后端没有任何 logging 配置，生产排障只能靠
# uvicorn 控制台；这里配置统一格式，uvicorn 自身的日志沿用其默认 handler。
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("recruitment")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 【Alembic迁移】启动时不再 create_all 建表，表结构统一由 Alembic 管理：
    # - 全新环境：先执行 alembic upgrade head 建库表
    # - 已有环境：执行一次 alembic stamp head 标记基线后，再通过迁移脚本升级
    yield
    # 关闭时释放连接池
    await engine.dispose()

app = FastAPI(title="实习招聘管理系统", lifespan=lifespan)

# 【新增】未处理异常兜底：记录完整堆栈到日志，但对客户端只返回统一的
# 500 文案，避免把内部细节（堆栈、SQL、路径等）泄露出去。
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})

# 【新增】允许跨域，供后续前端调用；来源白名单由环境变量 CORS_ORIGINS 控制
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(applications_router)



@app.get("/")
async def root():
    return {"message": "实习招聘管理系统 API"}



if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)