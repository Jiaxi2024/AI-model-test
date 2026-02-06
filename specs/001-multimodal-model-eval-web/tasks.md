# Tasks: 统一多模态模型评测网页

**Input**: Design documents from `/specs/001-multimodal-model-eval-web/`
**Prerequisites**: plan.md, spec.md, ui-design.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: 不包含测试任务（PRD 未要求 TDD）。

**Organization**: 任务按用户故事分组，每个故事可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3...）
- 包含精确文件路径

---

## Phase 1: Setup（项目初始化）

**Purpose**: 创建项目骨架、安装依赖、配置环境

- [X] T001 创建项目目录结构（backend/, frontend/, uploads/, data/, tests/）及所有 __init__.py 文件
- [X] T002 创建 requirements.txt，包含所有 Python 依赖（fastapi, uvicorn, sse-starlette, sqlalchemy[asyncio], aiosqlite, openai, python-multipart, python-dotenv, pydantic）in requirements.txt
- [X] T003 [P] 创建 .env.example 环境变量示例文件，包含 DASHSCOPE_API_KEY 占位 in .env.example
- [X] T004 [P] 创建配置管理模块，加载环境变量和定义常量（API 端点、超时 60s、文件大小限制等）in backend/config.py
- [X] T005 创建 FastAPI 应用入口文件，挂载 API 路由到 /api、挂载前端静态文件到 /、内嵌 uvicorn.run() 启动 in app.py

---

## Phase 2: Foundational（基础设施）

**Purpose**: 数据库、核心模型、共用前端框架 — 所有用户故事的前置依赖

**⚠️ CRITICAL**: 此阶段必须完成后才能开始任何用户故事

- [X] T006 创建 SQLAlchemy 异步引擎、会话管理、数据库初始化逻辑（自动创建 data/eval.db）in backend/database.py
- [X] T007 创建 ORM 基类（声明 Base + 通用字段 mixin）in backend/models/base.py
- [X] T008 [P] 创建 ModelConfig ORM 模型（含所有字段、唯一约束、JSON 字段）in backend/models/model_config.py
- [X] T009 [P] 创建 TestInput ORM 模型 in backend/models/test_input.py
- [X] T010 [P] 创建 UploadedFile ORM 模型（含文件校验规则常量）in backend/models/uploaded_file.py
- [X] T011 [P] 创建 TestRecord ORM 模型（含状态枚举、外键关系、索引）in backend/models/test_record.py
- [X] T012 [P] 创建 KeywordBatch ORM 模型（含状态枚举）in backend/models/keyword_batch.py
- [X] T013 [P] 创建 ComparisonSession + ComparisonGroup ORM 模型 in backend/models/comparison.py
- [X] T014 创建模型统一导出 in backend/models/__init__.py
- [X] T015 创建通用 Pydantic Schema（分页请求/响应、错误响应、状态枚举）in backend/schemas/common.py
- [X] T016 创建阿里云模型 API 客户端封装（OpenAI 兼容接口、流式调用、超时 60s、错误处理）in backend/services/model_client.py
- [X] T017 创建文件上传/校验/存储服务（格式校验、大小校验、存储到 uploads/）in backend/services/file_manager.py
- [X] T018 创建文件上传 API 路由（POST /api/files/upload）in backend/api/files.py
- [X] T019 创建模型列表 API 路由（GET /api/models, GET /api/models/{id}）in backend/api/models.py
- [X] T020 创建 API 路由注册模块，将所有路由挂载到 FastAPI app in backend/api/__init__.py
- [X] T021 创建前端 SPA 主页面骨架（HTML 结构、CDN 引入字体/图标/Chart.js、M3 布局容器）in frontend/index.html
- [X] T022 创建 M3 设计令牌 CSS 文件（全部 CSS Variables、全局样式、组件基础样式、Navigation Rail 样式）in frontend/css/app.css
- [X] T023 [P] 创建前端 API 调用封装模块（fetch 封装、SSE 接收、错误处理）in frontend/js/api.js
- [X] T024 [P] 创建前端 Hash 路由模块（页面切换、导航高亮）in frontend/js/router.js
- [X] T025 [P] 创建前端工具函数模块（格式化时间、截断文本、防抖函数等）in frontend/js/utils.js
- [X] T026 创建前端导航栏组件（Navigation Rail：图标+标签、选中态、悬停态）in frontend/js/components/navbar.js
- [X] T027 创建前端应用入口（初始化路由、加载导航栏、挂载页面容器）in frontend/js/app.js
- [X] T028 创建数据库初始化种子数据脚本（预置阿里云 Qwen 系列模型配置：qwen-omni-turbo, qwen-plus, qwen-flash 等）in backend/database.py（init_db 函数内）

