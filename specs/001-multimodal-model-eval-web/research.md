# 技术研究: 统一多模态模型评测网页

**分支**: `001-multimodal-model-eval-web` | **日期**: 2026-02-06

## 1. Web 框架选型

### Decision: FastAPI + 内嵌前端静态文件（HTML/CSS/JS）

### Rationale:
- PRD 要求"界面清晰美观、分栏布局、多功能页面导航（历史记录、模型对比、数据报表）"，需要自定义复杂 UI
- Gradio/Streamlit 组件化程度高但 UI 灵活性不足，无法满足多页面分栏导航需求
- FastAPI 支持高性能异步处理、SSE 流式响应、文件上传等核心能力
- 前端使用 HTML + CSS Variables（M3 设计令牌）+ 原生 JS，通过 FastAPI 的 `StaticFiles` 挂载，实现单脚本启动
- 无需 Node.js 编译步骤，前端文件直接由 Python 服务

### Alternatives considered:
- **Gradio**: 快速但 UI 定制能力不足，不支持复杂分栏导航
- **Streamlit**: 每次交互重新执行脚本，性能差，UI 定制受限
- **Reflex**: 生态较新，社区支持不够成熟
- **Django**: 过于重量级，不符合"单脚本启动"的轻量需求

## 2. 阿里云模型 API 接入方案

### Decision: 使用 OpenAI 兼容接口（HTTP REST） + DashScope SDK（实时语音场景）

### Rationale:
- 阿里云百炼平台提供 OpenAI 兼容接口（`https://dashscope.aliyuncs.com/compatible-mode/v1`），支持文本、图片、视频等多模态输入
- OpenAI 兼容接口支持 `stream=True` 实现 SSE 流式输出，与 FastAPI 的 `EventSourceResponse` 完美配合
- 对于实时语音对话场景（Qwen-Omni-Realtime），使用 DashScope Python SDK 的 WebSocket 接口
- 统一使用 `openai` Python SDK 作为主要客户端，降低代码复杂度

### Alternatives considered:
- **纯 DashScope SDK**: 接口风格不统一，社区文档不如 OpenAI SDK 丰富
- **纯 HTTP 调用**: 需要手动处理流式解析、重试等，工作量大

## 3. 流式响应方案

### Decision: FastAPI + sse-starlette（SSE 协议）

### Rationale:
- `sse-starlette` 库为 FastAPI 提供原生 SSE 支持，通过 `EventSourceResponse` 实现服务端推送
- 前端使用 `EventSource` API 或 `fetch` + `ReadableStream` 接收流式数据
- SSE 单向推送适合模型输出场景（服务端 → 客户端），比 WebSocket 更轻量
- 支持客户端断开检测，确保资源及时释放

### Alternatives considered:
- **WebSocket**: 双向通信过于复杂，模型输出场景只需单向推送
- **Long Polling**: 延迟高，不适合实时流式展示

## 4. 前端技术方案

### Decision: HTML + CSS Variables（M3 设计令牌）+ 原生 JavaScript（ES6+模块）+ Google Material Design 3

### Rationale:
- 采用 Google Material Design 3 设计语言，企业级淡色风格，简洁克制
- 不使用 Tailwind CSS，改用 **CSS Variables** 实现 M3 设计令牌（色彩、字体、间距、圆角、阴影），更贴合 M3 规范且无需额外依赖
- CDN 引入：Inter + Noto Sans SC 字体、Material Symbols Outlined 图标库、Chart.js 图表库
- 原生 JS 足以处理 SSE 接收、DOM 操作、文件上传等需求
- 使用 ES6 模块化组织代码，保持可维护性
- 音频录制使用浏览器原生 `MediaRecorder` API
- 色彩系统以蓝灰 (#1A73E8) 为主色调，Surface (#FFFFFF) 和 Surface Variant (#F1F3F4) 为背景色
- 完整 UI/UE 设计规范见 `ui-design.md`

### Alternatives considered:
- **React/Vue + Vite**: 需要 Node.js 构建步骤，违反"单 Python 脚本启动"要求
- **Tailwind CSS**: 可行但与 M3 设计令牌体系不完全对齐，CSS Variables 更直接
- **Alpine.js**: 可选增强，但核心功能用原生 JS 即可
- **Material Web Components**: Google 官方 M3 Web 组件库目前处于维护模式，不建议用于生产

## 5. 数据存储方案

### Decision: SQLite + SQLAlchemy（异步模式）

### Rationale:
- SQLite 零配置、文件级数据库，完美契合"本地存储、单脚本启动"需求
- SQLAlchemy 2.0+ 支持异步模式（`aiosqlite`），与 FastAPI 异步架构一致
- 上传文件存储在本地文件系统（`uploads/` 目录），数据库仅存引用路径
- 团队内部 20 人规模，SQLite 读写性能完全满足

### Alternatives considered:
- **PostgreSQL**: 需要额外安装和配置，过重
- **JSON 文件存储**: 不支持复杂查询（筛选、聚合统计）
- **TinyDB**: 性能和查询能力不如 SQLite

## 6. AI 自动补全方案

### Decision: 防抖 + 后端代理调用模型 API（轻量补全请求）

### Rationale:
- 前端输入框设置 500ms 防抖，避免频繁请求
- 后端接收当前输入文本，调用模型 API（使用较小模型如 qwen-flash 或 qwen-plus，低成本高速度）生成补全建议
- 返回 1-3 条补全建议，前端以内联灰色文本展示
- 用户按 Tab 接受补全

### Alternatives considered:
- **前端本地补全**: 无 AI 能力，只能做关键词匹配
- **独立补全服务**: 增加架构复杂度，不必要

## 7. 麦克风录音方案

### Decision: 浏览器 MediaRecorder API + WebM/Opus 格式

### Rationale:
- `MediaRecorder` 是浏览器原生 API，Chrome/Edge/Firefox 均支持
- 默认录制为 WebM/Opus 格式，压缩率高，传输快
- 录音完成后以 Blob 形式上传到后端，后端转换格式后发送给模型 API
- 权限被拒绝时，前端展示引导提示并提供手动上传音频文件的替代方案

### Alternatives considered:
- **Web Audio API + 手动 PCM 编码**: 复杂度高，浏览器兼容性需处理更多细节
- **第三方录音库（RecordRTC）**: 增加依赖，原生 API 已足够

## 8. 单脚本启动方案

### Decision: `python app.py` 一键启动，内置 Uvicorn

### Rationale:
- 入口文件 `app.py` 中使用 `uvicorn.run()` 启动 FastAPI 应用
- FastAPI 同时挂载前端静态文件（`/static`）和 API 路由（`/api`）
- 首次运行时自动创建 SQLite 数据库和 uploads 目录
- 用户只需配置环境变量 `DASHSCOPE_API_KEY`（或在 `.env` 文件中配置），然后 `python app.py` 即可

### Alternatives considered:
- **Docker Compose**: 增加部署复杂度
- **多进程启动（前端+后端分离）**: 违反"单脚本启动"要求
