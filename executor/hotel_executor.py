#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
酒店执行器模块
抽象酒店API调用接口，当前实现模拟模式
"""
import random
import uuid
import time
from typing import Optional, Dict, Any
from loguru import logger


class HotelError(Exception):
    """酒店相关错误基类"""
    pass


class HotelAPIError(HotelError):
    """酒店API调用错误"""
    pass


class HotelBookingError(HotelError):
    """酒店预订错误"""
    pass


class HotelExecutor:
    """
    酒店执行器类
    封装酒店API调用，当前为模拟实现
    """

    def __init__(self, api_key: str = None, base_url: str = None, mock: bool = True):
        """
        初始化酒店执行器
        Args:
            api_key: 酒店API密钥
            base_url: 酒店API基础URL
            mock: 是否启用模拟模式
        """
        self.api_key = api_key
        self.base_url = base_url
        self.mock = mock
        logger.info(f"HotelExecutor initialized with mock mode: {mock}")

    def query_price(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str) -> Dict[str, Any]:
        """
        查询酒店价格
        Args:
            hotel_id: 酒店ID
            room_id: 房型ID
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
        Returns:
            价格信息
        Raises:
            HotelAPIError: API调用失败时抛出
        """
        logger.info(f"Querying price for hotel {hotel_id}, room {room_id}, "
                    f"check-in {check_in_date}, check-out {check_out_date}")

        try:
            if self.mock:
                return self._mock_query_price(hotel_id, room_id, check_in_date, check_out_date)
            else:
                return self._real_query_price(hotel_id, room_id, check_in_date, check_out_date)
        except Exception as e:
            logger.error(f"Failed to query price: {e}")
            raise HotelAPIError(f"Price query failed: {str(e)}")

    def book_room(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str,
                  guest_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        预订房间
        Args:
            hotel_id: 酒店ID
            room_id: 房型ID
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
            guest_info: 客人信息
        Returns:
            预订结果
        Raises:
            HotelBookingError: 预订失败时抛出
            HotelAPIError: API调用失败时抛出
        """
        logger.info(f"Booking room for hotel {hotel_id}, room {room_id}, "
                    f"check-in {check_in_date}, check-out {check_out_date}")

        try:
            if self.mock:
                return self._mock_book_room(hotel_id, room_id, check_in_date, check_out_date, guest_info)
            else:
                return self._real_book_room(hotel_id, room_id, check_in_date, check_out_date, guest_info)
        except Exception as e:
            logger.error(f"Failed to book room: {e}")
            raise HotelBookingError(f"Booking failed: {str(e)}")

    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        取消预订
        Args:
            booking_id: 预订ID
        Returns:
            取消结果
        Raises:
            HotelAPIError: API调用失败时抛出
        """
        logger.info(f"Canceling booking: {booking_id}")

        try:
            if self.mock:
                return self._mock_cancel_booking(booking_id)
            else:
                return self._real_cancel_booking(booking_id)
        except Exception as e:
            logger.error(f"Failed to cancel booking: {e}")
            raise HotelAPIError(f"Cancel booking failed: {str(e)}")

    def _mock_query_price(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str) -> Dict[str, Any]:
        """
        模拟查询价格
        Returns:
            随机生成的价格信息（200-800元之间）
        """
        # 模拟网络延迟
        time.sleep(random.uniform(0.1, 0.5))

        # 随机生成价格（200-800元）
        price = random.randint(200, 800)

        result = {
            "success": True,
            "hotel_id": hotel_id,
            "room_id": room_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "price": price,
            "currency": "CNY",
            "original_price": price + random.randint(50, 200),
            "discount": random.randint(0, 20),
            "available": random.choice([True, True, True, False]),  # 偶尔返回无房
            "tax": int(price * 0.06)
        }

        logger.debug(f"Mock price query result: {result}")
        return result

    def _mock_book_room(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str,
                       guest_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        模拟预订房间
        Returns:
            预订成功结果
        """
        # 模拟网络延迟
        time.sleep(random.uniform(0.2, 0.8))

        # 随机失败概率（10%）
        if random.random() < 0.1:
            raise HotelBookingError("No rooms available")

        booking_id = f"BK{uuid.uuid4().hex[:12].upper()}"

        result = {
            "success": True,
            "booking_id": booking_id,
            "hotel_id": hotel_id,
            "room_id": room_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "guest_info": guest_info,
            "status": "CONFIRMED",
            "total_price": random.randint(200, 800),
            "currency": "CNY"
        }

        logger.debug(f"Mock booking result: {result}")
        return result

    def _mock_cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        模拟取消预订
        Returns:
            取消成功结果
        """
        # 模拟网络延迟
        time.sleep(random.uniform(0.1, 0.4))

        # 随机失败概率（5%）
        if random.random() < 0.05:
            raise HotelAPIError("Booking not found or cannot be canceled")

        result = {
            "success": True,
            "booking_id": booking_id,
            "status": "CANCELED",
            "refund_amount": random.randint(100, 500),
            "refund_currency": "CNY",
            "refund_method": "原路返回"
        }

        logger.debug(f"Mock cancel booking result: {result}")
        return result

    def _real_query_price(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str) -> Dict[str, Any]:
        """
        真实API查询价格（待实现）
        """
        raise NotImplementedError("Real API not implemented yet")

    def _real_book_room(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str,
                       guest_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        真实API预订房间（待实现）
        """
        raise NotImplementedError("Real API not implemented yet")

    def _real_cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        真实API取消预订（待实现）
        """
        raise NotImplementedError("Real API not implemented yet")
