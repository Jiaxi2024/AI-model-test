"""统计相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    """总览统计数据"""
    total_tests: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_tokens: int = 0
    models_used: int = 0
    avg_response_time_ms: float = 0.0


class UsageStatsItem(BaseModel):
    """用量统计项"""
    label: str
    test_count: int = 0
    token_input: int = 0
    token_output: int = 0
    avg_response_time_ms: float = 0.0


class UsageStats(BaseModel):
    """用量统计"""
    group_by: str
    data: list[UsageStatsItem] = Field(default_factory=list)
