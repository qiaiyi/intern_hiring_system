from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db_session
from models import User
from config import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session)
) -> User:
    """解析 JWT,返回当前登录用户对象"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录凭证无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 【修复】先判空再转 int：sub 缺失时 int(None) 会抛 TypeError（未被捕获→500），
        # 而正确行为应是返回 401 认证失败。
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    """返回一个依赖，校验当前用户角色"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role} 权限"
            )
        return current_user
    return role_checker