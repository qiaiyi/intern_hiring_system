from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import engine, Base
import models   # 确保模型被加载，以便建表
from auth import router as auth_router
from jobs import router as jobs_router
from applications import router as applications_router
from config import CORS_ORIGINS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时自动建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时释放连接池
    await engine.dispose()

app = FastAPI(title="实习招聘管理系统", lifespan=lifespan)

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
    uvicorn.run("main:app", reload=True)