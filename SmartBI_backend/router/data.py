from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from database.connection import get_db
from api import data as data_api
from api.ai_service import AiService
from database import models
import pandas as pd
import logging

router = APIRouter(prefix="/api/data", tags=["数据中心管理"])

# 全局 AI 服务实例
ai_service = AiService()

# 存储上传的新增机房数据
uploaded_new_data = []

logger = logging.getLogger(__name__)

class NewDataCenter(BaseModel):
    location: str = Field(..., description="机房地址")
    rent_price: float = Field(..., gt=0, description="报价金额(元/㎡·天)")
    area: float = Field(..., gt=0, description="机房面积(㎡)")
    coordinates: tuple[float, float] = Field(..., example=[39.9042, 116.4074])

class DataCenterResponse(BaseModel):
    id: int
    location: str
    rent_price: float
    area: float
    latitude: float
    longitude: float
    create_time: str

@router.post("/upload/existing")
async def upload_existing_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传存量机房数据"""
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="只支持 Excel 或 CSV 文件")
    return await data_api.process_existing_data(file, db)

@router.post("/upload/new")
async def upload_new_data(
    file: UploadFile = File(...),
):
    """上传新增机房数据"""
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(status_code=400, detail="只支持 Excel 或 CSV 文件")
    
    try:
        # 处理文件数据
        result = await data_api.process_new_data(file)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "数据处理失败"))
        
        # 存储处理后的数据
        global uploaded_new_data
        uploaded_new_data = result.get("data", [])
        
        # 直接返回处理后的数据
        return {
            "success": True,
            "message": "数据上传成功",
            "data": uploaded_new_data,
            "total": len(uploaded_new_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_data(
    file: UploadFile = File(...),
    radius_km: float = Form(...),
    db: Session = Depends(get_db)
):
    """分析新增机房与存量机房的关系"""
    try:
        # 处理新增机房数据
        result = await data_api.process_new_data(file)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "数据处理失败"))
            
        # 将字典列表转换为 DataFrame
        new_data = pd.DataFrame(result.get("data", []))
        
        if new_data.empty:
            raise HTTPException(status_code=400, detail="没有有效的机房数据")
        
        # 分析数据
        return await data_api.analyze_data_centers(db, new_data, radius_km)
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit/summary")
async def generate_summary(
    audit_results: List[Dict[str, Any]]
):
    """生成稽核结果总结"""
    return await data_api.generate_audit_summary(audit_results, ai_service)

@router.get("/centers")
async def get_data_centers(
    page: int = Query(1, gt=0),
    size: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    """分页获取存量机房数据"""
    try:
        # 计算总数
        total = db.query(models.DataCenter).count()
        
        # 获取分页数据
        data = db.query(models.DataCenter)\
            .order_by(models.DataCenter.id.desc())\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
            
        # 转换为字典列表，确保所有数值都是Python原生类型
        result = []
        for item in data:
            result.append({
                "id": int(item.id),
                "report_name": str(item.report_name),
                "contract_code": str(item.contract_code),
                "contract_name": str(item.contract_name),
                "contract_start": item.contract_start.strftime("%Y-%m-%d"),
                "contract_end": item.contract_end.strftime("%Y-%m-%d"),
                "annual_rent": float(item.annual_rent),
                "total_rent": float(item.total_rent),
                "area": float(item.area),
                "longitude": float(item.longitude),
                "latitude": float(item.latitude)
            })
            
        return {
            "success": True,
            "data": result,
            "total": int(total)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new")
async def get_new_data(
    page: int = Query(1, gt=0),
    size: int = Query(10, gt=0),
):
    """分页获取新增机房数据"""
    try:
        global uploaded_new_data
        
        if not uploaded_new_data:
            return {
                "success": True,
                "data": [],
                "total": 0
            }
        
        # 计算总数
        total = len(uploaded_new_data)
        
        # 计算分页
        start_idx = (page - 1) * size
        end_idx = min(start_idx + size, total)
        
        # 获取分页数据
        page_data = uploaded_new_data[start_idx:end_idx]
        
        return {
            "success": True,
            "data": page_data,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upload/existing")
async def get_existing_data(
    page: int = Query(1, gt=0),
    size: int = Query(3, gt=0),
    db: Session = Depends(get_db)
):
    """获取存量机房数据列表"""
    try:
        # 计算总数
        total = db.query(models.DataCenter).count()
        
        # 获取分页数据
        data = db.query(models.DataCenter)\
            .order_by(models.DataCenter.id.desc())\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
            
        return {
            "success": True,
            "data": [{
                "id": item.id,
                "report_name": item.report_name,
                "contract_code": item.contract_code,
                "contract_name": item.contract_name,
                "contract_start": item.contract_start.strftime("%Y-%m-%d"),
                "contract_end": item.contract_end.strftime("%Y-%m-%d"),
                "annual_rent": item.annual_rent,
                "total_rent": item.total_rent,
                "area": item.area,
                "longitude": item.longitude,
                "latitude": item.latitude
            } for item in data],
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/new")
# async def create_new(
#     data: NewDataCenter,
#     db: Session = Depends(get_db)
# ):
#     """
#     提交待评估的新增机房信息
#     """
#     result = await data_api.create_data_center(db, data.dict())
#     return {"code": 1, "msg": result["message"], "data": result["data"]} 