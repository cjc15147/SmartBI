from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from database.connection import get_db
from api import chart as chart_api
import logging
from datetime import datetime
from router.auth import get_current_user, User

router = APIRouter(prefix="/api/chart", tags=["图表管理"])

logger = logging.getLogger(__name__)

# 请求模型
class ChartCreate(BaseModel):
    name: str = Field(..., description="图表名称")
    goal: Optional[str] = Field(None, description="分析目标")
    chartData: Optional[str] = Field(None, description="图表数据")
    chartType: str = Field(..., description="图表类型")

class ChartUpdate(BaseModel):
    id: int = Field(..., description="图表ID")
    name: Optional[str] = Field(None, description="图表名称")
    goal: Optional[str] = Field(None, description="分析目标")
    chartData: Optional[str] = Field(None, description="图表数据")
    chartType: Optional[str] = Field(None, description="图表类型")
    genChart: Optional[str] = Field(None, description="生成的图表数据")
    genResult: Optional[str] = Field(None, description="生成的分析结论")
    status: Optional[int] = Field(None, description="图表状态")

class DeleteRequest(BaseModel):
    id: int = Field(..., description="图表ID")

class ChartQuery(BaseModel):
    current: int = Field(1, ge=1, description="当前页码")
    size: int = Field(10, ge=1, le=100, description="每页数量")
    name: Optional[str] = Field(None, description="图表名称")
    status: Optional[int] = Field(None, description="图表状态")

# 响应模型
class ChartDetail(BaseModel):
    id: int
    name: str
    goal: Optional[str]
    chartData: Optional[str]
    chartType: str
    genChart: Optional[str]
    genResult: Optional[str]
    status: int
    userId: int
    createTime: str
    updateTime: str

class Chart(BaseModel):
    id: int
    name: str
    goal: Optional[str]
    chartType: str
    status: int
    userId: int
    createTime: str
    updateTime: str

class PageResult(BaseModel):
    records: List[Any]
    total: int
    size: int
    current: int

# 1.1 创建图表
@router.post("/add", response_model=Dict[str, Any])
async def add_chart(
    chart: ChartCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新图表"""
    try:
        # 获取当前用户ID
        user_id = current_user.get("id")
        logger.info(f"用户 {user_id} 尝试创建图表: {chart.dict()}")
        
        # 创建图表
        chart_id = chart_api.create_chart(db, chart.dict(), user_id)
        
        return {"code": 1, "data": chart_id, "message": "创建成功"}
    except HTTPException as e:
        logger.error(f"创建图表失败(HTTP错误): {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"创建图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 1.2 删除图表
@router.post("/delete")
async def delete_chart(
    delete_request: DeleteRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """删除指定图表"""
    try:
        # 获取当前用户ID和角色
        user_id = current_user.get("id")
        is_admin = current_user.get("userRole") == "admin"
        
        # 删除图表
        result = chart_api.delete_chart(db, delete_request.id, user_id, is_admin)
        
        return {"code": 1, "message": "删除成功"}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"删除图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 1.3 更新图表
@router.post("/update")
async def update_chart(
    chart_update: ChartUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """更新图表信息(管理员权限)"""
    try:
        # 获取当前用户角色
        user_id = current_user.get("id")
        is_admin = current_user.get("userRole") == "admin"
        
        # 更新图表
        result = chart_api.update_chart(db, chart_update.dict(), user_id, is_admin)
        
        return {"code": 1, "message": "更新成功"}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"更新图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 1.4 用户编辑图表
@router.post("/edit")
async def edit_chart(
    chart_edit: ChartUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """用户编辑自己的图表"""
    try:
        # 获取当前用户ID
        user_id = current_user.get("id")
        
        # 编辑图表
        result = chart_api.edit_chart(db, chart_edit.dict(), user_id)
        
        return {"code": 1, "message": "编辑成功"}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"编辑图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 1.5 获取图表详情
@router.get("/get")
async def get_chart_by_id(
    id: int = Query(..., description="图表ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取图表详情"""
    try:
        # 获取图表详情
        chart = chart_api.get_chart_by_id(db, id)
        
        return {"code": 1, "data": chart}
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"获取图表详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 1.6 分页获取图表列表
@router.post("/list/page")
async def list_chart_by_page(
    query: ChartQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分页获取图表列表"""
    try:
        # 执行分页查询
        result = chart_api.list_chart_by_page(
            db, 
            query.current, 
            query.size, 
            query.name, 
            query.status
        )
        
        return {"code": 1, "data": result}
    except Exception as e:
        logger.error(f"分页获取图表列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 1.7 分页获取当前用户的图表
@router.post("/my/list/page")
async def list_my_chart_by_page(
    query: ChartQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分页获取当前用户的图表"""
    try:
        # 获取当前用户ID
        user_id = current_user.get("id")
        
        # 执行分页查询
        result = chart_api.list_chart_by_page(
            db, 
            query.current, 
            query.size, 
            query.name, 
            query.status, 
            user_id
        )
        
        return {"code": 1, "data": result}
    except Exception as e:
        logger.error(f"分页获取用户图表列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 