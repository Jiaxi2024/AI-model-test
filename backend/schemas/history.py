"""历史记录相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class HistoryFilterParams(BaseModel):
    """历史记录筛选参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    model_id: str | None = Field(default=None, description="按模型筛选")
    keyword: str | None = Field(default=None, description="关键字搜索")
    start_date: str | None = Field(default=None, description="开始日期")
    end_date: str | None = Field(default=None, description="结束日期")
    status: str | None = Field(default=None, description="状态筛选")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    record_ids: list[str] = Field(default_factory=list, description="要删除的记录 ID 列表")
    delete_all: bool = Field(default=False, description="是否删除全部记录")
