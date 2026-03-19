#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自然语言理解模块（NLU）
提供意图识别和实体提取功能
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime


class Intent:
    """意图类型"""
    PRICE_QUERY = "PRICE_QUERY"    # 价格查询
    BOOKING = "BOOKING"            # 预订请求
    CONFIRM = "CONFIRM"            # 确认
    CANCEL = "CANCEL"              # 取消
    PAYMENT = "PAYMENT"            # 付款通知
    REFUND = "REFUND"              # 退款申请
    UNKNOWN = "UNKNOWN"            # 未知意图


class IntentRecognizer:
    """意图识别器"""

    # 意图关键词映射
    _INTENT_KEYWORDS = {
        Intent.PRICE_QUERY: ["价格", "多少钱", "询价", "查价", "报价"],
        Intent.BOOKING: ["预订", "订房", "开房", "我要住", "想订", "订"],
        Intent.CONFIRM: ["确认", "是的", "对的", "没问题", "好的"],
        Intent.CANCEL: ["取消", "不要了", "算了", "取消订单"],
        Intent.PAYMENT: ["已付款", "付了", "付款了", "转账了"],
        Intent.REFUND: ["退款", "退钱", "申请退款"],
    }

    @classmethod
    def recognize(cls, text: str) -> str:
        """
        识别用户意图
        Args:
            text: 用户输入文本
        Returns:
            识别出的意图类型
        """
        text = text.strip().lower()

        # 按优先级顺序检查意图（从高到低）
        intent_priority = [
            Intent.CANCEL,
            Intent.REFUND,
            Intent.PAYMENT,
            Intent.CONFIRM,
            Intent.PRICE_QUERY,
            Intent.BOOKING,
        ]

        for intent in intent_priority:
            keywords = cls._INTENT_KEYWORDS.get(intent, [])
            for keyword in keywords:
                if keyword in text:
                    logger.debug(f"Recognized intent: {intent} from text: {text}")
                    return intent

        logger.debug(f"Unknown intent for text: {text}")
        return Intent.UNKNOWN


class EntityExtractor:
    """实体提取器"""

    # 酒店名称到ID的映射（测试用）
    _HOTEL_MAPPING = {
        "希尔顿": "hotel_hilton",
        "北京希尔顿": "hotel_bj_hilton",
        "上海希尔顿": "hotel_sh_hilton",
    }

    # 房型到ID的映射（测试用）
    _ROOM_MAPPING = {
        "大床房": "room_king",
        "双床房": "room_twin",
        "标间": "room_standard",
        "套房": "room_suite",
        "单人间": "room_single",
    }

    @classmethod
    def extract(cls, text: str) -> Dict[str, Any]:
        """
        从用户输入中提取实体
        Args:
            text: 用户输入文本
        Returns:
            包含提取出的实体的字典
        """
        entities = {}

        # 提取酒店相关实体
        entities.update(cls._extract_hotel_entities(text))

        # 提取房型相关实体
        entities.update(cls._extract_room_entities(text))

        # 提取日期实体
        entities.update(cls._extract_date_entities(text))

        # 提取房间数量
        entities.update(cls._extract_room_count(text))

        # 提取订单号
        entities.update(cls._extract_order_id(text))

        logger.debug(f"Extracted entities: {entities} from text: {text}")
        return entities

    @classmethod
    def _extract_hotel_entities(cls, text: str) -> Dict[str, Any]:
        """提取酒店名称/ID"""
        entities = {}

        # 查找酒店名称并映射到ID
        for hotel_name, hotel_id in cls._HOTEL_MAPPING.items():
            if hotel_name in text:
                entities["hotel_name"] = hotel_name
                entities["hotel_id"] = hotel_id
                break

        # 如果没有找到，尝试使用通用模式
        if "hotel_id" not in entities and "酒店" in text:
            entities["hotel_name"] = text
            # 为测试目的，使用默认酒店ID
            entities["hotel_id"] = "hotel_default"

        return entities

    @classmethod
    def _extract_room_entities(cls, text: str) -> Dict[str, Any]:
        """提取房型/ID"""
        entities = {}

        # 查找房型并映射到ID
        for room_type, room_id in cls._ROOM_MAPPING.items():
            if room_type in text:
                entities["room_type"] = room_type
                entities["room_id"] = room_id
                break

        # 如果没有找到，使用默认房型ID（用于测试）
        if "room_id" not in entities:
            entities["room_id"] = "room_default"

        return entities

    @classmethod
    def _extract_date_entities(cls, text: str) -> Dict[str, Any]:
        """提取日期实体"""
        entities = {}
        import re
        from datetime import datetime, timedelta

        # 匹配 YYYY-MM-DD 格式的日期
        date_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        dates = re.findall(date_pattern, text)

        if dates:
            if len(dates) >= 1:
                entities["check_in_date"] = f"{dates[0][0]}-{dates[0][1].zfill(2)}-{dates[0][2].zfill(2)}"
            if len(dates) >= 2:
                entities["check_out_date"] = f"{dates[1][0]}-{dates[1][1].zfill(2)}-{dates[1][2].zfill(2)}"
        else:
            # 尝试匹配 "X月Y日" 格式
            month_day_pattern = r'(\d{1,2})月(\d{1,2})日'
            month_days = re.findall(month_day_pattern, text)

            if month_days:
                current_year = datetime.now().year
                if len(month_days) >= 1:
                    entities["check_in_date"] = f"{current_year}-{month_days[0][0].zfill(2)}-{month_days[0][1].zfill(2)}"
                if len(month_days) >= 2:
                    entities["check_out_date"] = f"{current_year}-{month_days[1][0].zfill(2)}-{month_days[1][1].zfill(2)}"

        # 处理 "住X晚" 或 "X天" 的情况
        if "check_in_date" in entities and "check_out_date" not in entities:
            nights_match = re.search(r'住[：:]\s*(\d+)[晚晚]|(\d+)[晚晚]', text)
            if nights_match:
                nights = int(nights_match.group(1) or nights_match.group(2))
                try:
                    check_in = datetime.strptime(entities["check_in_date"], "%Y-%m-%d")
                    check_out = check_in + timedelta(days=nights)
                    entities["check_out_date"] = check_out.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        return entities

    @classmethod
    def _extract_room_count(cls, text: str) -> Dict[str, Any]:
        """提取房间数量"""
        entities = {}
        import re

        # 查找数字+房间/间的模式
        match = re.search(r'(\d+)(?:间|个|间房|房间)', text)
        if match:
            entities["room_count"] = int(match.group(1))
        else:
            # 默认1间房
            entities["room_count"] = 1

        return entities

    @classmethod
    def _extract_order_id(cls, text: str) -> Dict[str, Any]:
        """提取订单号"""
        entities = {}
        import re

        # 匹配订单号模式 ORDYYYYMMDDHHMMSSXXXXXXXX
        match = re.search(r'(ORD[0-9A-Z]{20})', text)
        if match:
            entities["order_id"] = match.group(1)

        return entities
