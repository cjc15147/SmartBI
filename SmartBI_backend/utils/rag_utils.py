"""
RAG工具模块

本模块提供向量数据库检索相关的功能实现，包括：

功能列表：
1. 文档导入和分块
   - 支持TXT、PDF、Word格式
   - 按行分块
   - 文本预处理
   
2. 向量数据库操作
   - 文档向量化
   - 向量存储
   - 相似度检索
   
3. 知识检索
   - 问题向量化
   - 相似度匹配
   - 上下文构建
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path
import PyPDF2
import docx
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import BaichuanTextEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.schema import Document

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, api_key: str = "sk-your-key"):
        """初始化RAG服务"""
        # 初始化嵌入模型
        self.embeddings = BaichuanTextEmbeddings(api_key=api_key)
        
        # 设置向量数据库存储路径（使用纯英文路径）
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.persist_directory = os.path.join(base_dir, "data", "chroma_db")
        
        # 确保目录存在
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            logger.info(f"向量数据库目录已创建: {self.persist_directory}")
        except Exception as e:
            logger.error(f"创建向量数据库目录失败: {str(e)}")
            raise
        
        # 初始化向量数据库
        self.vector_store = None
        self.documents = []
        
        # 尝试加载已存在的向量数据库
        try:
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                logger.info(f"成功加载已存在的向量数据库: {self.persist_directory}")
            else:
                logger.info("未找到已存在的向量数据库，将创建新的数据库")
        except Exception as e:
            logger.error(f"加载向量数据库失败: {str(e)}")
            logger.info("将创建新的向量数据库")

    def import_document(self, file_path: str) -> List[Document]:
        """导入文档并按行分块"""
        try:
            # 获取文件扩展名
            file_ext = Path(file_path).suffix.lower()
            
            # 根据文件类型选择加载器
            if file_ext == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_ext in ['.doc', '.docx']:
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_ext}")
            
            # 加载文档
            documents = loader.load()
            
            # 按行分块
            chunks = []
            for i, doc in enumerate(documents):
                # 获取原始文本内容
                text = doc.page_content
                
                # 按行分割
                lines = text.split('\n')
                
                # 创建文档列表
                for j, line in enumerate(lines):
                    if line.strip():  # 跳过空行
                        chunk = Document(
                            page_content=line.strip(),
                            metadata={
                                "row": j,
                                "source": doc.metadata.get("source", "未知来源"),
                                "page": doc.metadata.get("page", 0)
                            }
                        )
                        chunks.append(chunk)
            
            # 分批处理文档，每批最多处理10个文档
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                try:
                    # 添加到向量数据库
                    if self.vector_store is None:
                        self.vector_store = Chroma.from_documents(
                            documents=batch_chunks,
                            embedding=self.embeddings,
                            persist_directory=self.persist_directory
                        )
                    else:
                        self.vector_store.add_documents(batch_chunks)
                    
                    # 每批处理完后等待一段时间
                    if i + batch_size < len(chunks):
                        time.sleep(2)  # 批次间等待2秒
                        
                except Exception as e:
                    logger.error(f"处理批次 {i//batch_size + 1} 失败: {str(e)}")
                    raise
            
            # 保存文档信息
            self.documents.extend(chunks)
            
            logger.info(f"成功导入文档: {file_path}, 分块数量: {len(chunks)}")
            return chunks
            
        except Exception as e:
            logger.error(f"导入文档失败: {str(e)}")
            raise
            
    def delete_document(self, doc_id: str):
        """删除向量数据库中的文档"""
        try:
            if self.vector_store is None:
                raise ValueError("向量数据库未初始化")
                
            # 从向量数据库中删除
            self.vector_store.delete([doc_id])
            
            # 从文档列表中删除
            self.documents = [doc for doc in self.documents if doc.metadata.get('doc_id') != doc_id]
            
            logger.info(f"成功删除文档: {doc_id}")
            
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            raise
            
    def query(self, question: str, top_k: int = 3) -> str:
        """查询相关文档"""
        try:
            if self.vector_store is None:
                return "未找到相关政策和规定"
                
            # 搜索相似文档
            docs = self.vector_store.similarity_search(question, k=top_k)
            
            if not docs:
                return "未找到相关政策和规定"
                
            # 返回最相关文档的内容
            return docs[0].page_content
            
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            return "未找到相关政策和规定"
            
    def save_vector_store(self):
        """保存向量数据库"""
        try:
            if self.vector_store is None:
                raise ValueError("向量数据库未初始化")
            
            # 确保目录存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # ChromaDB会自动持久化，不需要显式调用save_local
            logger.info(f"向量数据库已自动保存到: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"保存向量数据库失败: {str(e)}")
            raise
            
    def load_vector_store(self):
        """加载向量数据库"""
        try:
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                self.vector_store = FAISS.load_local(
                    self.persist_directory,
                    self.embeddings
                )
                logger.info(f"成功加载向量数据库: {self.persist_directory}")
            else:
                logger.info("未找到已存在的向量数据库，将创建新的数据库")
                self.vector_store = FAISS.from_documents(
                    [],  # 空文档列表
                    self.embeddings
                )
        except Exception as e:
            logger.error(f"加载向量数据库失败: {str(e)}")
            raise 