**Checkpoint**: 基础设施就绪 — 可启动 python app.py，浏览器可见空白 SPA 骨架 + Navigation Rail，API /api/models 返回模型列表

---

## Phase 3: User Story 1 — 单模型多模态推理测试 (Priority: P1) 🎯 MVP

**Goal**: 用户选择模型、输入文本/上传文件/录音，点击发送后以流式方式看到模型输出

**Independent Test**: 选择 Qwen-Omni → 输入文字 → 点击发送 → 输出区域逐字展示模型响应

### Implementation for User Story 1

- [X] T029 [US1] 创建推理相关 Pydantic Schema（InferenceRequest, SSE 事件模型）in backend/schemas/inference.py
- [X] T030 [US1] 创建单次推理服务（接收多模态输入、构建 API 请求、流式调用模型、保存 TestRecord）in backend/services/inference.py
- [X] T031 [US1] 创建推理 API 路由（POST /api/inference，返回 SSE EventSourceResponse）in backend/api/inference.py
- [X] T032 [P] [US1] 创建前端模型选择器组件（下拉列表、参数配置折叠面板：temperature/max_tokens）in frontend/js/components/model-selector.js
- [X] T033 [P] [US1] 创建前端文本输入组件（多行输入框、Ctrl+Enter 发送、占位符提示）in frontend/js/components/text-input.js
- [X] T034 [P] [US1] 创建前端文件上传组件（拖拽上传、格式/大小前端校验、校验失败时展示 M3 Error Toast 提示、缩略图预览、多文件 Chip 列表）in frontend/js/components/file-upload.js
- [X] T035 [P] [US1] 创建前端麦克风录音组件（MediaRecorder API、录音中脉冲动画、波形预览、权限拒绝引导）in frontend/js/components/audio-recorder.js
- [X] T036 [P] [US1] 创建前端输出展示组件（SSE 流式文本渲染、闪烁光标、音频播放器、Token/耗时统计、错误信息展示、重试按钮可重新触发同一请求）in frontend/js/components/output-display.js
- [X] T037 [US1] 创建前端推理测试页面（组装所有组件：模型选择器+参数+文本输入+文件上传+录音+发送按钮+输出区，左右分栏布局）in frontend/js/pages/inference.js
- [X] T038 [US1] 集成推理页面到路由系统，设为默认首页 in frontend/js/app.js

**Checkpoint**: MVP 完成 — 用户可完成文本/图片/视频/语音输入 → 流式模型输出的完整测试流程

---

## Phase 4: User Story 2 — 文字输入 AI 自动补全 (Priority: P2)

**Goal**: 文本输入框中输入时实时展示 AI 补全建议，Tab 键接受

**Independent Test**: 在文本框输入若干字符 → 500ms 后出现灰色补全建议 → 按 Tab 自动填充

### Implementation for User Story 2

- [X] T039 [US2] 创建自动补全服务（调用轻量模型 API 生成 1-3 条建议、防抖控制）in backend/services/autocomplete.py
- [X] T040 [US2] 创建自动补全 API 路由（POST /api/autocomplete）in backend/api/autocomplete.py
- [X] T041 [US2] 增强前端文本输入组件：添加 500ms 防抖、调用补全 API、内联灰色建议文本、Tab 接受、Esc 忽略、继续输入时更新 in frontend/js/components/text-input.js

**Checkpoint**: 文本输入框具备 AI 自动补全能力

---

## Phase 5: User Story 3 — 双模型对比测试 (Priority: P2)

**Goal**: 用户选择两组模型/参数，输入相同内容，系统并行调用两个模型并将结果左右并排展示

**Independent Test**: 选择 Qwen-Omni(左) + Qwen-Plus(右) → 输入文本 → 两组输出同时流式展示

### Implementation for User Story 3

- [X] T042 [US3] 创建对比相关 Pydantic Schema（ComparisonRequest, 对比 SSE 事件模型）in backend/schemas/comparison.py
- [X] T043 [US3] 创建模型对比服务（并行调用两组模型 API、合并 SSE 流、标记 group 0/1、保存 ComparisonSession + ComparisonGroup + TestRecord）in backend/services/comparison.py
- [X] T044 [US3] 创建对比 API 路由（POST /api/comparison，返回带 group 标记的 SSE 流）in backend/api/comparison.py
- [X] T045 [US3] 创建前端模型对比页面（共用输入区 + 两组模型选择器 + 并排输出区，蓝/紫色边框区分，复用 output-display 组件）in frontend/js/pages/comparison.js

**Checkpoint**: 双模型对比功能可用，两组输出并排流式展示

---

## Phase 6: User Story 4 — 关键词与批量测试 (Priority: P3)

