from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from router import user, auth, data, analysis, chart, ai, document
import logging
import traceback
import uvicorn
import numpy as np
import os

# 配置 NumPy 错误处理
np.seterr(all='ignore')  # 忽略所有 NumPy 警告

# 设置环境变量
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
os.environ["RELOAD_DIRS"] = "router"  # 只监视 router 目录

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="SmartBI Backend API",
    description="智能BI系统后端API文档",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error occurred: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc)
        }
    )

# 注册路由
app.include_router(auth.router)
app.include_router(user.router, prefix="/api/v1", tags=["用户管理"])
app.include_router(data.router)
app.include_router(analysis.router)
app.include_router(chart.router)
app.include_router(ai.router)
app.include_router(document.router)

@app.get("/")
async def root():
    return {"message": "Welcome to SmartBI Backend API"}

if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            reload_delay=1,
            log_level="info",
            workers=1
        )
    except KeyboardInterrupt:
        print("正在优雅地关闭服务器...")
    except Exception as e:
        print(f"服务器发生错误: {str(e)}")
    finally:
        print("服务器已关闭") 