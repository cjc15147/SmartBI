"""
数据处理API测试模块

本模块用于测试数据处理API的功能，包括：
1. 新增机房数据分析
2. 稽核结果生成
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
import asyncio

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from database.connection import DatabaseConnection
from api.data import analyze_data_centers, generate_audit_summary
from api.ai_service import AiService

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_data_analysis():
    """测试数据分析功能"""
    try:
        # 获取数据库会话
        db_session = DatabaseConnection.get_session()
        
        try:
            # 1. 读取新增机房数据
            logger.info("\n=== 读取新增机房数据 ===")
            new_file_path = os.path.join(project_root, "test", "新增机房.xlsx")
            if not os.path.exists(new_file_path):
                logger.error(f"新增机房文件不存在: {new_file_path}")
                return
                
            # 读取新增机房数据
            new_data = pd.read_excel(new_file_path)
            logger.info(f"成功读取新增机房数据，共 {len(new_data)} 条记录")
            
            # 2. 分析新增机房数据
            logger.info("\n=== 分析新增机房数据 ===")
            # 设置分析半径（公里）
            radius_km = 10
            
            # 执行分析
            result = await analyze_data_centers(db_session, new_data, radius_km)
            
            # 输出分析结果
            logger.info(f"\n分析结果 (分析半径: {radius_km}公里):")
            
            # 输出地图数据概况
            logger.info("\n地图数据概况:")
            logger.info(f"中心点坐标: {result['map_data']['center']}")
            logger.info(f"存量机房数量: {len(result['map_data']['existing_markers'])}")
            logger.info(f"新增机房数量: {len(result['map_data']['new_markers'])}")
            
            # 输出稽核结果
            logger.info("\n稽核结果:")
            for i, audit in enumerate(result['audit_results'], 1):
                logger.info(f"\n新增机房 {i}:")
                logger.info(f"位置: ({audit['新机房经度']}, {audit['新机房纬度']})")
                logger.info(f"合同年租金: {audit['新机房合同年租金']}")
                logger.info(f"周围存量机房平均年租金: {audit['周围存量机房平均合同年租金']:.2f}")
                logger.info(f"周围存量机房租金范围: {audit['周围存量机房最小合同年租金']:.2f} - {audit['周围存量机房最大合同年租金']:.2f}")
                logger.info(f"最近存量机房: {audit['最近存量机房名称']} (合同编码: {audit['最近存量机房合同编码']})")
                logger.info(f"最近存量机房年租金: {audit['最近存量机房合同年租金']:.2f}")
                logger.info(f"与周边平均租金比较: {audit['新机房租金与周边平均租金对比结果']}")
                logger.info(f"与最近机房租金比较: {audit['新机房租金与最近存量机房租金对比结果']}")
            
            # 3. 生成稽核总结
            logger.info("\n=== 生成稽核总结 ===")
            ai_service = AiService()
            summary = await generate_audit_summary(result['audit_results'], ai_service)
            
            print("\n" + "="*50)
            print("稽核总结：")
            print("="*50)
            print(summary['summary'])
            print("="*50)
            
        finally:
            # 关闭数据库会话
            db_session.close()
                
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_data_analysis()) 