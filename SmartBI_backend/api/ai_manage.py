from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
import pandas as pd
import logging
from typing import Dict, Optional
from .ai_service import AiService
from . import chart as chart_api
import io

logger = logging.getLogger(__name__)

# 创建AI服务实例
ai_service = AiService()

def process_file(file: UploadFile) -> str:
    """处理上传的文件，返回CSV格式的数据"""
    try:
        # 读取文件内容
        content = file.file.read()
        
        # 根据文件类型处理数据
        if file.filename.endswith('.csv'):
            # 直接返回CSV内容
            return content.decode('utf-8')
        elif file.filename.endswith(('.xls', '.xlsx')):
            # 将Excel转换为CSV
            df = pd.read_excel(io.BytesIO(content))
            return df.to_csv(index=False)
        else:
            raise ValueError("不支持的文件类型，仅支持CSV和Excel文件")
            
    except Exception as e:
        logger.error(f"文件处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"文件处理失败: {str(e)}")
    finally:
        file.file.close()

def validate_file(file: UploadFile):
    """验证上传的文件"""
    # 检查文件大小（限制为5MB）
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过限制(5MB)")
        
    # 检查文件类型
    allowed_types = ['.csv', '.xls', '.xlsx']
    if not any(file.filename.endswith(t) for t in allowed_types):
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持CSV和Excel文件")

def gen_chart_sync(
    db: Session,
    file: UploadFile,
    user_id: int,
    goal: str,
    name: Optional[str] = None,
    chart_type: Optional[str] = None
) -> Dict:
    """同步生成图表"""
    try:
        # 1. 验证文件
        validate_file(file)
        
        # 2. 处理文件数据
        csv_data = process_file(file)
        
        # 3. 调用AI生成图表
        ai_result = ai_service.generate_chart(goal, chart_type, csv_data)
        
        # 4. 创建图表记录
        chart_data = {
            "name": name or "AI生成图表",
            "goal": goal,
            "chart_type": ai_result["chartType"],
            "chart_data": csv_data,
            "gen_chart": ai_result["chartData"],
            "gen_result": ai_result["genResult"],
            "status": "succeeded",
            "exec_message": None,
            "user_id": user_id,
            "is_delete": 0
        }
        chart_id = chart_api.create_chart(db, chart_data, user_id)
        
        # 5. 返回结果
        return {
            "genType": ai_result["chartType"],
            "genChart": ai_result["chartData"],
            "genResult": ai_result["genResult"]
        }
        
    except Exception as e:
        logger.error(f"生成图表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成图表失败: {str(e)}")

async def gen_chart_async_task(
    db: Session,
    chart_id: int,
    csv_data: str,
    goal: str,
    chart_type: Optional[str] = None
):
    """异步生成图表的后台任务"""
    try:
        # 1. 调用AI生成图表
        ai_result = ai_service.generate_chart(goal, chart_type, csv_data)
        
        # 2. 更新图表记录
        chart_data = {
            "id": chart_id,
            "chart_type": ai_result["chartType"],
            "gen_chart": ai_result["chartData"],
            "gen_result": ai_result["genResult"],
            "status": "succeeded"
        }
        chart_api.update_chart(db, chart_data, None, True)
        
    except Exception as e:
        logger.error(f"异步生成图表失败: {str(e)}")
        # 更新图表状态为失败
        chart_data = {
            "id": chart_id,
            "status": "failed",
            "exec_message": str(e)
        }
        chart_api.update_chart(db, chart_data, None, True)

def gen_chart_async(
    db: Session,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    user_id: int,
    goal: str,
    name: Optional[str] = None,
    chart_type: Optional[str] = None
) -> Dict:
    """异步生成图表"""
    try:
        # 1. 验证文件
        validate_file(file)
        
        # 2. 处理文件数据
        csv_data = process_file(file)
        
        # 3. 创建初始图表记录
        chart_data = {
            "name": name or "AI生成图表",
            "goal": goal,
            "chart_data": csv_data,
            "status": "running"
        }
        chart_id = chart_api.create_chart(db, chart_data, user_id)
        
        # 4. 添加后台任务
        background_tasks.add_task(
            gen_chart_async_task,
            db,
            chart_id,
            csv_data,
            goal,
            chart_type
        )
        
        # 5. 返回图表ID
        return {"id": chart_id}
        
    except Exception as e:
        logger.error(f"创建异步图表任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建异步图表任务失败: {str(e)}")

def gen_chart_async_mq(
    db: Session,
    file: UploadFile,
    user_id: int,
    goal: str,
    name: Optional[str] = None,
    chart_type: Optional[str] = None
) -> Dict:
    """通过消息队列异步生成图表"""
    try:
        # 1. 验证文件
        validate_file(file)
        
        # 2. 处理文件数据
        csv_data = process_file(file)
        
        # 3. 创建初始图表记录
        chart_data = {
            "name": name or "AI生成图表",
            "goal": goal,
            "chart_data": csv_data,
            "status": "waiting"
        }
        chart_id = chart_api.create_chart(db, chart_data, user_id)
        
        # 4. 发送消息到队列
        # TODO: 实现消息队列发送逻辑
        
        # 5. 返回图表ID
        return {"id": chart_id}
        
    except Exception as e:
        logger.error(f"创建异步图表任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建异步图表任务失败: {str(e)}") 