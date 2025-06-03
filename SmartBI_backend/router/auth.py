from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database.connection import DatabaseConnection
from api import auth as auth_api
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re
from jose import jwt, JWTError
import logging
from config import JWT_SECRET_KEY, JWT_ALGORITHM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["认证管理"])

# 用户类型别名
User = Dict[str, Any]

def get_db():
    db = DatabaseConnection.get_session()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """
    从请求头中获取并验证Token，返回当前用户信息
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="认证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not authorization:
        logger.error("Authorization header is missing")
        raise credentials_exception
    
    try:
        # 打印完整的authorization头部内容
        logger.info(f"Received authorization header: {authorization}")
        
        # 解析 Bearer token
        parts = authorization.split()
        if len(parts) != 2:
            logger.error(f"Invalid authorization format: {authorization}")
            raise credentials_exception
            
        scheme, token = parts
        if scheme.lower() != "bearer":
            logger.error(f"Invalid scheme: {scheme}")
            raise credentials_exception
            
        # 打印token信息
        logger.info(f"Attempting to decode token: {token[:10]}...")
        
        # 解码JWT token
        try:
            # 打印使用的密钥信息
            logger.info(f"Using JWT_SECRET_KEY: {JWT_SECRET_KEY[:5]}...")
            logger.info(f"Using JWT_ALGORITHM: {JWT_ALGORITHM}")
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            logger.info(f"Token decoded successfully. Payload: {payload}")
            
            user_id = payload.get("sub")
            if user_id is None:
                logger.error("User ID not found in token")
                raise credentials_exception
                
            try:
                user_id = int(user_id)
                logger.info(f"User ID extracted from token: {user_id}")
            except ValueError:
                logger.error(f"Invalid user ID format: {user_id}")
                raise credentials_exception
            
            # 从数据库获取用户信息
            from database.models import User as UserModel
            user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.isDelete == 0).first()
            if user is None:
                logger.error(f"User with ID {user_id} not found in database or is deleted")
                raise credentials_exception
                
            # 构建用户信息
            user_info = {
                "id": user.id,
                "userAccount": user.userAccount,
                "userName": user.userName,
                "userAvatar": user.userAvatar,
                "userRole": user.userRole,
                "createTime": user.createTime
            }
            logger.info(f"User info retrieved successfully: {user_info}")
            
            return user_info
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {str(e)}")
        raise credentials_exception

class UserLogin(BaseModel):
    userAccount: str = Field(..., description="登录账号", example="user123")
    userPassword: str = Field(..., description="登录密码", example="password@123")

    @validator('userAccount')
    def validate_account(cls, v):
        if len(v) < 4 or not v.isalnum():
            raise ValueError('账号长度至少4位，且只能包含字母和数字')
        return v

    @validator('userPassword')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v

class UserRegister(BaseModel):
    userAccount: str = Field(..., description="登录账号", example="new_user")
    userPassword: str = Field(..., description="登录密码", example="newPass@123")
    userName: str = Field(None, description="用户昵称", max_length=256, example="张三")
    userAvatar: str = Field(None, description="用户头像URL")
    userRole: str = Field('user', description="用户角色", example="user")

    @validator('userAccount')
    def validate_account(cls, v):
        if len(v) < 4 or not v.isalnum():
            raise ValueError('账号长度至少4位，且只能包含字母和数字')
        return v

    @validator('userPassword')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v

    @validator('userRole')
    def validate_role(cls, v):
        if v not in ['user', 'admin']:
            raise ValueError('用户角色只能是 user 或 admin')
        return v

@router.post("/login", summary="用户登录")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    
    - **userAccount**: 登录账号（至少4位，仅允许字母数字）
    - **userPassword**: 登录密码（至少8位）
    """
    result = auth_api.login_user(db, user.userAccount, user.userPassword)
    return result

@router.post("/register", summary="用户注册")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    - **userAccount**: 登录账号（至少4位，仅允许字母数字）
    - **userPassword**: 登录密码（至少8位）
    - **userName**: 用户昵称（可选）
    - **userAvatar**: 用户头像URL（可选）
    - **userRole**: 用户角色（可选，默认为user）
    """
    result = auth_api.register_user(db, user.dict(exclude_unset=True))
    return result

@router.get("/current-user", summary="获取当前用户信息")
async def get_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    需要在请求头中携带有效的Bearer Token
    """
    return {
        "code": 1,
        "data": current_user,
        "message": "获取成功"
    } 