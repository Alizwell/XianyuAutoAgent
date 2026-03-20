"""酒店适配器基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class HotelAdapter(ABC):
    """酒店适配器基类"""

    @abstractmethod
    async def search_hotel(
        self,
        keyword: str,
        check_in_date: str,
        check_out_date: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜索酒店

        Args:
            keyword: 酒店名称关键词
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            **kwargs: 其他可选参数

        Returns:
            酒店列表
        """
        pass

    @abstractmethod
    async def query_room_info(
        self,
        hotel_id: str,
        check_in_date: str,
        check_out_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        查询房间信息

        Args:
            hotel_id: 酒店ID
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            **kwargs: 其他可选参数

        Returns:
            房间信息
        """
        pass
