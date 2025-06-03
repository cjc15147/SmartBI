from fastapi import APIRouter, Depends, File, Form, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Optional
from database.connection import get_db
from router.auth import get_current_user, User
from api import ai_manage
import logging

router = APIRouter(prefix="/api/ai", tags=["AI智能分析"])

logger = logging.getLogger(__name__)

# 2.1 同步生成图表
@router.post("/gen")
async def gen_chart_by_ai(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    goal: str = Form(...),
    chart_type: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """同步方式调用AI生成图表"""
    try:
        # 获取用户ID
        user_id = current_user.get("id")
        
        # 调用AI生成图表
        result = ai_manage.gen_chart_sync(
            db=db,
            file=file,
            user_id=user_id,
            goal=goal,
            name=name,
            chart_type=chart_type
        )
        
        return {"code": 1, "data": result}
    except Exception as e:
        logger.error(f"同步生成图表失败: {str(e)}")
        return {"code": 0, "message": str(e)}

# 2.2 异步生成图表
@router.post("/gen/async")
async def gen_chart_by_ai_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    goal: str = Form(...),
    chart_type: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """异步方式调用AI生成图表(后台任务)"""
    try:
        # 获取用户ID
        user_id = current_user.get("id")
        
        # 异步生成图表
        result = ai_manage.gen_chart_async(
            db=db,
            background_tasks=background_tasks,
            file=file,
            user_id=user_id,
            goal=goal,
            name=name,
            chart_type=chart_type
        )
        
        return {"code": 1, "data": result}
    except Exception as e:
        logger.error(f"创建异步图表任务失败: {str(e)}")
        return {"code": 0, "message": str(e)}

# 2.3 消息队列异步生成图表
@router.post("/gen/async/mq")
async def gen_chart_by_ai_async_mq(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    goal: str = Form(...),
    chart_type: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过消息队列异步生成图表"""
    try:
        # 获取用户ID
        user_id = current_user.get("id")
        
        # 通过消息队列异步生成图表
        result = ai_manage.gen_chart_async_mq(
            db=db,
            file=file,
            user_id=user_id,
            goal=goal,
            name=name,
            chart_type=chart_type
        )
        
        return {"code": 1, "data": result}
    except Exception as e:
        logger.error(f"创建异步图表任务失败: {str(e)}")
        return {"code": 0, "message": str(e)} 