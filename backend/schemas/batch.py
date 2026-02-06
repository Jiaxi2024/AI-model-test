"""批量测试相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class BatchRequest(BaseModel):
    """批量测试请求"""
    model_config_id: str = Field(description="模型配置 ID")
    keywords: list[str] = Field(min_length=1, max_length=200, description="关键词列表")
    prompt_template: str = Field(description="提示词模板，使用 {keyword} 作为占位符")
    params: dict | None = Field(default=None, description="自定义模型参数")

    model_config = {"protected_namespaces": ()}
