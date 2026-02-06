"""对比相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class ComparisonGroupInput(BaseModel):
    """对比组输入"""
    model_config_id: str = Field(description="模型配置 ID")
    params: dict | None = Field(default=None, description="本组自定义参数")

    model_config = {"protected_namespaces": ()}


class ComparisonRequest(BaseModel):
    """对比请求"""
    text: str | None = Field(default=None, description="共用的文本输入")
    file_ids: list[str] = Field(default_factory=list, description="共用的已上传文件 ID 列表")
    groups: list[ComparisonGroupInput] = Field(
        min_length=2, max_length=2,
        description="两组模型配置",
    )
