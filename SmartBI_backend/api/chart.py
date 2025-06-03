"""
图表生成API服务模块

本模块提供图表生成和可视化相关的核心业务逻辑实现，包括：

功能列表：
1. 基础图表生成
   - 折线图
   - 柱状图
   - 饼图
   - 散点图
   
2. 高级图表功能
   - 多维数据可视化
   - 交互式图表
   - 实时数据更新
   - 自定义样式
   
3. 图表管理
   - 图表保存
   - 模板管理
   - 批量生成
   - 导出功能
   
4. 数据处理
   - 数据预处理
   - 数据转换
   - 数据聚合
   - 异常处理

技术实现：
- 使用 ECharts/Highcharts 等图表库
- 支持多种图表类型和样式
- 实现了图表配置模板
- 支持图表主题定制

依赖关系：
- echarts/highcharts: 图表库
- database: 数据存储
- utils.chart_utils: 图表工具
- schemas.chart: 图表模型

性能优化：
- 数据缓存机制
- 按需加载
- 图表组件复用
- 异步渲染

特色功能：
- 智能推荐图表类型
- 自动优化图表布局
- 支持图表联动
- 丰富的交互功能
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
import logging
from typing import Dict, Any, List, Optional
from database import models
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def create_chart(db: Session, chart_data: Dict[str, Any], user_id: int) -> int:
    """
    创建新图表
    返回创建的图表ID
    """
    logger.info(f"开始创建图表: user_id={user_id}, chart_data={chart_data}")
    try:
        # 获取当前最大id
        max_id = db.query(func.max(models.Chart.id)).scalar()
        new_id = 1 if max_id is None else max_id + 1
        
        # 处理gen_chart字段，确保是字符串格式
        gen_chart = chart_data.get("gen_chart")
        if isinstance(gen_chart, dict):
            gen_chart = json.dumps(gen_chart, ensure_ascii=False)
        
        # 创建图表记录
        chart = models.Chart(
            id=new_id,
            name=chart_data.get("name"),
            goal=chart_data.get("goal"),
            chart_data=chart_data.get("chart_data"),
            chart_type=chart_data.get("chart_type"),
            gen_chart=gen_chart,
            gen_result=chart_data.get("gen_result"),
            status=chart_data.get("status", "waiting"),  # 默认状态为waiting
            exec_message=chart_data.get("exec_message"),
            user_id=user_id,
            is_delete=0
        )
        logger.info(f"图表对象创建成功，准备添加到数据库")
        db.add(chart)
        db.commit()
        db.refresh(chart)
        logger.info(f"图表创建成功，ID: {chart.id}")
        return chart.id
    except Exception as e:
        db.rollback()
        logger.error(f"创建图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建图表失败: {str(e)}")

def delete_chart(db: Session, chart_id: int, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
    """
    删除图表（逻辑删除）
    """
    try:
        # 查询图表
        chart = db.query(models.Chart).filter(models.Chart.id == chart_id, models.Chart.is_delete == False).first()
        if not chart:
            raise HTTPException(status_code=404, detail="图表不存在或已删除")
        
        # 校验权限
        if chart.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="无权限删除该图表")
        
        # 逻辑删除
        chart.is_delete = True
        chart.update_time = datetime.now()
        db.commit()
        
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除图表失败: {str(e)}")

def update_chart(db: Session, chart_data: Dict[str, Any], user_id: int, is_admin: bool = True) -> Dict[str, Any]:
    """
    更新图表（管理员权限）
    """
    try:
        # 校验管理员权限
        if not is_admin:
            raise HTTPException(status_code=403, detail="无管理员权限")
        
        # 查询图表
        chart = db.query(models.Chart).filter(models.Chart.id == chart_data["id"], models.Chart.is_delete == 0).first()
        if not chart:
            raise HTTPException(status_code=404, detail="图表不存在或已删除")
        
        # 更新图表信息
        if "name" in chart_data:
            chart.name = chart_data["name"]
        if "goal" in chart_data:
            chart.goal = chart_data["goal"]
        if "chart_data" in chart_data:
            chart.chart_data = chart_data["chart_data"]
        if "chart_type" in chart_data:
            chart.chart_type = chart_data["chart_type"]
        if "gen_chart" in chart_data:
            chart.gen_chart = chart_data["gen_chart"]
        if "gen_result" in chart_data:
            chart.gen_result = chart_data["gen_result"]
        if "status" in chart_data:
            chart.status = chart_data["status"]
        if "exec_message" in chart_data:
            chart.exec_message = chart_data["exec_message"]
        
        chart.update_time = datetime.now()
        db.commit()
        
        return {"success": True, "message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新图表失败: {str(e)}")

def edit_chart(db: Session, chart_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    用户编辑自己的图表
    """
    try:
        # 查询图表
        chart = db.query(models.Chart).filter(models.Chart.id == chart_data["id"], models.Chart.is_delete == False).first()
        if not chart:
            raise HTTPException(status_code=404, detail="图表不存在或已删除")
        
        # 校验权限
        if chart.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限编辑该图表")
        
        # 更新图表信息
        if "name" in chart_data:
            chart.name = chart_data["name"]
        if "goal" in chart_data:
            chart.goal = chart_data["goal"]
        if "chartData" in chart_data:
            chart.chart_data = chart_data["chartData"]
        if "chartType" in chart_data:
            chart.chart_type = chart_data["chartType"]
        
        chart.update_time = datetime.now()
        # 如果用户修改了数据，重置状态为待生成
        chart.status = 0
        db.commit()
        
        return {"success": True, "message": "编辑成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"编辑图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"编辑图表失败: {str(e)}")

def get_chart_by_id(db: Session, chart_id: int) -> Dict[str, Any]:
    """
    获取图表详情
    """
    try:
        # 查询图表
        chart = db.query(models.Chart).filter(models.Chart.id == chart_id, models.Chart.is_delete == 0).first()
        if not chart:
            raise HTTPException(status_code=404, detail="图表不存在或已删除")
        
        # 转换为字典
        return {
            "id": chart.id,
            "name": chart.name,
            "goal": chart.goal,
            "chartData": chart.chart_data,
            "chartType": chart.chart_type,
            "genChart": chart.gen_chart,
            "genResult": chart.gen_result,
            "status": chart.status,
            "execMessage": chart.exec_message,
            "userId": chart.user_id,
            "createTime": chart.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "updateTime": chart.update_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图表详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图表详情失败: {str(e)}")

def list_chart_by_page(db: Session, page: int, size: int, name: Optional[str] = None, status: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    分页获取图表列表
    """
    try:
        # 构建查询条件
        query = db.query(models.Chart).filter(models.Chart.is_delete == 0)
        
        if name:
            query = query.filter(models.Chart.name.like(f"%{name}%"))
        if status is not None:
            query = query.filter(models.Chart.status == status)
        if user_id:
            query = query.filter(models.Chart.user_id == user_id)
        
        # 统计总数
        total = query.count()
        
        # 执行分页查询
        charts = query.order_by(models.Chart.create_time.desc())\
            .offset((page - 1) * size)\
            .limit(size)\
            .all()
        
        # 转换为字典列表
        items = []
        for chart in charts:
            items.append({
                "id": chart.id,
                "name": chart.name,
                "goal": chart.goal,
                "chartType": chart.chart_type,
                "status": chart.status,
                "execMessage": chart.exec_message,
                "userId": chart.user_id,
                "createTime": chart.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "updateTime": chart.update_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "records": items,
            "total": total,
            "size": size,
            "current": page
        }
    except Exception as e:
        logger.error(f"分页获取图表列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分页获取图表列表失败: {str(e)}") 