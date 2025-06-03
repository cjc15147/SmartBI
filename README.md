项目简介
本项目为“基于智能BI的机房报价稽核系统”，包含前端（SmartBI_front）和后端（SmartBI_backend）两部分。
后端：基于 FastAPI，负责数据处理、RAG文档管理、AI接口等。
前端：基于 Vue3 + Element Plus，提供可视化操作界面，支持数据上传、RAG文档管理等功能。
后端（SmartBI_backend）
主要功能
用户管理、认证
机房数据管理
RAG文档上传与检索
AI智能问答接口
环境要求
Python 3.8+
推荐使用虚拟环境（venv/conda）
安装依赖
Apply to .gitignore
cd SmartBI_backend
pip install -r requirements.txt
启动方式
Apply to .gitignore
# 启动 FastAPI 服务（默认端口8080）
python main.py
启动后可访问接口文档：http://127.0.0.1:8080/docs
重要说明
RAG文档的本地向量数据库存储在 SmartBI_backend/vector_db 目录下。
上传的临时文件存储在 SmartBI_backend/uploads 目录下。
前端（SmartBI_front）
主要功能
机房数据的可视化展示与上传
RAG文档的上传与管理
智能问答交互界面
环境要求
Node.js 16+
npm 8+ 或 yarn
安装依赖
Apply to .gitignore
cd SmartBI_front
npm install
启动方式
Apply to .gitignore
npm run dev
启动后访问：http://localhost:3000
代理说明
前端通过 Vite 代理将 /api 开头的请求转发到后端（默认 http://127.0.0.1:8080）。
常见问题
端口冲突：如 8080 或 3000 端口被占用，请修改对应配置文件中的端口号。
依赖安装失败：请确认 Python/Node 版本，或尝试更换国内镜像源。
RAG文档无法上传/检索：请确保后端 vector_db 目录为英文路径，且有写入权限。
如需详细功能说明或遇到问题，请查阅各自目录下的 README 或联系开发者。
