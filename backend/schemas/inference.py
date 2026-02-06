"""推理相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    """推理请求"""
    model_config_id: str = Field(description="模型配置 ID")
    text: str | None = Field(default=None, description="文本输入")
    file_ids: list[str] = Field(default_factory=list, description="已上传文件的 ID 列表")
    params: dict | None = Field(default=None, description="自定义模型参数")

    # 允许 model_config 不与 pydantic 冲突
    model_config = {"protected_namespaces": ()}


class InferenceSSEToken(BaseModel):
    """SSE token 事件"""
    text: str


class InferenceSSEAudio(BaseModel):
    """SSE audio 事件"""
    audio_url: str


class InferenceSSEUsage(BaseModel):
    """SSE usage 事件"""
    input_tokens: int
    output_tokens: int


class InferenceSSEDone(BaseModel):
    """SSE done 事件"""
    record_id: str
    response_time_ms: int


class InferenceSSEError(BaseModel):
    """SSE error 事件"""
    message: str
