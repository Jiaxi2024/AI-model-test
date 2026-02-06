"""通用 Pydantic Schema：分页、错误、状态枚举"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel):
    """分页响应基类"""
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(description="错误详情")
    code: str | None = Field(default=None, description="错误代码")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(description="消息内容")
