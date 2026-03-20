"""搜索酒店工具"""

from typing import Optional
from src.adapters import HuaZhuAdapter
from src.models import Hotel
from .base_tool import BaseTool, ToolResult


class SearchHotelTool(BaseTool):
    """搜索酒店工具"""

    name = "search_hotel"
    description = "根据酒店名称、城市、日期搜索酒店列表"

    def __init__(self, adapter: Optional[HuaZhuAdapter] = None):
        self.adapter = adapter or HuaZhuAdapter()

    async def execute(
        self,
        keyword: str,
        check_in_date: str,
        check_out_date: str,
        city_name: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> ToolResult:
        """
        执行酒店搜索

        Args:
            keyword: 酒店名称关键词
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            city_name: 城市名称（可选）
            limit: 返回数量限制

        Returns:
            ToolResult: 搜索结果
        """
        # 验证必需参数
        error = self.validate_params(
            ['keyword', 'check_in_date', 'check_out_date'],
            {
                'keyword': keyword,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date
            }
        )
        if error:
            return ToolResult.error_result(error)

        try:
            # 调用适配器搜索酒店
            hotels_data = await self.adapter.search_hotel(
                keyword=keyword,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                city_name=city_name,
                limit=limit
            )

            # 转换为Hotel对象
            hotels = [Hotel.from_dict(h) for h in hotels_data]

            return ToolResult.success_result(
                data=[h.to_dict() for h in hotels],
                metadata={
                    'total': len(hotels),
                    'keyword': keyword,
                    'check_in_date': check_in_date,
                    'check_out_date': check_out_date
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
