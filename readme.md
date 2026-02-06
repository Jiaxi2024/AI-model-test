# 统一多模态模型评测平台

基于阿里云 DashScope（通义千问）系列模型的统一评测 Web 平台，支持文本、图片、音频、视频等多模态输入，提供单次推理、双模型对比、关键词批量测试、历史记录管理和数据统计等功能。

## 功能特性

- **单次推理**：选择模型 + 多模态输入（文本/图片/音频/视频），流式输出结果
- **双模型对比**：同一输入并行调用两个模型，对比输出效果
- **关键词批量测试**：模板 + 关键词列表，逐一调用模型并汇总结果，支持 CSV/JSON 导出
- **历史记录**：查看所有测试记录，支持搜索、筛选、批量删除
- **数据报表**：测试次数、Token 消耗、模型使用分布等统计图表
- **设置**：API Key 配置（支持运行时覆盖）
- **AI 自动补全**：输入提示词时自动建议补全（Tab 接受）
- **麦克风录音**：浏览器原生录音上传

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / Uvicorn / SQLAlchemy 2.0 (async) / SQLite (WAL) |
| 前端 | 原生 HTML5 + CSS3 (Material Design 3) + JavaScript ES6 Modules |
| 模型 API | 阿里云 DashScope OpenAI 兼容接口 |
| 流式传输 | Server-Sent Events (SSE) via sse-starlette |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/<your-username>/ai-model-test-V2.git
cd ai-model-test-V2
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的阿里云百炼 API Key：

```
DASHSCOPE_API_KEY=sk-your-api-key-here
```

> API Key 获取地址：https://bailian.console.aliyun.com/

### 4. 启动服务

```bash
python app.py
```

访问 http://localhost:8000 即可使用。API 文档地址：http://localhost:8000/docs

## 项目结构

```
├── app.py                  # 应用入口（一键启动）
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
├── backend/
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库初始化
│   ├── models/             # SQLAlchemy ORM 模型
│   ├── schemas/            # Pydantic 请求/响应模型
│   ├── services/           # 业务逻辑
│   └── api/                # FastAPI 路由
├── frontend/
│   ├── index.html          # 单页应用入口
│   ├── css/app.css         # Material Design 3 样式
│   └── js/
│       ├── app.js          # 前端入口
│       ├── api.js          # API 调用封装
│       ├── router.js       # 前端路由
│       ├── utils.js        # 工具函数
│       ├── components/     # 可复用组件
│       └── pages/          # 页面模块
└── specs/                  # 需求/设计文档
```

## 支持的模型

| 模型 | 支持模态 |
|------|---------|
| Qwen-Omni-Turbo | 文本 + 图片 + 音频 + 视频 |
| Qwen-VL-Plus | 文本 + 图片 + 视频 |
| Qwen-Max | 文本 + 图片 |
| Qwen-Plus | 文本 + 图片 |
| Qwen-Turbo | 文本 |

## License

MIT
