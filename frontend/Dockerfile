# 【Docker部署】前端镜像：Streamlit + requests，仅运行 frontend/ 内的代码
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /srv/frontend

# 先装依赖（利用层缓存），再复制页面代码
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# 0.0.0.0 监听是容器对外提供服务的前提；关闭 Streamlit 邮箱头，避免无谓告警
CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]
