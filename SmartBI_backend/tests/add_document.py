"""
添加文档到向量数据库的测试脚本

本脚本用于测试将新文件添加到向量数据库的功能。
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from utils.rag_utils import RAGService

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_document_to_vector_db():
    """添加文档到向量数据库"""
    try:
        # 初始化RAG服务
        rag_service = RAGService()
        logger.info("RAG服务初始化成功")

        # 设置要添加的文件路径
        file_path = os.path.join(project_root, "test", "人员分工名单.txt")  # 替换为您的文件路径

        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"Error: Document file {file_path} not found")
            return

        # 导入文档
        logger.info(f"\n=== 开始导入文档: {file_path} ===")
        chunks = rag_service.import_document(file_path)
        
        # 打印导入结果
        logger.info(f"成功导入文档，分块数量: {len(chunks)}")
        logger.info("\n文档内容：")
        for i, chunk in enumerate(chunks):
            logger.info(f"\n块 {i+1}:")
            logger.info(chunk.page_content)
            logger.info(f"元数据: {chunk.metadata}")

        # 保存向量数据库
        rag_service.save_vector_store()
        logger.info("\n向量数据库保存成功")

    except Exception as e:
        logger.error(f"添加文档过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    add_document_to_vector_db() 