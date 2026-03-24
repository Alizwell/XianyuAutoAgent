"""搜索酒店工具 —— LangChain 集成"""

import json
from typing import Optional, Any, Type

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from src.adapters import HuaZhuAdapter
from src.models import Hotel
from .base_tool import ToolResult


class SearchHotelInput(BaseModel):
    """搜索酒店输入参数（LangChain args_schema）"""
    keyword: str = Field(description="酒店名称关键词")
    check_in_date: str = Field(description="入住日期 (YYYY-MM-DD)")
    check_out_date: str = Field(description="离店日期 (YYYY-MM-DD)")
    city_name: Optional[str] = Field(default=None, description="城市名称（可选）")
    limit: int = Field(default=10, description="返回数量限制")


class SearchHotelTool(BaseTool):
    """
    搜索酒店工具

    同时支持：
    - LangChain 调用：ainvoke({"keyword": ..., ...}) → 返回JSON字符串
    - 内部直接调用：execute(keyword=..., ...) → 返回ToolResult
    """

    name: str = "search_hotel"
    description: str = "根据酒店名称关键词、入住日期、离店日期搜索酒店列表"
    args_schema: Type[BaseModel] = SearchHotelInput

    # 适配器实例（Pydantic字段）
    adapter: Any = None

    def __init__(self, adapter: Optional[HuaZhuAdapter] = None, **kwargs):
        super().__init__(**kwargs)
        if self.adapter is None:
            self.adapter = HuaZhuAdapter()

    def _run(self, **kwargs) -> str:
        """同步入口（不支持，仅异步调用）"""
        raise NotImplementedError("该工具仅支持异步调用，请使用 ainvoke()")

    async def _arun(self, keyword: str, check_in_date: str, check_out_date: str,
                    city_name: Optional[str] = None, limit: int = 10) -> str:
        """LangChain 异步入口，返回JSON字符串"""
        result = await self.execute(
            keyword=keyword,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            city_name=city_name,
            limit=limit,
        )
        return result.to_json()

    async def execute(self, keyword: str, check_in_date: str, check_out_date: str,
                      city_name: Optional[str] = None, limit: int = 10, **kwargs) -> ToolResult:
        """
        直接调用入口，返回 ToolResult（供 HotelPriceAgent 等内部使用）

        Args:
            keyword: 酒店名称关键词
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            city_name: 城市名称（可选）
            limit: 返回数量限制

        Returns:
            ToolResult: 搜索结果
        """
        # 参数验证
        if not all([keyword, check_in_date, check_out_date]):
            return ToolResult.error_result("缺少必需参数: keyword, check_in_date, check_out_date")

        try:
            # 调用适配器搜索酒店
            hotels_data = await self.adapter.search_hotel(
                keyword=keyword,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                city_name=city_name,
                limit=limit,
            )

            # 转换为Hotel对象
            hotels = [Hotel.from_dict(h) for h in hotels_data]

            return ToolResult.success_result(
                data=[h.to_dict() for h in hotels],
                metadata={
                    'total': len(hotels),
                    'keyword': keyword,
                    'check_in_date': check_in_date,
                    'check_out_date': check_out_date,
                }
            )

        except Exception as e:
            return ToolResult.error_result(
                f"搜索酒店失败: {str(e)}",
                metadata={'keyword': keyword}
            )

    async def close(self):
        """关闭适配器"""
        await self.adapter.close()
