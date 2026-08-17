import base64    #解析 Basic Auth 请求头编码
import hashlib   #hashlib.sha256：密码单向哈希加密
import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status  #Request 获取请求头、Depends 依赖注入、HTTPException 抛 401/403 错误
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import UserAccount


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()   #加密密码的方法  bootstrap 初始化管理员账号时，把 admin123 加密存入 password_hash 字段


def verify_password(password: str, hashed: str) -> bool:    #判断密码是否一致的方法， 判断输入密码和数据库里的加密密码是否一致
    return hmac.compare_digest(hash_password(password), hashed)


def _credentials(request: Request) -> tuple[str, str]:    #从请求头取出密码的方法
    header = request.headers.get("authorization", "")   #取出请求头 Authorization，请求头的前缀格式Authorization: Basic dXNlcjE6cGFzc3dvcmQ=，
    if not header.lower().startswith("basic "):   #判断前缀是不是 Basic ，不是直接抛出 401 未登录
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Basic authorization")
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")  #分割 Basic 后面的 base64 字符串，解码得到 username:password
        username, password = decoded.split(":", 1)
        return username, password
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Basic authorization") from exc


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> UserAccount:  #从数据库中取出用户信息  使用了上边的方法，返回用户信息
    username, password = _credentials(request)
    user = db.query(UserAccount).filter(UserAccount.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    return user


def require_admin(user: Annotated[UserAccount, Depends(current_user)]) -> UserAccount: #判断用户是否是管理员
    if "ROLE_ADMIN" not in user.roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user

