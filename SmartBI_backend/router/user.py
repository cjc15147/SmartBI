from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import DatabaseConnection
from api import user as user_api
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# 依赖项：获取数据库会话
def get_db():
    db = DatabaseConnection.get_session()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    userName: str = Field(..., description="用户昵称", example="张三")
    userAccount: str = Field(..., description="登录账号", example="zhangsan")
    userPassword: str = Field(..., description="登录密码", example="password123")
    userAvatar: Optional[str] = Field(None, description="头像URL")
    userRole: Optional[str] = Field("user", description="用户角色", example="user")

class UserResponse(BaseModel):
    id: int = Field(..., description="用户ID")
    userName: str = Field(..., description="用户昵称")
    userAccount: str = Field(..., description="登录账号")
    userAvatar: Optional[str] = Field(None, description="头像URL")
    userRole: str = Field(..., description="用户角色")
    isDelete: int = Field(..., description="是否删除")
    createTime: datetime = Field(..., description="创建时间")
    updateTime: datetime = Field(..., description="更新时间")

class UserListResponse(BaseModel):
    code: int = Field(0, description="响应码")
    data: List[UserResponse] = Field(..., description="用户列表数据")
    message: str = Field(..., description="响应消息")

class UserCreateResponse(BaseModel):
    code: int = Field(0, description="响应码")
    data: dict = Field(..., description="创建的用户信息")
    message: str = Field(..., description="响应消息")

@router.post("/users/", response_model=UserCreateResponse, summary="创建新用户")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    创建新用户
    
    - **userName**: 用户昵称
    - **userAccount**: 登录账号
    - **userPassword**: 登录密码
    - **userAvatar**: 头像URL（可选）
    - **userRole**: 用户角色（可选，默认为user）
    """
    user_data = user.dict()
    result = user_api.create_new_user(db, user_data)
    return {
        "code": 0,
        "data": {
            "id": result.id,
            "userName": result.userName,
            "userAccount": result.userAccount
        },
        "message": "用户创建成功"
    }

@router.get("/users/", response_model=UserListResponse, summary="获取用户列表")
async def read_users(
    skip: int = Query(0, description="跳过的记录数", ge=0),
    limit: int = Query(100, description="返回的最大记录数", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取用户列表
    
    - **skip**: 跳过前面的记录数（分页用）
    - **limit**: 返回的最大记录数（分页用）
    """
    users = user_api.get_user_list(db, skip, limit)
    return {
        "code": 0,
        "data": users,
        "message": "获取用户列表成功"
    }