"""查询房间价格工具 —— LangChain 集成"""

import json
from typing import Optional, Any, Type

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from src.adapters import HuaZhuAdapter
from src.models import RoomPrice
from .base_tool import ToolResult


class QueryPriceInput(BaseModel):
    """查询价格输入参数（LangChain args_schema）"""
    hotel_id: str = Field(description="酒店ID")
    check_in_date: str = Field(description="入住日期 (YYYY-MM-DD)")
    check_out_date: str = Field(description="离店日期 (YYYY-MM-DD)")
    room_type: Optional[str] = Field(default=None, description="房型筛选（可选）")


class QueryPriceTool(BaseTool):
    """
    查询房间价格工具

    同时支持：
    - LangChain 调用：ainvoke({"hotel_id": ..., ...}) → 返回JSON字符串
    - 内部直接调用：execute(hotel_id=..., ...) → 返回ToolResult
    """

    name: str = "query_room_price"
    description: str = "根据酒店ID、入住日期、离店日期查询房间价格列表"
    args_schema: Type[BaseModel] = QueryPriceInput

    # 适配器实例（Pydantic字段）
    adapter: Any = None

    def __init__(self, adapter: Optional[HuaZhuAdapter] = None, **kwargs):
        super().__init__(**kwargs)
        if self.adapter is None:
            self.adapter = HuaZhuAdapter()

    def _run(self, **kwargs) -> str:
        """同步入口（不支持，仅异步调用）"""
        raise NotImplementedError("该工具仅支持异步调用，请使用 ainvoke()")

    async def _arun(self, hotel_id: str, check_in_date: str, check_out_date: str,
                    room_type: Optional[str] = None) -> str:
        """LangChain 异步入口，返回JSON字符串"""
        result = await self.execute(
            hotel_id=hotel_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            room_type=room_type,
        )
        return result.to_json()

    async def execute(self, hotel_id: str, check_in_date: str, check_out_date: str,
                      room_type: Optional[str] = None, **kwargs) -> ToolResult:
        """
        直接调用入口，返回 ToolResult（供 HotelPriceAgent 等内部使用）

        Args:
            hotel_id: 酒店ID
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            room_type: 房型筛选（可选）

        Returns:
            ToolResult: 查询结果
        """
        # 参数验证
        if not all([hotel_id, check_in_date, check_out_date]):
            return ToolResult.error_result("缺少必需参数: hotel_id, check_in_date, check_out_date")

        try:
            # 调用适配器查询房间信息
            room_info = await self.adapter.query_room_info(
                hotel_id=hotel_id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                room_type=room_type,
            )

            # 转换为RoomPrice对象
            room_list = room_info.get('room_list', [])
            rooms = []
            for room_data in room_list:
                try:
                    room = RoomPrice.from_dict(room_data)
                    rooms.append(room)
                except Exception:
                    # 跳过解析失败的房间
                    continue

            return ToolResult.success_result(
                data={
                    'hotel_id': room_info.get('hotel_id'),
                    'hotel_name': room_info.get('hotel_name'),
                    'check_in_date': room_info.get('check_in_date'),
                    'check_out_date': room_info.get('check_out_date'),
                    'rooms': [r.to_dict() for r in rooms],
                },
                metadata={
                    'total_rooms': len(rooms),
                    'hotel_id': hotel_id,
                    'check_in_date': check_in_date,
                    'check_out_date': check_out_date,
                    'room_type_filter': room_type,
                }
            )

        except Exception as e:
            return ToolResult.error_result(
                f"查询房间价格失败: {str(e)}",
                metadata={'hotel_id': hotel_id}
            )

    async def close(self):
        """关闭适配器"""
        await self.adapter.close()
