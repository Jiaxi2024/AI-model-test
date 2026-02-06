# Implementation Plan: 统一多模态模型评测网页

**Branch**: `001-multimodal-model-eval-web` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-multimodal-model-eval-web/spec.md`

## Summary

构建一个团队内部使用的统一多模态模型评测网页，支持文本/图片/视频/语音输入，调用阿里云 Qwen 系列模型（含 Qwen-Omni 全模态）进行推理测试。技术方案采用 FastAPI 后端 + 原生 HTML/JS 前端，SQLite 持久化存储，通过 SSE 实现流式输出，单 Python 脚本一键启动。核心功能包括：单模型多模态推理、双模型对比、关键词批量测试、AI 自动补全、历史记录管理、数据报表统计。

**UI/UE 设计**: 采用 Google Material Design 3 设计语言，企业级淡色风格。详见 [ui-design.md](./ui-design.md)。

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Uvicorn, sse-starlette, SQLAlchemy 2.0+（异步模式）, aiosqlite, openai SDK, python-multipart, python-dotenv, Pydantic  
**Frontend Stack**: HTML5 + CSS3（CSS Variables 实现 M3 设计令牌）+ 原生 JavaScript ES6+；CDN 引入: Inter + Noto Sans SC 字体, Material Symbols Outlined 图标, Chart.js 图表库  
**Storage**: SQLite（通过 aiosqlite 异步驱动），文件系统（上传文件）  
**Testing**: pytest + pytest-asyncio + httpx（API 测试）  
**Target Platform**: Web 应用，运行于 Windows/macOS/Linux 本地服务器  
**Project Type**: Web 应用（Python 后端 + 静态前端，单进程）  
**Performance Goals**: API 响应 <500ms（不含模型推理时间）；SSE 流式首字节 <1s；历史记录查询 <2s（1000 条）  
**Constraints**: 单 Python 脚本启动；模型 API 超时阈值 60 秒；前端无需编译构建步骤  
**Scale/Scope**: 约 20 并发用户，数据量级万级测试记录

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution 文件为空模板（项目尚未定义特定原则），无阻塞性约束。以下为本项目自定义的设计原则检查：

| 原则 | 状态 | 说明 |
|------|------|------|
| 单脚本启动 | ✅ 通过 | `python app.py` 启动 FastAPI，内嵌前端静态文件服务 |
| 前端无构建 | ✅ 通过 | HTML + CSS Variables（M3 设计令牌）+ CDN 引入 Chart.js / 字体 / 图标，无需 Node.js |
| 数据本地化 | ✅ 通过 | SQLite 文件级数据库 + 本地文件系统 |
| API 可扩展 | ✅ 通过 | OpenAI 兼容接口层支持未来切换模型服务商 |
| 最小复杂度 | ✅ 通过 | 单进程、单数据库、无消息队列、无缓存层 |

**Re-check after Phase 1**: ✅ 全部通过。数据模型和 API 合约设计均遵循上述原则。

## Project Structure

### Documentation (this feature)

```text
specs/001-multimodal-model-eval-web/
├── spec.md              # 功能规格说明
├── plan.md              # 本文件（实现计划）
├── ui-design.md         # UI/UE 设计规范（Material Design 3）
├── research.md          # Phase 0 技术研究
├── data-model.md        # Phase 1 数据模型
├── quickstart.md        # Phase 1 快速启动指南
├── contracts/           # Phase 1 API 合约
│   └── openapi.yaml     # OpenAPI 3.1 规范
├── checklists/          # 质量检查清单
│   └── requirements.md  # 需求质量检查
└── tasks.md             # Phase 2 任务分解（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
ai-model-test-V2/
├── app.py                      # 入口文件：创建 FastAPI 应用，挂载路由和静态文件，启动 Uvicorn
├── requirements.txt            # Python 依赖清单
├── .env                        # 环境变量配置（API Key 等，需用户手动创建）
├── .env.example                # 环境变量示例文件
│
├── backend/                    # 后端代码
│   ├── __init__.py
│   ├── config.py               # 配置管理（环境变量加载、常量定义）
│   ├── database.py             # 数据库连接、会话管理、初始化
│   │
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── __init__.py         # 统一导出所有模型
│   │   ├── base.py             # 声明基类
│   │   ├── model_config.py     # 模型配置表
│   │   ├── test_input.py       # 测试输入表
│   │   ├── uploaded_file.py    # 上传文件表
│   │   ├── test_record.py      # 测试记录表
│   │   ├── keyword_batch.py    # 关键词批次表
│   │   └── comparison.py       # 对比会话表 + 对比组表
│   │
│   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── inference.py        # 推理相关 Schema
│   │   ├── comparison.py       # 对比相关 Schema
│   │   ├── batch.py            # 批量测试相关 Schema
│   │   ├── history.py          # 历史记录相关 Schema
│   │   ├── statistics.py       # 统计相关 Schema
│   │   └── common.py           # 通用 Schema（分页、错误等）
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── model_client.py     # 阿里云模型 API 客户端封装（OpenAI 兼容）
│   │   ├── inference.py        # 单次推理服务（含流式处理）
│   │   ├── comparison.py       # 模型对比服务（并行调用 + 流式合并）
│   │   ├── batch.py            # 批量测试服务（队列管理 + 进度跟踪）
│   │   ├── autocomplete.py     # AI 自动补全服务
│   │   ├── history.py          # 历史记录 CRUD 服务
│   │   ├── statistics.py       # 统计聚合服务
│   │   └── file_manager.py     # 文件上传/校验/存储服务
│   │
│   └── api/                    # FastAPI 路由层
│       ├── __init__.py         # 路由注册
│       ├── models.py           # GET /api/models
│       ├── inference.py        # POST /api/inference（SSE）
│       ├── comparison.py       # POST /api/comparison（SSE）
│       ├── batch.py            # POST/GET /api/batch（SSE 进度）
│       ├── history.py          # GET/DELETE /api/history
│       ├── statistics.py       # GET /api/statistics
│       ├── autocomplete.py     # POST /api/autocomplete
│       ├── files.py            # POST /api/files/upload
│       └── settings.py         # POST/DELETE /api/settings/api-key
│
├── frontend/                   # 前端代码（纯静态文件，FastAPI 挂载）
│   ├── index.html              # SPA 主页面骨架
│   ├── css/
│   │   └── app.css             # M3 设计令牌（CSS Variables）+ 全局样式 + 组件样式
│   ├── js/
│   │   ├── app.js              # 应用入口、初始化
│   │   ├── api.js              # API 调用封装（fetch + SSE）
│   │   ├── router.js           # 前端 Hash 路由
│   │   ├── utils.js            # 工具函数
│   │   ├── components/         # 可复用 UI 组件
│   │   │   ├── navbar.js       # 导航栏
│   │   │   ├── model-selector.js   # 模型选择器（下拉 + 参数配置）
│   │   │   ├── text-input.js       # 文本输入框（含 AI 自动补全）
│   │   │   ├── file-upload.js      # 文件上传组件（拖拽 + 预览）
│   │   │   ├── audio-recorder.js   # 麦克风录音组件
│   │   │   └── output-display.js   # 输出展示组件（流式渲染 + 音频播放）
│   │   └── pages/              # 页面模块
│   │       ├── inference.js    # 单模型推理页
│   │       ├── comparison.js   # 模型对比页
│   │       ├── batch.js        # 批量测试页
│   │       ├── history.js      # 历史记录页
│   │       ├── statistics.js   # 数据报表页
│   │       └── settings.js     # 设置页
│   └── assets/                 # 静态资源（图标等）
│
├── uploads/                    # 上传文件存储目录（自动创建）
├── data/                       # 数据库文件目录（自动创建）
│   └── eval.db                 # SQLite 数据库文件
│
└── tests/                      # 测试代码
    ├── __init__.py
    ├── conftest.py             # 测试配置（测试数据库、客户端 fixture）
    ├── unit/                   # 单元测试
    │   ├── test_file_manager.py
    │   ├── test_inference.py
    │   └── test_statistics.py
    ├── integration/            # 集成测试
    │   ├── test_api_inference.py
    │   ├── test_api_comparison.py
    │   ├── test_api_batch.py
    │   └── test_api_history.py
    └── contract/               # 合约测试
        └── test_openapi_compliance.py
```

**Structure Decision**: 采用 Web 应用结构，后端和前端在同一仓库中。后端为 Python（FastAPI），前端为纯静态文件（HTML/CSS/JS）。通过 FastAPI 的 `StaticFiles` 中间件将前端挂载到 `/` 路径，API 路由挂载到 `/api` 路径，实现单进程单端口服务。

## Complexity Tracking

无 Constitution 违反项，无需记录。
