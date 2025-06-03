"""
数据处理API服务模块

本模块提供数据处理和分析相关的核心业务逻辑实现，包括：

功能列表：
1. 数据导入导出
   - 支持多种数据格式（CSV、Excel等）
   - 数据验证和清洗
   - 批量导入导出
   
2. 数据处理
   - 数据转换和规范化
   - 数据过滤和筛选
   - 数据聚合和计算
   
3. 数据分析
   - 基础统计分析
   - 趋势分析
   - 关联分析
   
4. 数据存储
   - 数据持久化
   - 缓存管理
   - 版本控制

技术实现：
- 使用 Pandas 进行数据处理
- 使用 NumPy 进行数值计算
- 实现了数据处理管道
- 支持异步处理大数据集
- 集成RAG功能，支持政策检索

依赖关系：
- pandas: 数据处理库
- numpy: 数值计算库
- database: 数据库操作
- utils.data_utils: 数据处理工具
- utils.rag_utils: RAG工具集

性能优化：
- 实现了数据缓存机制
- 支持分批处理大数据
- 优化了内存使用
- 实现了并行处理

错误处理：
- 完整的异常处理机制
- 详细的错误日志
- 用户友好的错误提示
"""

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from database import models
import logging
from haversine import haversine
import folium
import plotly.express as px
import json
from io import StringIO, BytesIO
from .ai_service import AiService
from openai import OpenAI
from utils.rag_utils import RAGService

logger = logging.getLogger(__name__)

# 初始化RAG服务
rag_service = RAGService()

