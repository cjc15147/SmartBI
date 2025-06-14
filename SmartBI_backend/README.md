# 基于智能BI的机房报价稽核系统

## 项目简介
本项目是一个基于智能BI的机房报价稽核系统，用于分析和评估新增机房与存量机房的报价合理性。系统通过地理空间分析、数据挖掘和AI技术，提供全面的机房报价稽核服务。

## 主要功能
1. **数据分析**
   - 新增机房数据分析
   - 存量机房数据管理
   - 地理空间分析
   - 价格合理性评估

2. **智能稽核**
   - 自动生成稽核报告
   - 政策法规参考
   - 价格对比分析
   - 风险评估

3. **可视化展示**
   - 地图可视化
   - 数据图表展示
   - 分析结果展示

## 技术架构
### 1. 机房报价稽核模块 (data.py)
- **核心功能**：
  - 新增机房数据导入与分析
  - 存量机房数据管理
  - 地理空间分析
  - 价格合理性评估

- **技术栈**：
  - **数据处理**：
    - Pandas：数据清洗和预处理
    - NumPy：数值计算
    - SQLAlchemy：数据库ORM
  - **地理计算**：
    - Geopy：地理编码和距离计算
    - Folium：地图可视化
  - **数据存储**：
    - MySQL：关系型数据库
    - Chroma：向量数据库
  - **AI集成**：
    - LangChain：AI模型集成
    - Baichuan：大语言模型
    - RAG：检索增强生成

- **技术路线**：
  1. 数据导入与预处理
     - Excel数据解析
     - 数据清洗和标准化
     - 地理信息编码
  2. 空间分析
     - 地理距离计算
     - 周边机房分析
     - 价格对比分析
  3. 智能评估
     - RAG技术检索相关政策
     - 价格合理性评估
     - 风险评估

### 2. 通用数据分析模块 (ai_service.py)
- **核心功能**：
  - 智能问答
  - 政策法规检索
  - 数据分析报告生成
  - 知识库管理

- **技术栈**：
  - **AI模型**：
    - LangChain：AI框架
    - Baichuan：大语言模型
    - RAG：检索增强生成
  - **向量数据库**：
    - Chroma：文档向量存储
    - 文档分块和索引
  - **数据处理**：
    - Pandas：数据分析
    - NumPy：数值计算
  - **API服务**：
    - FastAPI：Web框架
    - Uvicorn：ASGI服务器

- **技术路线**：
  1. 知识库构建
     - 文档导入和分块
     - 向量化存储
     - 索引构建
  2. 智能问答
     - 问题理解
     - 相关文档检索
     - 答案生成
  3. 报告生成
     - 数据分析
     - 报告模板
     - 自动生成

### 3. RAG工具模块 (rag_utils.py)
- **核心功能**：
  - 文档导入和分块
  - 向量数据库操作
  - 知识检索和问答

- **技术栈**：
  - **文档处理**：
    - PyPDF2：PDF文档解析
    - python-docx：Word文档解析
    - LangChain TextSplitter：文本分块
  - **向量化**：
    - BaichuanTextEmbeddings：文本向量化
    - LangChain：向量化流程管理
  - **向量存储**：
    - Chroma：向量数据库
    - 持久化存储
  - **检索增强**：
    - 相似度搜索
    - 上下文构建
    - 答案生成

- **技术路线**：
  1. 文档处理流程
     - 支持多种格式（TXT、PDF、Word）
     - 按行分块处理
     - 文本预处理和清洗
  2. 向量化存储
     - 文档向量化
     - 向量数据库存储
     - 持久化管理
  3. 知识检索
     - 问题向量化
     - 相似度匹配
     - 上下文构建
     - 答案生成

## 项目结构
```
SmartBI-backend/
├── api/                    # API接口
│   ├── data.py            # 数据处理接口
│   ├── ai_service.py      # AI服务接口
│   └── user_api.py        # 用户管理接口
├── database/              # 数据库相关
│   ├── connection.py      # 数据库连接
│   └── models.py         # 数据模型
├── utils/                 # 工具类
│   ├── rag_utils.py      # RAG工具
│   └── geo_utils.py      # 地理计算工具
├── tests/                 # 测试用例
└── requirements.txt       # 项目依赖
```

## 安装部署
1. 克隆项目
```bash
git clone [项目地址]
cd SmartBI-backend
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置数据库
- 创建MySQL数据库
- 修改数据库连接配置

4. 启动服务
```bash
uvicorn main:app --reload
```

## 使用说明
1. **数据导入**
   - 支持Excel格式的新增机房数据导入
   - 支持存量机房数据管理

2. **数据分析**
   - 设置分析半径
   - 执行数据分析
   - 查看分析结果

3. **稽核报告**
   - 生成稽核报告
   - 查看政策参考
   - 导出分析结果

## 开发环境要求
- Python 3.11+
- MySQL 8.0+
- 操作系统: Windows/Linux/MacOS

## 主要依赖
- fastapi==0.104.1
- sqlalchemy==2.0.23
- pandas==2.1.3
- langchain==0.0.350
- chromadb==0.4.22
- geopy==2.4.1
- folium==0.14.0

## 注意事项
1. 确保数据库配置正确
2. 检查API密钥配置
3. 注意数据文件格式要求
4. 定期备份数据库

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 许可证
[许可证类型]

## 联系方式
[联系方式] 