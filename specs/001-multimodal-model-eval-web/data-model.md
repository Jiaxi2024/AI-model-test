# 数据模型: 统一多模态模型评测网页

**分支**: `001-multimodal-model-eval-web` | **日期**: 2026-02-06

## 实体关系概览

```
ModelConfig 1───N TestRecord
ModelConfig 1───N ComparisonGroup
KeywordBatch 1───N TestRecord
ComparisonSession 1───2 ComparisonGroup
ComparisonSession 1───1 TestInput
ComparisonGroup 1───1 TestRecord
TestRecord N───1 TestInput
TestInput 1───N UploadedFile
```

## 实体定义

### 1. ModelConfig（模型配置）

代表一个可用的模型及其参数配置。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| name | String(100) | NOT NULL | 模型显示名称，如 "Qwen-Omni" |
| model_id | String(200) | NOT NULL | API 模型标识符，如 "qwen-omni-turbo" |
| provider | String(50) | NOT NULL, DEFAULT "aliyun" | 服务商标识 |
| api_endpoint | String(500) | NOT NULL | API 端点 URL |
| default_params | JSON | DEFAULT {} | 默认参数，如 {"temperature": 0.7, "max_tokens": 2048} |
| supported_modalities | JSON | NOT NULL | 支持的输入模态列表，如 ["text", "image", "audio", "video"] |
| is_active | Boolean | DEFAULT true | 是否启用 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 最后更新时间 |

**唯一性规则**: (model_id, provider) 唯一

---

### 2. TestRecord（测试记录）

代表一次完整的模型推理交互记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| model_config_id | UUID | FK → ModelConfig.id, NOT NULL | 使用的模型配置 |
| test_input_id | UUID | FK → TestInput.id, NOT NULL | 关联的输入内容 |
| custom_params | JSON | DEFAULT {} | 本次请求的自定义参数（覆盖模型默认参数） |
| prompt_text | Text | NULLABLE | 本次请求的完整提示词文本 |
| output_text | Text | NULLABLE | 模型返回的文本内容 |
| output_audio_path | String(500) | NULLABLE | 模型返回的音频文件路径 |
| token_input | Integer | DEFAULT 0 | 输入 Token 消耗 |
| token_output | Integer | DEFAULT 0 | 输出 Token 消耗 |
| response_time_ms | Integer | DEFAULT 0 | 响应耗时（毫秒） |
| status | Enum | NOT NULL | 状态：pending / running / success / failed / timeout |
| error_message | Text | NULLABLE | 失败时的错误信息 |
| keyword_batch_id | UUID | FK → KeywordBatch.id, NULLABLE | 所属批量测试（如有） |
| comparison_session_id | UUID | FK → ComparisonSession.id, NULLABLE | 所属对比会话（如有） |
| created_at | DateTime | NOT NULL | 创建时间 |

**状态流转**:
```
pending → running → success
pending → running → failed
pending → running → timeout
```

---

### 3. TestInput（测试输入）

代表一组用户输入内容（文本 + 附件），可被多条 TestRecord 复用（如对比场景）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| text_content | Text | NULLABLE | 用户输入的文本内容 |
| input_type | Enum | NOT NULL | 输入类型：single / comparison / batch |
| created_at | DateTime | NOT NULL | 创建时间 |

---

### 4. UploadedFile（上传文件）

代表用户上传的一个媒体文件。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| test_input_id | UUID | FK → TestInput.id, NOT NULL | 所属输入 |
| file_name | String(255) | NOT NULL | 原始文件名 |
| file_path | String(500) | NOT NULL | 服务端存储路径 |
| file_size | Integer | NOT NULL | 文件大小（字节） |
| mime_type | String(100) | NOT NULL | MIME 类型，如 "image/jpeg" |
| modality | Enum | NOT NULL | 模态类型：image / video / audio |
| created_at | DateTime | NOT NULL | 创建时间 |

**校验规则**:
- image: 最大 10MB，支持 MIME: image/jpeg, image/png, image/gif, image/webp
- video: 最大 100MB，支持 MIME: video/mp4, video/webm
- audio: 最大 25MB，支持 MIME: audio/webm, audio/wav, audio/mp3, audio/mpeg

---

### 5. KeywordBatch（关键词批次）

代表一次批量测试任务。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| model_config_id | UUID | FK → ModelConfig.id, NOT NULL | 使用的模型配置 |
| keywords | JSON | NOT NULL | 关键词列表，如 ["猫", "狗", "鸟"] |
| prompt_template | Text | NOT NULL | 提示词模板，如 "请描述{keyword}的特征" |
| custom_params | JSON | DEFAULT {} | 自定义模型参数 |
| total_count | Integer | NOT NULL | 关键词总数 |
| completed_count | Integer | DEFAULT 0 | 已完成数 |
| failed_count | Integer | DEFAULT 0 | 失败数 |
| status | Enum | NOT NULL | 状态：pending / running / completed / cancelled |
| created_at | DateTime | NOT NULL | 创建时间 |
| completed_at | DateTime | NULLABLE | 完成时间 |

**状态流转**:
```
pending → running → completed
pending → running → cancelled (用户取消)
```

---

### 6. ComparisonSession（对比会话）

代表一次模型对比任务（MVP 固定 2 组）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| test_input_id | UUID | FK → TestInput.id, NOT NULL | 共用的输入内容 |
| status | Enum | NOT NULL | 状态：pending / running / completed / failed |
| created_at | DateTime | NOT NULL | 创建时间 |

---

### 7. ComparisonGroup（对比组）

代表对比会话中的一组模型配置（与 ComparisonSession 组合使用）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 唯一标识 |
| comparison_session_id | UUID | FK → ComparisonSession.id, NOT NULL | 所属对比会话 |
| model_config_id | UUID | FK → ModelConfig.id, NOT NULL | 使用的模型配置 |
| custom_params | JSON | DEFAULT {} | 本组自定义参数 |
| group_index | Integer | NOT NULL | 组序号（0=左，1=右） |
| test_record_id | UUID | FK → TestRecord.id, NULLABLE | 关联的测试记录（执行后填充） |

**约束**: (comparison_session_id, group_index) 唯一；MVP 阶段 group_index 仅允许 0 和 1

---

## 索引建议

| 表 | 索引 | 用途 |
|----|------|------|
| TestRecord | (created_at DESC) | 历史记录按时间排序 |
| TestRecord | (model_config_id, created_at DESC) | 按模型筛选历史记录 |
| TestRecord | (status) | 按状态查询 |
| TestRecord | (keyword_batch_id) | 批量测试关联查询 |
| TestRecord | (comparison_session_id) | 对比会话关联查询 |
| UploadedFile | (test_input_id) | 查询输入关联的文件 |
| KeywordBatch | (created_at DESC) | 批量任务列表 |
