# 基于智能BI的机房报价稽核前端项目（smartbi_vue）

## 项目简介
本项目是"基于智能BI的机房报价稽核系统"的前端部分，采用 Vue3 + Element Plus + ECharts 实现，支持智能数据分析、AI自动生成分析结论和可视化图表。用户可上传 Excel/CSV 数据，输入分析目标，系统自动调用后端 AI 服务，返回分析结论和 ECharts 图表。

## 主要功能
- **数据上传与预览**：支持 Excel/CSV 文件上传，预览前几行数据。
- **智能分析配置**：输入分析目标、图表名称、图表类型，支持折线图、柱状图、饼图、散点图。
- **AI智能分析**：自动调用后端 `/api/ai/gen` 接口，返回分析结论和 ECharts 图表配置。
- **结论展示**：AI 分析结论以对话框形式展示。
- **图表可视化**：ECharts 动态渲染分析结果。

## 目录结构
```
smartbi_vue/
├── public/           # 静态资源
│   ├── api/          # 接口请求
│   ├── assets/       # 静态资源
│   ├── components/   # 公共组件
│   ├── router/       # 路由
│   ├── store/        # 状态管理
│   ├── utils/        # 工具函数
│   └── views/        # 主要页面（如 analysis/detail.vue）
├── .gitignore        # 忽略文件配置
├── package.json      # 依赖配置
└── README.md         # 项目说明
```

## 开发环境
- Node.js 16.x 及以上
- npm 8.x 或 yarn/pnpm
- 推荐使用 VSCode 编辑器

## 安装依赖
```bash
npm install
# 或
yarn install
```

## 运行项目
```bash
npm run dev
# 或
yarn dev
```
启动后访问：http://localhost:3000

## 生产打包
```bash
npm run build
# 或
yarn build
```

## 常见问题
1. **node_modules 不上传**：已在 `.gitignore` 配置忽略。
2. **AI分析接口需后端支持**：请确保后端服务已启动，并代理 `/api` 到后端。
3. **token 认证**：登录后 token 自动存储，分析等操作需登录。
4. **ECharts 图表无法显示**：请确保 AI 返回的 `genChart` 字段为标准 ECharts option 对象。

## 参与贡献
如需二次开发或贡献代码，请先 fork 本仓库，提交 PR 前请确保代码通过本地测试。

---

如有问题请联系：chenjichao@sn.chinamobile.com
