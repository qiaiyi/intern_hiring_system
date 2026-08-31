from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # 新增导入
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt

from app.core.config import SECRET_KEY, ALGORITHM, EXPIRE_MINUTES
from app.db.database import get_db_session
from app.models import User
from app.schemas import UserCreate, UserOut, Token  # 【清理】UserLogin 从未使用，登录走 OAuth2 表单

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    # 【修复】exp 必须用 UTC 时间：python-jose 编码 naive datetime 时会把它当作 UTC，
    # 此前用本地时间 datetime.now()，东八区下 token 实际有效期比配置长约 8 小时
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db_session: AsyncSession = Depends(get_db_session)):
    result = await db_session.execute(select(User).where(User.username == user_data.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        # 【清理】UserCreate.role 已带 Role.student 默认值，恒为真，直接取枚举的字符串值即可
        role=user_data.role.value,
        # 【新增】写入可选的基础资料字段
        name=user_data.name,
        email=user_data.email,
    )
    db_session.add(user)
    # 【修复】并发注册同名用户的竞态兜底（与问题 13 的投递去重同思路）：
    # 两个请求都通过上面的查重后，第二个 INSERT 会撞 username 唯一约束
    # 抛 IntegrityError，这里捕获并回滚返回 400，避免 500。
    try:
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="用户名已存在")
    await db_session.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), #使用表单，方便后续认证用户身份
                db_session: AsyncSession = Depends(get_db_session)):
    result = await db_session.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": user}