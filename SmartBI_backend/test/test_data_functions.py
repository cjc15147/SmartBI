import sys
import os
import pandas as pd
from fastapi import UploadFile
import logging
from datetime import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 创建必要的空__init__.py文件
for dir_name in ['api', 'database']:
    init_file = os.path.join(project_root, dir_name, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass

from database.models import Base
from api.data import process_existing_data, analyze_data_centers, calculate_distance
from api.ai_service import AiService

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockUploadFile:
    """模拟FastAPI的UploadFile"""
    def __init__(self, filename, file_path):
        self.filename = filename
        self.file_path = file_path
        self._file = open(file_path, 'rb')  # 直接打开文件

    @property
    def file(self):
        """返回文件对象"""
        return self._file

    def read(self):
        """读取文件内容"""
        return self._file.read()

    async def close(self):
        """关闭文件"""
        if self._file:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            self._file.close()

def test_process_existing_data(db_session):
    """测试处理存量机房数据"""
    logger.info("\n=== 测试处理存量机房数据 ===")
    
    # 构建文件路径
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "存量机房.xlsx")
    logger.info(f"尝试读取文件: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
    
    try:
        # 先清空数据库
        from database.models import DataCenter
        db_session.query(DataCenter).delete()
        db_session.commit()
        
        # 处理数据
        upload_file = MockUploadFile("存量机房.xlsx", file_path)
        result = process_existing_data(upload_file, db_session)
        
        logger.info("存量机房数据处理结果:")
        logger.info(f"总记录数: {result['total_records']}")
        logger.info(f"成功导入数: {result['success_count']}")
        logger.info(f"失败记录数: {result['failed_count']}")
        if result['failed_records']:
            logger.info("失败记录详情:")
            for record in result['failed_records']:
                logger.info(f"行号: {record['row_index']}, 错误: {record['error']}")
        
        # 验证数据是否成功存入数据库
        count = db_session.query(DataCenter).count()
        logger.info(f"数据库中的记录数: {count}")
        if count == 0:
            logger.error("数据未能成功存入数据库！")
        else:
            logger.info("数据已成功存入数据库")
            
    except Exception as e:
        logger.error(f"处理存量机房数据失败: {str(e)}")
        db_session.rollback()
        raise  # 重新抛出异常，以便调试
    finally:
        if upload_file:
            upload_file._file.close()

def test_analyze_data_centers(db_session):
    """测试分析机房数据"""
    logger.info("\n=== 测试分析机房数据 ===")
    
    # 读取新增机房数据
    file_path = os.path.join(os.path.dirname(__file__), "新增机房.xlsx")
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
    
    try:
        # 读取新增机房数据
        new_data = pd.read_excel(file_path)
        
        # 设置分析半径（公里）
        radius_km = 10
        
        # 执行分析
        result = analyze_data_centers(db_session, new_data, radius_km)
        
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
            
    except Exception as e:
        logger.error(f"分析机房数据失败: {str(e)}")

def main():
    """主测试函数"""
    # 初始化数据库
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.db")
    engine = create_engine(f"sqlite:///{db_path}", echo=True)  # 启用echo以查看SQL语句
    Base.metadata.create_all(engine)
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    try:
        # 测试处理存量机房数据
        test_process_existing_data(db_session)
        db_session.commit()  # 提交更改
        
        # 测试分析机房数据
        test_analyze_data_centers(db_session)
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        db_session.rollback()
    finally:
        # 确保关闭数据库会话
        db_session.close()
        engine.dispose()
        
        # 等待一小段时间确保连接完全关闭
        time.sleep(1)
        
        # 删除测试数据库
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception as e:
            logger.warning(f"无法删除测试数据库文件: {str(e)}")
            logger.warning("请手动删除 test.db 文件")

if __name__ == "__main__":
    main() 