**Goal**: 用户输入关键词列表 + 提示词模板，系统自动逐一发送请求，以表格展示所有结果并支持导出

**Independent Test**: 输入 3 个关键词 + 模板 → 执行 → 进度条更新 → 表格展示结果 → 导出 CSV

### Implementation for User Story 4

- [X] T046 [US4] 创建批量测试相关 Pydantic Schema（BatchRequest, BatchDetail, 进度 SSE 事件）in backend/schemas/batch.py
- [X] T047 [US4] 创建批量测试服务（逐一拼接关键词+模板、调用模型、更新进度、失败继续、结果聚合、CSV/JSON 导出）in backend/services/batch.py
- [X] T048 [US4] 创建批量测试 API 路由（POST /api/batch 创建任务、GET /api/batch/{id} 查询、GET /api/batch/{id}/stream SSE 进度、GET /api/batch/{id}/export 导出）in backend/api/batch.py
- [X] T049 [US4] 创建前端批量测试页面（模型选择 + 模板输入 + 关键词列表输入 + 进度条 + 结果表格 + 导出按钮）in frontend/js/pages/batch.js

**Checkpoint**: 批量测试功能可用，含实时进度和结果导出

---

## Phase 7: User Story 5 — 历史记录查看与管理 (Priority: P3)

**Goal**: 用户可查看所有测试记录，支持筛选/搜索/查看详情/删除/批量清理

**Independent Test**: 执行几次测试后 → 进入历史页 → 按模型筛选 → 点击查看详情 → 删除一条记录

### Implementation for User Story 5

- [X] T050 [US5] 创建历史记录相关 Pydantic Schema（HistoryList, TestRecordDetail, 筛选参数, 批量删除请求）in backend/schemas/history.py
- [X] T051 [US5] 创建历史记录服务（分页查询、多条件筛选、关键字搜索、详情查询、单条删除、批量删除/全部清空）in backend/services/history.py
- [X] T052 [US5] 创建历史记录 API 路由（GET /api/history 列表、GET /api/history/{id} 详情、DELETE /api/history/{id} 删除、POST /api/history/batch-delete 批量删除）in backend/api/history.py
- [X] T053 [US5] 创建前端历史记录页面（筛选栏 + 记录列表卡片 + 详情展开 + 复选框批量删除 + 分页组件）in frontend/js/pages/history.js

**Checkpoint**: 历史记录功能可用，含筛选、搜索、删除、分页

---

## Phase 8: User Story 6 — 数据报表与用量统计 (Priority: P3)

**Goal**: 用户可查看 Token 总消耗、测试次数等核心指标，以及按模型/时间段的可视化图表

**Independent Test**: 积累测试数据后 → 进入报表页 → 查看总览指标卡片 → 切换按模型/按时间段查看图表

### Implementation for User Story 6

- [X] T054 [US6] 创建统计相关 Pydantic Schema（OverviewStats, UsageStats）in backend/schemas/statistics.py
- [X] T055 [US6] 创建统计聚合服务（总览指标聚合、按模型分组统计、按时间段分组统计）in backend/services/statistics.py
- [X] T056 [US6] 创建统计 API 路由（GET /api/statistics/overview, GET /api/statistics/usage）in backend/api/statistics.py
- [X] T057 [US6] 创建前端数据报表页面（核心指标卡片 + 时间筛选 + Chart.js 折线图/柱状图/饼图 + 悬浮详情）in frontend/js/pages/statistics.js

**Checkpoint**: 数据报表功能可用，含可视化图表和交互式筛选

---

## Phase 9: Settings（设置功能）

**Purpose**: API Key 配置页面

- [X] T058 创建设置 API 路由（POST /api/settings/api-key 保存、DELETE /api/settings/api-key 清除）in backend/api/settings.py
- [X] T059 创建前端设置页面（API Key 输入框 + 脱敏展示 + 保存/恢复默认按钮 + 关于信息）in frontend/js/pages/settings.js

**Checkpoint**: 用户可在网页端配置自定义 API Key

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: 全局优化、错误处理、边界场景

