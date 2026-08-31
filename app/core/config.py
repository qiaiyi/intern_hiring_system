import os
from dotenv import load_dotenv

# 加载项目根目录下的 .env 文件
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60

# 【新增】启动时 fail-fast 校验关键配置，避免缺失时到运行期才暴露问题
if not DATABASE_URL:
    raise RuntimeError("缺少环境变量 DATABASE_URL，请在 .env 中配置数据库连接地址")
if not SECRET_KEY:
    raise RuntimeError("缺少环境变量 SECRET_KEY，请在 .env 中配置 JWT 签名密钥")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# 【新增】CORS 允许的来源白名单：逗号分隔的域名列表。
# 未配置时回退到本地开发常用端口，生产环境必须显式配置真实前端域名。
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]