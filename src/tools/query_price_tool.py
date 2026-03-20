"""查询房间价格工具"""

from typing import Optional
from src.adapters import HuaZhuAdapter
from src.models import RoomPrice
from .base_tool import BaseTool, ToolResult


class QueryPriceTool(BaseTool):
    """查询房间价格工具"""

    name = "query_room_price"
    description = "根据酒店ID、日期查询房间价格列表"

    def __init__(self, adapter: Optional[HuaZhuAdapter] = None):
        self.adapter = adapter or HuaZhuAdapter()

    async def execute(
        self,
        hotel_id: str,
        check_in_date: str,
        check_out_date: str,
        room_type: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        执行房间价格查询

        Args:
            hotel_id: 酒店ID
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            room_type: 房型筛选（可选）

        Returns:
            ToolResult: 查询结果
        """
        # 验证必需参数
        error = self.validate_params(
            ['hotel_id', 'check_in_date', 'check_out_date'],
            {
                'hotel_id': hotel_id,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date
            }
        )
        if error:
            return ToolResult.error_result(error)

        try:
            # 调用适配器查询房间信息
            room_info = await self.adapter.query_room_info(
                hotel_id=hotel_id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                room_type=room_type
            )

            # 转换为RoomPrice对象
            room_list = room_info.get('room_list', [])
            rooms = []
            for room_data in room_list:
                try:
                    room = RoomPrice.from_dict(room_data)
                    rooms.append(room)
                except Exception as e:
                    # 跳过解析失败的房间
                    continue

            return ToolResult.success_result(
                data={
                    'hotel_id': room_info.get('hotel_id'),
                    'hotel_name': room_info.get('hotel_name'),
                    'check_in_date': room_info.get('check_in_date'),
                    'check_out_date': room_info.get('check_out_date'),
                    'rooms': [r.to_dict() for r in rooms]
                },
                metadata={
                    'total_rooms': len(rooms),
                    'hotel_id': hotel_id,
                    'check_in_date': check_in_date,
                    'check_out_date': check_out_date,
                    'room_type_filter': room_type
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
