"""华住酒店适配器"""

import httpx
import json
from typing import List, Dict, Any, Optional
from .base_adapter import HotelAdapter


class HuaZhuAPIError(Exception):
    """华住API错误"""
    pass


class HuaZhuAdapter(HotelAdapter):
    """华住酒店适配器"""

    BASE_URL = "https://hweb-hotel.huazhu.com"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def search_hotel(
        self,
        keyword: str,
        check_in_date: str,
        check_out_date: str,
        city_name: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜索酒店
        对应接口：GET /hotels/search/search
        """
        url = f"{self.BASE_URL}/hotels/search/search"

        params = {
            "keyword": keyword,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "source": "1",
            "cityType": "cities",
            "limit": limit
        }

        if city_name:
            params["cityName"] = city_name

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 解析华住响应格式
            hotels = self._parse_search_response(data)
            return hotels

        except httpx.HTTPError as e:
            raise HuaZhuAPIError(f"Search hotel failed: {str(e)}")

    async def query_room_info(
        self,
        hotel_id: str,
        check_in_date: str,
        check_out_date: str,
        room_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        查询房间信息
        对应接口：POST /v2/hotels/hotelDetail/getRoomInfo
        """
        url = f"{self.BASE_URL}/v2/hotels/hotelDetail/getRoomInfo"

        payload = {
            "hotelId": hotel_id,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "rcpType": "1",
            "roomCount": "1"
        }

        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()

            # 解析华住响应格式
            room_info = self._parse_room_info_response(data)

            # 如果指定了房型，进行过滤
            if room_type and room_info.get('room_list'):
                room_info['room_list'] = [
                    r for r in room_info['room_list']
                    if room_type.lower() in r.get('room_type_name', '').lower()
                ]

            return room_info

        except httpx.HTTPError as e:
            raise HuaZhuAPIError(f"Query room info failed: {str(e)}")

    def _parse_search_response(self, data: Dict) -> List[Dict[str, Any]]:
        """解析搜索响应"""
        hotels = []
        # 根据华住实际响应格式解析
        hotel_list = data.get('data', {}).get('list', [])
        for item in hotel_list:
            hotels.append({
                'hotel_id': str(item.get('hotelId', '')),
                'hotel_name': item.get('hotelName', ''),
                'brand_name': item.get('brandName', ''),
                'address': item.get('address', ''),
                'rating': item.get('score'),
                'price_start': item.get('price'),
                'distance': item.get('distanceDesc', '')
            })
        return hotels

    def _parse_room_info_response(self, data: Dict) -> Dict[str, Any]:
        """解析房间信息响应"""
        result = {
            'hotel_id': '',
            'hotel_name': '',
            'check_in_date': '',
            'check_out_date': '',
            'room_list': []
        }

        # 解析华住响应格式
        response_data = data.get('data', {})
        result['hotel_id'] = str(response_data.get('hotelId', ''))
        result['hotel_name'] = response_data.get('hotelName', '')
        result['check_in_date'] = response_data.get('checkInDate', '')
        result['check_out_date'] = response_data.get('checkOutDate', '')

        # 解析房间列表
        room_list = response_data.get('roomList', [])
        for item in room_list:
            result['room_list'].append({
                'room_type_name': item.get('roomTypeName', ''),
                'bed_type': item.get('bedType', ''),
                'price': float(item.get('price', 0)),
                'currency': item.get('currency', 'CNY'),
                'original_price': float(item['originalPrice']) if item.get('originalPrice') else None,
                'breakfast': item.get('breakfast', ''),
                'cancel_policy': item.get('cancelPolicy', ''),
                'room_count': int(item.get('roomCount', 0)),
                'area': item.get('area'),
                'floor': item.get('floor'),
            })

        return result

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
