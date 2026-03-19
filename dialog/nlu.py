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

        # 提取酒店相关实体（简化实现）
        entities.update(cls._extract_hotel_entities(text))

        # 提取房型相关实体
        entities.update(cls._extract_room_entities(text))

        # 提取日期实体
        entities.update(cls._extract_date_entities(text))

        # 提取房间数量
        entities.update(cls._extract_room_count(text))

        logger.debug(f"Extracted entities: {entities} from text: {text}")
        return entities

    @classmethod
    def _extract_hotel_entities(cls, text: str) -> Dict[str, Any]:
        """提取酒店名称/ID"""
        entities = {}

        # 简化的酒店名称提取（实际应该使用知识库或正则表达式）
        # 这里假设文本中包含"酒店"关键词的部分是酒店名称
        if "酒店" in text:
            # 简单的提取逻辑，实际应用中需要更复杂的算法
            entities["hotel_name"] = text

        # 这里可以添加酒店ID提取的逻辑

        return entities

    @classmethod
    def _extract_room_entities(cls, text: str) -> Dict[str, Any]:
        """提取房型/ID"""
        entities = {}

        # 常见房型关键词
        room_types = ["大床房", "双床房", "标间", "套房", "单人间"]
        for room_type in room_types:
            if room_type in text:
                entities["room_type"] = room_type
                break

        # 这里可以添加房型ID提取的逻辑

        return entities

    @classmethod
    def _extract_date_entities(cls, text: str) -> Dict[str, Any]:
        """提取日期实体"""
        entities = {}

        # 简单的日期提取逻辑（实际应用中需要更复杂的日期解析库）
        # 这里只处理简单的日期格式，如"2023-12-25"或"12月25日"

        # 尝试提取入住和离店日期（简化实现）
        if "入住" in text or "离店" in text:
            # 这里可以使用日期解析库如 dateutil.parser 或 jieba
            # 暂时使用简单的字符串匹配
            pass

        return entities

    @classmethod
    def _extract_room_count(cls, text: str) -> Dict[str, Any]:
        """提取房间数量"""
        entities = {}

        # 查找数字+房间/间的模式
        import re
        match = re.search(r"(\d+)(?:间|个|间房)", text)
        if match:
            entities["room_count"] = int(match.group(1))

        return entities
