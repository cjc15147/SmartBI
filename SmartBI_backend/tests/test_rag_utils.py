"""
RAG工具类测试模块

本模块用于测试RAG工具类的功能，包括：
1. 文档导入和分块
2. 向量数据库操作
3. 知识检索
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

def test_rag_service():
    """测试RAG服务"""
    try:
        # 设置参数
        file_path = os.path.join(project_root, "test", "人员分工名单.txt")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"Error: Document file {file_path} not found")
            return

        # 初始化RAG服务
        rag_service = RAGService()
        logger.info("RAG服务初始化成功")

        # 测试文档导入
        logger.info("\n=== 测试文档导入 ===")
        chunks = rag_service.import_document(file_path)
        logger.info(f"成功导入文档，分块数量: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            logger.info(f"\n块 {i+1}:")
            logger.info(chunk.page_content)
            logger.info(f"元数据: {chunk.metadata}")

        # 测试查询功能
        logger.info("\n=== 测试查询功能 ===")
        test_questions = [
            "我在算法研发与优化方面有问题，我要找谁？",
            "谁负责数据分析和可视化？",
            "系统架构设计由谁负责？"
        ]

        print("\n" + "="*50)
        print("查询结果：")
        print("="*50)
        
        for question in test_questions:
            print(f"\n问题：{question}")
            answer = rag_service.query(question)
            print(f"回答：{answer}")
            print("-"*50)

        # 测试保存向量数据库
        logger.info("\n=== 测试保存向量数据库 ===")
        rag_service.save_vector_store()
        logger.info("向量数据库保存成功")

        # 测试加载向量数据库
        logger.info("\n=== 测试加载向量数据库 ===")
        rag_service.load_vector_store()
        logger.info("向量数据库加载成功")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    test_rag_service() 