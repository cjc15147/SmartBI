from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from database.connection import get_db
from api import analysis as analysis_api
from router.data import NewDataCenter

router = APIRouter(prefix="/api/analysis", tags=["租金分析"])

class GeoAnalysisResult(BaseModel):
    compliant_count: int = Field(..., description="合规机房数量")
    rent_stats: dict = Field(..., description="租金统计数据")
    heatmap_data: List[List[float]] = Field(..., description="热力图数据矩阵")

class ModelResult(BaseModel):
    estimated_price: float = Field(..., description="评估租金")
    factors: Dict[str, float] = Field(..., description="影响因子")
    confidence: float = Field(..., description="置信度")

class TrendPoint(BaseModel):
    date: str
    value: float

@router.post("/geo")
async def geo_fence_analysis(
    center: tuple[float, float] = Query(..., description="中心点坐标"),
    radius: int = Query(1000, ge=500, le=5000, description="分析半径(米)"),
    db: Session = Depends(get_db)
) -> GeoAnalysisResult:
    """
    动态生成合规地理围栏
    返回包含以下结构的数据：
    - 合规机房数量
    - 租金中位数/最大值/最小值
    - 热力图数据矩阵
    """
    result = await analysis_api.analyze_geo_fence(db, center, radius)
    return GeoAnalysisResult(**result)

@router.post("/model")
async def model_evaluation(
    data: NewDataCenter,
    db: Session = Depends(get_db)
) -> ModelResult:
    """
    执行多维租金评估模型
    """
    result = await analysis_api.evaluate_model(db, data.dict())
    return ModelResult(**result)

@router.get("/trend")
async def rent_trend(
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    months: int = Query(12, ge=3, le=24, description="预测月数"),
    db: Session = Depends(get_db)
) -> List[TrendPoint]:
    """
    获取区域租金预测曲线
    """
    result = await analysis_api.predict_trend(db, latitude, longitude, months)
    return [TrendPoint(**point) for point in result] 