- [X] T060 [P] 添加全局错误处理中间件（统一 JSON 错误格式、日志记录）in app.py
- [X] T061 [P] 添加前端 Toast 通知组件（成功/错误/警告提示，自动消失）in frontend/js/components/toast.js
- [X] T062 [P] 添加前端空状态组件（历史为空、搜索无结果、报表无数据的友好提示）in frontend/js/utils.js
- [X] T063 [P] 添加前端加载骨架屏组件（页面加载时的 Skeleton 占位）in frontend/css/app.css
- [X] T064 添加响应式布局适配（Tablet 单栏、Mobile Bottom Navigation）in frontend/css/app.css
- [X] T065 前端交互动画完善（页面切换淡入淡出、卡片悬停阴影、按钮状态过渡）in frontend/css/app.css
- [X] T066 全局代码审查与清理（移除 TODO、统一错误日志格式、检查文件引用完整性）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 — 可立即开始
- **Foundational (Phase 2)**: 依赖 Phase 1 完成 — **阻塞所有用户故事**
- **User Stories (Phase 3-8)**: 全部依赖 Phase 2 完成
  - US1 (P1): 最高优先级，必须首先完成 → 形成 MVP
  - US2 (P2): 依赖 US1 的文本输入组件已存在
  - US3 (P2): 复用 US1 的输出展示组件，可与 US2 并行
  - US4 (P3): 复用 US1 的模型客户端，可独立开发
  - US5 (P3): 依赖 US1 产生的测试记录数据
  - US6 (P3): 依赖 US1 产生的测试记录数据
- **Settings (Phase 9)**: 可在 Phase 2 之后任意时间开发
- **Polish (Phase 10)**: 依赖所有用户故事完成

### User Story Dependencies

- **US1 (P1)**: 仅依赖 Phase 2 → 可独立完成并交付 MVP
- **US2 (P2)**: 增强 US1 的文本输入组件 → 需 US1 的 text-input.js 已存在
- **US3 (P2)**: 复用 US1 的 output-display.js 组件 → 需 US1 完成；可与 US2 并行
- **US4 (P3)**: 复用 model_client.py → 需 Phase 2 完成；可与 US2/US3 并行
- **US5 (P3)**: 查询 TestRecord 数据 → 需 US1 至少执行过测试产生数据
- **US6 (P3)**: 聚合 TestRecord 统计 → 需 US1 至少执行过测试产生数据

### Within Each User Story

- Schema → Service → API Route → Frontend Page
- 后端 [P] 任务可与前端 [P] 组件并行
- 前端页面（集成任务）必须在所有组件完成后

### Parallel Opportunities

**Phase 2 内部并行**:
- T008~T013（6 个 ORM 模型）可全部并行
- T023~T025（3 个前端模块）可全部并行

**User Story 1 内部并行**:
- T032~T036（5 个前端组件）可全部并行
- T029 后端 Schema 与 T032~T036 前端组件可并行

**跨 User Story 并行**:
- Phase 2 完成后，US2 + US3 可并行
- US4、US5、US6 在 US1 完成后可全部并行

---

## Parallel Example: User Story 1

```bash
# 后端 Schema（先行）:
Task T029: 创建推理 Pydantic Schema in backend/schemas/inference.py

# 前端组件（全部并行，与 T029 也可并行）:
Task T032: 创建模型选择器组件 in frontend/js/components/model-selector.js
Task T033: 创建文本输入组件 in frontend/js/components/text-input.js
Task T034: 创建文件上传组件 in frontend/js/components/file-upload.js
Task T035: 创建录音组件 in frontend/js/components/audio-recorder.js
Task T036: 创建输出展示组件 in frontend/js/components/output-display.js

# 后端服务 + 路由（依赖 T029）:
Task T030: 创建推理服务 in backend/services/inference.py
Task T031: 创建推理 API 路由 in backend/api/inference.py

# 前端页面集成（依赖 T032~T036 + T031）:
Task T037: 创建推理测试页面 in frontend/js/pages/inference.js
Task T038: 集成到路由系统 in frontend/js/app.js
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001~T005)
2. Complete Phase 2: Foundational (T006~T028)
3. Complete Phase 3: User Story 1 (T029~T038)
4. **STOP and VALIDATE**: 用户可完成 文本/图片/视频/语音 → 流式模型输出 全流程
5. 部署/演示 MVP

### Incremental Delivery

1. Setup + Foundational → 基础就绪 ✓
2. + User Story 1 → MVP 交付 ✓（核心推理测试）
3. + User Story 2 → 增加 AI 自动补全 ✓
4. + User Story 3 → 增加双模型对比 ✓
5. + User Story 4 → 增加批量测试 ✓
6. + User Story 5 → 增加历史记录 ✓
7. + User Story 6 → 增加数据报表 ✓
8. + Settings + Polish → 完整交付 ✓

每个增量都独立可用，不破坏已有功能。

---

## Notes

- [P] 任务 = 不同文件、无依赖，可并行执行
- [Story] 标签映射到 spec.md 中的用户故事，便于追溯
- 每个用户故事独立可完成和测试
- 每完成一个 Checkpoint 可暂停验证
- 前端不使用 Tailwind CSS，使用 CSS Variables 实现 M3 设计令牌（详见 ui-design.md）
