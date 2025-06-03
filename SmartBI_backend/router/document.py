from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import logging
from utils.rag_utils import RAGService
from pathlib import Path

# 创建路由
router = APIRouter(prefix="/api/v1/documents", tags=["文档管理"])

# 配置日志
logger = logging.getLogger(__name__)

# 初始化RAG服务
rag_service = RAGService()

# 创建上传文件目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/import")
async def import_document(file: UploadFile = File(...)):
    """
    导入文档到向量数据库
    
    参数:
    - file: 上传的文件（支持 .txt, .pdf, .doc, .docx 格式）
    
    返回:
    - 导入结果信息
    """
    try:
        # 检查文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.txt', '.pdf', '.doc', '.docx']:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件类型，仅支持 .txt, .pdf, .doc, .docx 格式"
            )
        
        # 保存上传的文件
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 导入文档到向量数据库
        chunks = rag_service.import_document(str(file_path))
        
        # 保存向量数据库
        rag_service.save_vector_store()
        
        # 删除临时文件
        os.remove(file_path)
        
        return JSONResponse(
            content={
                "success": True,
                "message": "文档导入成功",
                "data": {
                    "filename": file.filename,
                    "chunks_count": len(chunks)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"导入文档失败: {str(e)}")
        # 确保清理临时文件
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"导入文档失败: {str(e)}"
        )

@router.get("/list")
async def list_documents():
    """
    获取已导入的文档列表
    
    返回:
    - 文档列表信息
    """
    try:
        if not rag_service.documents:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "暂无导入的文档",
                    "data": []
                }
            )
            
        # 获取文档信息
        docs_info = []
        for doc in rag_service.documents:
            docs_info.append({
                "source": doc.metadata.get("source", "未知来源"),
                "page": doc.metadata.get("page", 0),
                "row": doc.metadata.get("row", 0)
            })
            
        return JSONResponse(
            content={
                "success": True,
                "message": "获取文档列表成功",
                "data": docs_info
            }
        )
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取文档列表失败: {str(e)}"
        ) 