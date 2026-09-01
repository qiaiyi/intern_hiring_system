# 【Docker部署】后端镜像：Python 3.11 slim 底座 + 项目锁定依赖
FROM python:3.11-slim

# 容器内建议关闭 SQL 回显，日志更干净；时区设为东八区，created_at 语义与本地一致
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /srv/app

# 先单独复制依赖清单再安装，利用 Docker 层缓存：
# 依赖不变时重构建不会重新 pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端运行所需的代码与 Alembic 迁移（不含 tests/ 等，见 .dockerignore）
COPY app/ app/
COPY alembic.ini ./
COPY migrations/ migrations/

EXPOSE 8000

# 【Docker部署】启动时自动迁移：先把库表升级到最新版本，再启动 API 服务。
# MySQL 容器首次初始化会内部重启一次，即使 compose 健康检查通过也可能短暂连不上，
# 因此对迁移做有界重试（最多 30 次 x 2 秒），避免竞态导致启动失败；
# 超出重试仍失败则退出（配置错误不该被无限掩盖）。多实例部署应把迁移挪到发布流程单独执行
CMD ["sh", "-c", "i=0; until alembic upgrade head; do i=$((i+1)); [ $i -ge 30 ] && echo '迁移重试超限，退出' && exit 1; echo \"等待数据库就绪，第 $i 次重试...\"; sleep 2; done; exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
