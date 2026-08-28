from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # 新增导入
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt
import bcrypt

from database import get_db_session
from models import User
from schemas import UserCreate, UserLogin, UserOut, Token
from config import SECRET_KEY, ALGORITHM, EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=EXPIRE_MINUTES)
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
    )
    db_session.add(user)
    await db_session.commit()
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