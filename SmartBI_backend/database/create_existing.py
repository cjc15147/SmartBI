from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
from typing import Dict, Any, List
import logging
from .models import DataCenter
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def create_batch_existing_data(db: Session, df: pd.DataFrame) -> Dict[str, Any]:
    """
    批量创建存量机房数据
    
    Args:
        db: 数据库会话
        df: 包含机房数据的DataFrame
    
    Returns:
        Dict: 包含操作结果的字典
    """
    try:
        # 验证必要的列是否存在
        required_columns = ['机房面积', '经度', '纬度', '合同年租金']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必要的列: {', '.join(missing_columns)}")
        
        # 清理数据：只清理必要列的空值
        df = df.dropna(subset=required_columns)
        
        # 记录成功和失败的数量
        success_count = 0
        failed_records = []
        
        # 开始批量插入
        for index, row in df.iterrows():
            try:
                # 将所有列数据转换为字典
                extra_data = row.to_dict()
                # 移除已经作为单独字段的列
                for col in required_columns:
                    extra_data.pop(col, None)
                
                # 创建数据中心记录
                data_center = DataCenter(
                    area=float(row['机房面积']),
                    longitude=float(row['经度']),
                    latitude=float(row['纬度']),
                    annual_rent=float(row['合同年租金']),
                    is_new=False,
                    extra_data=extra_data
                )
                db.add(data_center)
                success_count += 1
                
            except Exception as e:
                # 记录失败的行
                failed_records.append({
                    'row_index': index + 2,  # Excel行号从2开始
                    'error': str(e)
                })
                logger.error(f"第 {index + 2} 行数据插入失败: {str(e)}")
                continue
        
        # 提交事务
        if success_count > 0:
            db.commit()
        
        # 返回处理结果
        return {
            "success": True,
            "message": "存量机房数据导入完成",
            "total_records": len(df),
            "success_count": success_count,
            "failed_count": len(failed_records),
            "failed_records": failed_records,
            "columns": list(df.columns)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"批量创建存量机房数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建存量机房数据失败: {str(e)}")

def get_existing_data_by_coordinates(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float
) -> List[DataCenter]:
    """
    根据坐标和半径获取范围内的存量机房数据
    
    Args:
        db: 数据库会话
        latitude: 纬度
        longitude: 经度
        radius_km: 半径（公里）
    
    Returns:
        List[DataCenter]: 范围内的机房列表
    """
    try:
        # 使用 Haversine 公式计算距离的 SQL
        sql = text("""
            SELECT *, 
            (
                6371 * acos(
                    cos(radians(:lat)) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians(:lon)) +
                    sin(radians(:lat)) * sin(radians(latitude))
                )
            ) AS distance
            FROM data_centers
            WHERE is_new = false
            HAVING distance <= :radius
            ORDER BY distance;
        """)
        
        # 执行查询
        result = db.execute(
            sql,
            {
                "lat": latitude,
                "lon": longitude,
                "radius": radius_km
            }
        )
        
        # 转换结果
        return [dict(row) for row in result]
        
    except Exception as e:
        logger.error(f"获取范围内的存量机房数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取范围内的存量机房数据失败: {str(e)}")

def get_all_existing_data(db: Session) -> List[DataCenter]:
    """
    获取所有存量机房数据
    
    Args:
        db: 数据库会话
    
    Returns:
        List[DataCenter]: 所有存量机房列表
    """
    try:
        return db.query(DataCenter).filter_by(is_new=False).all()
    except Exception as e:
        logger.error(f"获取所有存量机房数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取所有存量机房数据失败: {str(e)}")

def delete_existing_data(db: Session, data_center_id: int) -> Dict[str, Any]:
    """
    删除指定的存量机房数据
    
    Args:
        db: 数据库会话
        data_center_id: 机房ID
    
    Returns:
        Dict: 操作结果
    """
    try:
        data_center = db.query(DataCenter).filter_by(
            id=data_center_id,
            is_new=False
        ).first()
        
        if not data_center:
            raise HTTPException(status_code=404, detail="未找到指定的存量机房数据")
        
        db.delete(data_center)
        db.commit()
        
        return {
            "success": True,
            "message": "存量机房数据删除成功",
            "data_center_id": data_center_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除存量机房数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除存量机房数据失败: {str(e)}")

def update_existing_data(
    db: Session,
    data_center_id: int,
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    更新指定的存量机房数据
    
    Args:
        db: 数据库会话
        data_center_id: 机房ID
        update_data: 更新的数据
    
    Returns:
        Dict: 更新后的数据
    """
    try:
        data_center = db.query(DataCenter).filter_by(
            id=data_center_id,
            is_new=False
        ).first()
        
        if not data_center:
            raise HTTPException(status_code=404, detail="未找到指定的存量机房数据")
        
        # 更新基本字段
        if 'area' in update_data:
            data_center.area = float(update_data['area'])
        if 'longitude' in update_data:
            data_center.longitude = float(update_data['longitude'])
        if 'latitude' in update_data:
            data_center.latitude = float(update_data['latitude'])
        if 'annual_rent' in update_data:
            data_center.annual_rent = float(update_data['annual_rent'])
        
        # 更新额外数据
        if 'extra_data' in update_data:
            if data_center.extra_data is None:
                data_center.extra_data = {}
            data_center.extra_data.update(update_data['extra_data'])
        
        db.commit()
        db.refresh(data_center)
        
        return {
            "success": True,
            "message": "存量机房数据更新成功",
            "data": {
                "id": data_center.id,
                "area": data_center.area,
                "longitude": data_center.longitude,
                "latitude": data_center.latitude,
                "annual_rent": data_center.annual_rent,
                "extra_data": data_center.extra_data,
                "create_time": data_center.create_time,
                "update_time": data_center.update_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新存量机房数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新存量机房数据失败: {str(e)}") 