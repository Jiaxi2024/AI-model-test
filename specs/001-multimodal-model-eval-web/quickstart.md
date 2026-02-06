# 快速启动指南: 统一多模态模型评测网页

## 前置条件

- Python 3.11+
- 阿里云 DashScope API Key（从 [阿里云百炼平台](https://bailian.console.aliyun.com/) 获取）

## 安装步骤

### 1. 克隆项目并进入目录

```bash
cd ai-model-test-V2
```

### 2. 创建并激活虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置 API Key

创建 `.env` 文件（或设置环境变量）：

```bash
# .env 文件内容
DASHSCOPE_API_KEY=sk-your-api-key-here
```

### 5. 启动服务

```bash
python app.py
```

服务启动后，在浏览器中打开 `http://localhost:8000` 即可使用。

## 核心依赖

### Python 后端

| 包名 | 用途 |
|------|------|
| fastapi | Web 框架 |
| uvicorn | ASGI 服务器 |
| sse-starlette | SSE 流式响应支持 |
| sqlalchemy[asyncio] | ORM（异步模式） |
| aiosqlite | SQLite 异步驱动 |
| openai | 阿里云 OpenAI 兼容 SDK |
| python-multipart | 文件上传支持 |
| python-dotenv | 环境变量管理 |
| pydantic | 数据校验 |

### 前端（CDN 引入，无需安装）

| 资源 | 用途 |
|------|------|
| Inter + Noto Sans SC (Google Fonts) | 西文 + 中文字体 |
| Material Symbols Outlined (Google Fonts) | M3 图标库 |
| Chart.js | 数据报表图表 |

**UI 设计语言**: Google Material Design 3，企业级淡色风格。详见 `ui-design.md`。

## 项目结构

```
ai-model-test-V2/
├── app.py                  # 入口文件（单脚本启动）
├── requirements.txt        # Python 依赖
├── .env                    # API Key 配置（需手动创建）
├── backend/
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接与初始化
│   ├── models/             # SQLAlchemy 数据模型
│   │   ├── __init__.py
│   │   ├── model_config.py
│   │   ├── test_record.py
│   │   ├── test_input.py
│   │   ├── uploaded_file.py
│   │   ├── keyword_batch.py
│   │   └── comparison.py
│   ├── services/           # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── inference.py    # 模型推理服务
│   │   ├── comparison.py   # 模型对比服务
│   │   ├── batch.py        # 批量测试服务
│   │   ├── autocomplete.py # AI 自动补全服务
│   │   ├── history.py      # 历史记录服务
│   │   └── statistics.py   # 统计服务
│   └── api/                # API 路由
│       ├── __init__.py
│       ├── models.py
│       ├── inference.py
│       ├── comparison.py
│       ├── batch.py
│       ├── history.py
│       ├── statistics.py
│       ├── autocomplete.py
│       ├── files.py
│       └── settings.py
├── frontend/
│   ├── index.html          # 主页面（SPA）
│   ├── css/
│   │   └── app.css         # M3 设计令牌 + 自定义样式（CSS Variables）
│   ├── js/
│   │   ├── app.js          # 主入口
│   │   ├── api.js          # API 调用封装
│   │   ├── router.js       # 前端路由
│   │   ├── components/     # UI 组件
│   │   │   ├── model-selector.js
│   │   │   ├── text-input.js
│   │   │   ├── file-upload.js
│   │   │   ├── audio-recorder.js
│   │   │   ├── output-display.js
│   │   │   └── navbar.js
│   │   └── pages/          # 页面模块
│   │       ├── inference.js
│   │       ├── comparison.js
│   │       ├── batch.js
│   │       ├── history.js
│   │       ├── statistics.js
│   │       └── settings.js
│   └── assets/             # 静态资源
├── uploads/                # 上传文件存储（自动创建）
└── data/                   # SQLite 数据库文件（自动创建）
    └── eval.db
```

## 常用开发命令

```bash
# 启动开发服务器（自动重载）
python app.py --reload

# 查看 API 文档
# 启动后访问 http://localhost:8000/docs（Swagger UI）
```
