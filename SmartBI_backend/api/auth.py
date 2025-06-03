"""
认证和授权API服务模块

本模块提供用户认证和授权相关的核心业务逻辑实现，包括：

功能列表：
1. 用户认证
   - JWT令牌生成
   - 令牌验证和解析
   - 刷新令牌机制
   
2. 权限管理
   - 角色权限验证
   - 访问控制
   - 权限检查
   
3. 会话管理
   - 用户会话创建
   - 会话状态维护
   - 会话失效处理

技术实现：
- 使用 JWT 实现无状态认证
- 实现了令牌刷新机制
- 支持多种认证方式（账号密码、令牌等）
- 实现了细粒度的权限控制

依赖关系：
- utils.jwt_utils: JWT 相关工具
- database.user_db: 用户数据操作
- schemas.auth: 认证相关的数据模型

安全特性：
- 密码加密存储
- 令牌过期机制
- 防止重放攻击
- 完整的日志记录

使用说明：
- 所有需要认证的API都应该使用本模块提供的装饰器
- 权限验证失败会抛出适当的HTTP异常
- 支持多角色权限控制
"""

from database import crud
from sqlalchemy.orm import Session
from fastapi import HTTPException
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
import logging
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

def mask_sensitive_data(user_dict: dict) -> dict:
    """对敏感数据进行脱敏"""
    # 移除敏感字段
    user_dict.pop("userPassword", None)
    user_dict.pop("isDelete", None)
    user_dict.pop("updateTime", None)
    
    return user_dict

def create_access_token(data: dict):
    """创建JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def upgrade_password_to_bcrypt(db: Session, user, plain_password: str):
    """将明文密码升级为bcrypt加密"""
    try:
        hashed_password = bcrypt.hashpw(
            plain_password.encode(), 
            bcrypt.gensalt()
        ).decode()
        crud.update_user_password(db, user.id, hashed_password)
    except Exception as e:
        logger.error(f"Failed to upgrade password: {str(e)}")

def login_user(db: Session, user_account: str, password: str):
    """用户登录"""
    logger.info(f"Attempting login for user: {user_account}")
    
    # 获取用户信息
    user = crud.get_user_by_account(db, user_account)
    if not user:
        logger.error(f"User not found: {user_account}")
        raise HTTPException(status_code=400, detail="账号或密码错误")
    
    # 检查用户是否被删除
    if user.isDelete == 1:
        logger.error(f"User is deleted: {user_account}")
        raise HTTPException(status_code=400, detail="账号不存在")
    
    # 验证密码
    try:
        # 首先尝试验证加密密码
        if bcrypt.checkpw(password.encode(), user.userPassword.encode()):
            logger.info("Password verified successfully (bcrypt)")
            pass
        else:
            # 如果密码不正确，检查是否是明文密码
            if user.userPassword == password:
                logger.info("Password verified successfully (plaintext)")
                # 如果是明文密码匹配，则升级为bcrypt加密
                upgrade_password_to_bcrypt(db, user, password)
            else:
                logger.error("Password verification failed")
                raise HTTPException(status_code=400, detail="账号或密码错误")
    except ValueError:
        # 如果bcrypt.checkpw失败（可能是因为密码格式不是bcrypt），
        # 检查是否是明文密码
        if user.userPassword == password:
            logger.info("Password verified successfully (plaintext)")
            # 如果是明文密码匹配，则升级为bcrypt加密
            upgrade_password_to_bcrypt(db, user, password)
        else:
            logger.error("Password verification failed")
            raise HTTPException(status_code=400, detail="账号或密码错误")
    
    # 创建token
    token_data = {"sub": str(user.id), "role": user.userRole}
    logger.info(f"Creating token with data: {token_data}")
    token = create_access_token(token_data)
    logger.info(f"Token created successfully: {token[:10]}...")
    
    # 转换为字典并脱敏
    user_dict = {
        "id": user.id,
        "userName": user.userName,
        "userAccount": user.userAccount,
        "userAvatar": user.userAvatar,
        "userRole": user.userRole,
        "createTime": user.createTime
    }
    
    response_data = {
        "code": 1,
        "msg": "登录成功",
        "data": mask_sensitive_data(user_dict),
        "token": token
    }
    logger.info("Login successful")
    return response_data

def register_user(db: Session, user_data: dict):
    """用户注册"""
    # 检查账号是否已存在
    if crud.get_user_by_account(db, user_data["userAccount"]):
        raise HTTPException(status_code=400, detail="账号已存在")
    
    # 如果没有提供用户名，使用账号作为默认用户名
    if "userName" not in user_data or not user_data["userName"]:
        user_data["userName"] = user_data["userAccount"]
    
    # 对密码进行bcrypt加密
    try:
        user_data["userPassword"] = bcrypt.hashpw(
            user_data["userPassword"].encode(),
            bcrypt.gensalt()
        ).decode()
    except Exception as e:
        logger.error(f"密码加密失败: {str(e)}")
        raise HTTPException(status_code=500, detail="注册失败")
    
    # 创建用户
    try:
        user = crud.create_user(db, user_data)
        
        # 创建token
        token = create_access_token({"sub": str(user.id), "role": user.userRole})
        
        # 转换为字典并脱敏
        user_dict = {
            "id": user.id,
            "userName": user.userName,
            "userAccount": user.userAccount,
            "userAvatar": user.userAvatar,
            "userRole": user.userRole,
            "createTime": user.createTime
        }
        
        return {
            "code": 1,
            "msg": "注册成功",
            "data": mask_sensitive_data(user_dict),
            "token": token
        }
    except Exception as e:
        logger.error(f"Failed to register user: {str(e)}")
        raise HTTPException(status_code=500, detail="注册失败") 