async def process_existing_data(file: UploadFile, db: Session) -> Dict[str, Any]:
    """
    处理上传的机房数据文件并存入数据库
    每次上传新文件时会清空原有数据并插入新数据
    """
    try:
        # 读取文件内容到内存
        contents = await file.read()
        
        # 读取文件内容
        if file.filename.endswith('.csv'):
            # 使用StringIO处理CSV文件
            df = pd.read_csv(StringIO(contents.decode('utf-8')))
        else:
            # 使用BytesIO处理Excel文件
            df = pd.read_excel(BytesIO(contents))
        
        # 验证必要的列是否存在
        required_columns = [
            '报账点名称', '合同编码', '合同名称', '合同期始', '合同期终',
            '合同年租金', '合同总金额', '机房面积', '经度', '纬度'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"文件缺少必要的列: {', '.join(missing_columns)}")
        
        # 清理数据：清理必要列的空值
        df = df.dropna(subset=required_columns)
        
        try:
            # 清空原有数据
            db.query(models.DataCenter).delete()
            
            # 转换数据并批量插入
            success_count = 0
            failed_records = []
            
            for index, row in df.iterrows():
                try:
                    # 转换日期格式
                    contract_start = pd.to_datetime(row['合同期始'])
                    contract_end = pd.to_datetime(row['合同期终'])
                    
                    # 确保数值类型正确
                    data_center = models.DataCenter(
                        report_name=str(row['报账点名称']),
                        contract_code=str(row['合同编码']),
                        contract_name=str(row['合同名称']),
                        contract_start=contract_start,
                        contract_end=contract_end,
                        annual_rent=float(row['合同年租金'].item() if isinstance(row['合同年租金'], (np.integer, np.floating)) else row['合同年租金']),
                        total_rent=float(row['合同总金额'].item() if isinstance(row['合同总金额'], (np.integer, np.floating)) else row['合同总金额']),
                        area=float(row['机房面积'].item() if isinstance(row['机房面积'], (np.integer, np.floating)) else row['机房面积']),
                        longitude=float(row['经度'].item() if isinstance(row['经度'], (np.integer, np.floating)) else row['经度']),
                        latitude=float(row['纬度'].item() if isinstance(row['纬度'], (np.integer, np.floating)) else row['纬度'])
                    )
                    db.add(data_center)
                    success_count += 1
                    
                except Exception as e:
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
                "message": "机房数据更新成功",
                "total_records": len(df),
                "success_count": success_count,
                "failed_count": len(failed_records),
                "failed_records": failed_records
            }
            
        except Exception as e:
            db.rollback()
            raise Exception(f"数据库操作失败: {str(e)}")
        
    except Exception as e:
        logger.error(f"文件处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"文件处理失败: {str(e)}")

async def process_new_data(file: UploadFile) -> Dict[str, Any]:
    """
    处理上传的新增机房数据文件
    """
    try:
        # 读取文件内容到内存
        contents = await file.read()
        
        # 读取文件内容
        if file.filename.endswith('.csv'):
            # 使用StringIO处理CSV文件
            df = pd.read_csv(StringIO(contents.decode('utf-8')))
        else:
            # 使用BytesIO处理Excel文件
            df = pd.read_excel(BytesIO(contents))
        
        # 验证必要的列是否存在
        required_columns = ['机房面积', '经度', '纬度', '合同年租金']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"文件缺少必要的列: {', '.join(missing_columns)}")
        
        # 清理数据：只移除空值
        df = df.dropna(subset=required_columns)
        
        if len(df) == 0:
            raise ValueError("没有有效的机房数据")
        
        # 转换为字典列表，保持中文列名
        result_data = []
        for _, row in df.iterrows():
            try:
                data = {
                    "area": float(row['机房面积']),
                    "longitude": float(row['经度']),
                    "latitude": float(row['纬度']),
                    "annual_rent": float(row['合同年租金'])
                }
                result_data.append(data)
            except Exception as e:
                logger.error(f"处理行数据失败: {str(e)}")
                continue
        
        if not result_data:
            raise ValueError("没有有效的机房数据")
        
        return {
            "success": True,
            "message": "数据处理成功",
            "data": result_data,
            "total": len(result_data)
        }
        
    except Exception as e:
        logger.error(f"文件处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"文件处理失败: {str(e)}")

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点间距离（公里）"""
    return haversine((lat1, lon1), (lat2, lon2))

async def analyze_data_centers(db: Session, new_data: pd.DataFrame, radius_km: float) -> Dict[str, Any]:
    """
    分析新增机房与存量机房的关系
    如果数据库中没有存量机房数据，则返回错误提示
    """
    try:
        # 获取所有机房数据
        existing_centers = db.query(models.DataCenter).all()
        if not existing_centers:
            raise HTTPException(
                status_code=400, 
                detail="数据库中没有存量机房数据，请先上传存量机房数据"
            )
            
        existing_data = pd.DataFrame([{
            'area': dc.area,
            'longitude': dc.longitude,
            'latitude': dc.latitude,
            'annual_rent': dc.annual_rent,
            'report_name': dc.report_name,
            'contract_code': dc.contract_code
        } for dc in existing_centers])
        
        # 生成地图数据
        map_data = await generate_map_data(existing_data, new_data, radius_km)
        
        # 生成散点图数据
        scatter_data = await generate_scatter_data(existing_data, new_data, radius_km)
        
        # 生成稽核结果
        audit_results = []
        for _, new_dc in new_data.iterrows():
            nearby_centers = []
            for _, exist_dc in existing_data.iterrows():
                distance = calculate_distance(
                    new_dc['latitude'], new_dc['longitude'],
                    exist_dc['latitude'], exist_dc['longitude']
                )
                if distance <= radius_km:
                    nearby_centers.append({
                        **exist_dc.to_dict(),
                        'distance': distance
                    })
            
            if nearby_centers:
                nearby_df = pd.DataFrame(nearby_centers)
                result = {
                    'new_longitude': new_dc['longitude'],
                    'new_latitude': new_dc['latitude'],
                    'new_annual_rent': new_dc['annual_rent'],
                    'nearby_avg_rent': nearby_df['annual_rent'].mean(),
                    'nearby_min_rent': nearby_df['annual_rent'].min(),
                    'nearby_max_rent': nearby_df['annual_rent'].max(),
                    'nearest_rent': nearby_df.loc[nearby_df['distance'].idxmin(), 'annual_rent'],
                    'nearest_name': nearby_df.loc[nearby_df['distance'].idxmin(), 'report_name'],
                    'nearest_contract_code': nearby_df.loc[nearby_df['distance'].idxmin(), 'contract_code'],
                    'rent_comparison_avg': '<=' if new_dc['annual_rent'] <= nearby_df['annual_rent'].mean() else '>',
                    'rent_comparison_nearest': '<=' if new_dc['annual_rent'] <= nearby_df.loc[nearby_df['distance'].idxmin(), 'annual_rent'] else '>'
                }
                audit_results.append(result)
            else:
                # 如果在指定半径内没有找到存量机房，也记录这个结果
                result = {
                    'new_longitude': new_dc['longitude'],
                    'new_latitude': new_dc['latitude'],
                    'new_annual_rent': new_dc['annual_rent'],
                    'analysis_result': f'在{radius_km}公里范围内未找到存量机房'
                }
                audit_results.append(result)
        
        return {
            "map_data": map_data,
            "scatter_data": scatter_data,
            "audit_results": audit_results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"数据分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据分析失败: {str(e)}")

async def generate_map_data(existing_data: pd.DataFrame, new_data: pd.DataFrame, radius_km: float) -> Dict[str, Any]:
    """生成地图展示数据，只包含新增机房周围指定半径内的存量机房"""
    map_center = [34.341575, 108.93977]  # 西安市中心坐标
    
    # 构建地图数据
    existing_markers = []
    
    # 遍历每个新增机房
    for _, new_dc in new_data.iterrows():
        # 遍历存量机房，检查是否在半径范围内
        for _, exist_dc in existing_data.iterrows():
            distance = calculate_distance(
                new_dc['latitude'], new_dc['longitude'],
                exist_dc['latitude'], exist_dc['longitude']
            )
            # 如果在半径范围内且尚未添加到标记列表中
            if distance <= radius_km and not any(
                marker['latitude'] == exist_dc['latitude'] and 
                marker['longitude'] == exist_dc['longitude'] 
                for marker in existing_markers
            ):
                existing_markers.append({
                    "type": "existing",
                    "latitude": exist_dc['latitude'],
                    "longitude": exist_dc['longitude'],
                    "annual_rent": exist_dc['annual_rent'],
                    "distance": round(distance, 2)  # 添加到新增机房的距离信息
                })
    
    new_markers = []
    for _, row in new_data.iterrows():
        new_markers.append({
            "type": "new",
            "latitude": row['latitude'],
            "longitude": row['longitude'],
            "annual_rent": row['annual_rent']
        })
    
    
    return {
        "center": map_center,
        "existing_markers": existing_markers,
        "new_markers": new_markers,
        "radius_km": radius_km
    }

async def generate_scatter_data(existing_data: pd.DataFrame, new_data: pd.DataFrame, radius_km: float) -> Dict[str, Any]:
    """生成散点图数据，只包含新增机房周围指定半径内的存量机房"""
    # 存储在范围内的存量机房
    nearby_existing = set()
    
    # 遍历每个新增机房
    for _, new_dc in new_data.iterrows():
        # 遍历存量机房，检查是否在半径范围内
        for idx, exist_dc in existing_data.iterrows():
            distance = calculate_distance(
                new_dc['latitude'], new_dc['longitude'],
                exist_dc['latitude'], exist_dc['longitude']
            )
            # 如果在半径范围内，添加到集合中
            if distance <= radius_km:
                nearby_existing.add(idx)
    
    # 只保留在范围内的存量机房数据
    filtered_existing = existing_data.iloc[list(nearby_existing)]
    
    scatter_data = {
        "existing": filtered_existing[['longitude', 'latitude', 'annual_rent']].to_dict('records'),
        "new": new_data[['longitude', 'latitude', 'annual_rent']].to_dict('records')
    }
    return scatter_data

async def generate_audit_summary(audit_results: List[Dict[str, Any]], ai_service: AiService) -> Dict[str, str]:
    """
    生成稽核结果总结
    分析每个新增机房的价格是否合理
    """
    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key="sk-yourkey",
            base_url="https://api.deepseek.com/v1"
        )

        # 构造分析数据
        analysis_data = []
        for result in audit_results:
            # 跳过没有找到周边存量机房的数据
            if 'analysis_result' in result:
                analysis_data.append({
                    '位置': f"经度{result['new_longitude']},纬度{result['new_latitude']}",
                    '分析结果': result['analysis_result']
                })
                continue

            # 计算是否通过稽核
            rent_new = result['new_annual_rent']
            rent_nearest = result['nearest_rent']
            rent_avg = result['nearby_avg_rent']
            rent_min = result['nearby_min_rent']
            
            status = "通过" if (rent_new <= rent_min or rent_new <= rent_avg) else "不通过"
            
            analysis_data.append({
                '位置': f"经度{result['new_longitude']},纬度{result['new_latitude']}",
                '新机房租金': rent_new,
                '周边最低租金': rent_min,
                '周边平均租金': rent_avg,
                '最近机房租金': rent_nearest,
                '稽核结果': status
            })

        # 使用RAG检索相关政策
        policy_context = rag_service.query("机房租金定价标准")
        if policy_context == "未找到相关政策和规定":
            policy_context = "未找到相关政策规定，将按照默认规则进行评估。"

        # 构造提示语
        prompt = f"""请根据以下数据分析和评估新增机房的租金定价是否合理：

分析数据：
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

相关政策和规定：
{policy_context}

分析要求：
1. 新增机房的租金应不大于周边规定范围内租金最低的存量机房的租金
2. 如果大于最低租金，则应不大于周边平均租金
3. 请分别说明每个新增机房的具体分析情况
4. 最后给出总体评估结论
5. 评估结论必须考虑相关政策规定

请生成一段分析总结，包含具体分析和最终结论。"""

        # 调用 AI 接口
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的机房租金定价分析专家，擅长分析租金定价的合理性。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        # 获取分析结果
        analysis_result = response.choices[0].message.content

        return {
            "summary": analysis_result
        }

    except Exception as e:
        logger.error(f"生成稽核总结失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成稽核总结失败: {str(e)}")
