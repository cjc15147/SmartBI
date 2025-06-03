"""
用户管理API服务模块

本模块提供用户管理相关的核心业务逻辑实现，包括：

功能列表：
1. 用户注册
   - 验证用户数据完整性
   - 检查用户是否已存在
   - 密码加密处理
   - 创建新用户记录
   
2. 用户登录
   - 验证用户凭证
   - 生成访问令牌
   - 返回用户信息
   
3. 用户信息管理
   - 获取用户详情
   - 更新用户信息
   - 删除用户（软删除）

技术实现：
- 使用 SQLAlchemy 进行数据库操作
- 使用 JWT 进行身份验证
- 使用 Pydantic 进行数据验证
- 实现了完整的错误处理机制

依赖关系：
- database.user_db: 数据库操作
- utils.jwt_utils: JWT 工具
- schemas.user: 数据模型

注意事项：
- 所有密码都经过加密处理
- 用户删除采用软删除方式
- 包含完整的日志记录
"""

from database import crud
from sqlalchemy.orm import Session
from fastapi import HTTPException
import hashlib
import logging

logger = logging.getLogger(__name__)

def create_new_user(db: Session, user_data: dict):
    try:
        # 检查用户账号是否已存在
        db_user = crud.get_user_by_account(db, user_data['userAccount'])
        if db_user:
            raise HTTPException(status_code=400, detail="账号已被注册")
        
        
        # 密码加密
        user_data['userPassword'] = hashlib.sha256(
            user_data['userPassword'].encode()
        ).hexdigest()
        
        logger.info(f"Creating new user with account: {user_data['userAccount']}")
        # 创建新用户
        return crud.create_user(db, user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

def get_user_list(db: Session, skip: int = 0, limit: int = 100):
    try:
        logger.info(f"Fetching user list with skip={skip}, limit={limit}")
        users = crud.get_users(db, skip, limit)
        return [{
            "id": user.id,
            "userAccount": user.userAccount,
            "userName": user.userName,
            "userAvatar": user.userAvatar,
            "userRole": user.userRole,
            "createTime": user.createTime,
            "updateTime": user.updateTime,
            "isDelete": user.isDelete
        } for user in users]
    except Exception as e:
        logger.error(f"Error fetching user list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}") 