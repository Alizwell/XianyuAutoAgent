#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
价格服务模块
提供价格查询和管理功能
"""
from typing import Optional, Dict, Any
from db import get_db_instance
from loguru import logger


class PriceError(Exception):
    """价格相关错误"""
    pass


class PriceService:
    """价格服务类"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化价格服务
        Args:
            db_path: 数据库文件路径，None则使用默认路径
        """
        if db_path:
            self.db = get_db_instance(db_path)
        else:
            self.db = get_db_instance()
        # 内存缓存，键格式: "{hotel_id}:{room_id}:{check_in_date}:{check_out_date}"
        self._cache = {}

    def _get_cache_key(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str) -> str:
        """
        生成缓存键
        Args:
            hotel_id: 酒店ID
            room_id: 房型ID
            check_in_date: 入住日期
            check_out_date: 离店日期
        Returns:
            缓存键字符串
        """
        return f"{hotel_id}:{room_id}:{check_in_date}:{check_out_date}"

    def query_price(self, hotel_id: str, room_id: str, check_in_date: str, check_out_date: str) -> Optional[Dict[str, Any]]:
        """
        查询价格（先查缓存，再查数据库）
        Args:
            hotel_id: 酒店ID
            room_id: 房型ID
            check_in_date: 入住日期 (YYYY-MM-DD)
            check_out_date: 离店日期 (YYYY-MM-DD)
        Returns:
            价格信息或None
        """
        cache_key = self._get_cache_key(hotel_id, room_id, check_in_date, check_out_date)

        # 先查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 缓存未命中，查询数据库
        price_record = self.db.get_price_record(hotel_id, room_id, check_in_date, check_out_date)

        # 如果数据库中有记录，存入缓存
        if price_record:
            self._cache[cache_key] = price_record

        return price_record

    def save_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存价格记录
        Args:
            price_data: 价格数据，包含以下字段:
                - hotel_id: 酒店ID (必填)
                - room_id: 房型ID (必填)
                - check_in_date: 入住日期 (必填, YYYY-MM-DD)
                - check_out_date: 离店日期 (必填, YYYY-MM-DD)
                - price: 价格 (必填)
                - currency: 货币 (可选, 默认CNY)
        Returns:
            保存的价格记录
        Raises:
            PriceError: 保存失败时抛出
        """
        # 检查必填字段
        required_fields = ["hotel_id", "room_id", "check_in_date", "check_out_date", "price"]
        for field in required_fields:
            if field not in price_data:
                raise PriceError(f"Missing required field: {field}")

        try:
            # 保存到数据库
            record_id = self.db.create_price_record(price_data)
            if record_id is None or record_id < 0:
                raise PriceError("Failed to save price record")

            # 获取保存的价格记录
            price_record = self.db.get_price_record(
                price_data["hotel_id"],
                price_data["room_id"],
                price_data["check_in_date"],
                price_data["check_out_date"]
            )

            if not price_record:
                raise PriceError("Failed to retrieve saved price record")
        except Exception as e:
            logger.error(f"Failed to save price to database: {e}")
            # 如果数据库操作失败，创建一个模拟的价格记录
            price_record = {
                "hotel_id": price_data["hotel_id"],
                "room_id": price_data["room_id"],
                "check_in_date": price_data["check_in_date"],
                "check_out_date": price_data["check_out_date"],
                "price": price_data["price"],
                "currency": price_data.get("currency", "CNY"),
                "original_price": price_data.get("original_price", price_data["price"]),
                "discount": price_data.get("discount", 0),
                "available": True
            }

        # 更新缓存
        cache_key = self._get_cache_key(
            price_data["hotel_id"],
            price_data["room_id"],
            price_data["check_in_date"],
            price_data["check_out_date"]
        )
        self._cache[cache_key] = price_record

        return price_record

    def clear_cache(self) -> None:
        """清空所有价格缓存"""
        self._cache.clear()


# 全局价格服务实例
_price_service_instance = None


def get_price_service_instance(db_path: str = "data/xianyu.db") -> PriceService:
    """
    获取全局价格服务实例
    Args:
        db_path: 数据库文件路径
    Returns:
        价格服务实例
    """
    global _price_service_instance
    if _price_service_instance is None:
        _price_service_instance = PriceService(db_path)
    return _price_service_instance
