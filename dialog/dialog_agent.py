#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话Agent模块
整合NLU和状态机，处理用户输入，生成回复
"""

from typing import Dict, Any, Optional
from loguru import logger

from .nlu import IntentRecognizer, EntityExtractor, Intent
from .state_machine import StateMachine, DialogState
from services import OrderService
from services.price_service import PriceService


class DialogAgent:
    """对话Agent主类"""

    def __init__(
        self,
        chat_id: str,
        user_id: str,
        order_service: Optional[OrderService] = None,
        price_service: Optional[PriceService] = None
    ):
        """
        初始化对话Agent
        Args:
            chat_id: 对话ID
            user_id: 用户ID
            order_service: 订单服务实例，None则创建新实例
            price_service: 价格服务实例，None则创建新实例
        """
        self.chat_id = chat_id
        self.user_id = user_id
        self.state_machine = StateMachine()
        self.order_service = order_service or OrderService()
        self.price_service = price_service or PriceService()

        # 对话上下文：存储当前对话的相关信息
        self.context: Dict[str, Any] = {
            "current_order_id": None,
            "price_params": {},  # 价格查询参数
            "booking_params": {},  # 预订参数
        }

        logger.info(f"DialogAgent initialized for chat_id: {chat_id}, user_id: {user_id}")

    def process_message(self, message: str) -> str:
        """
        处理用户消息，生成回复
        Args:
            message: 用户输入的消息
        Returns:
            生成的回复
        """
        logger.debug(f"Processing message: {message}")

        # 1. 进行NLU处理
        intent = IntentRecognizer.recognize(message)
        entities = EntityExtractor.extract(message)

        logger.debug(f"Intent: {intent}, Entities: {entities}")

        # 2. 根据意图和当前状态进行处理
        reply = self._handle_intent(intent, entities, message)

        logger.debug(f"Generated reply: {reply}")
        return reply

    def _handle_intent(
        self,
        intent: str,
        entities: Dict[str, Any],
        message: str
    ) -> str:
        """
        根据意图处理消息
        Args:
            intent: 用户意图
            entities: 提取的实体
            message: 原始消息
        Returns:
            生成的回复
        """
        current_state = self.state_machine.state

        try:
            if intent == Intent.PRICE_QUERY:
                return self._handle_price_query(entities)
            elif intent == Intent.CONFIRM:
                return self._handle_confirmation(entities)
            elif intent == Intent.CANCEL:
                return self._handle_cancellation()
            elif intent == Intent.PAYMENT:
                return self._handle_payment(entities)
            elif intent == Intent.REFUND:
                return self._handle_refund(entities)
            elif intent == Intent.BOOKING:
                return self._handle_booking_request(entities)
            else:  # UNKNOWN
                return self._handle_unknown_intent(message)
        except Exception as e:
            logger.exception(f"Error handling intent {intent}: {e}")
            return "抱歉，处理您的请求时出现了错误，请稍后再试。"

    def _handle_price_query(self, entities: Dict[str, Any]) -> str:
        """处理价格查询意图"""
        current_state = self.state_machine.state
        logger.debug(f"Handling price query in state: {current_state}")

        # 检查状态是否合法
        if current_state not in [DialogState.IDLE, DialogState.AWAITING_PRICE_PARAMS]:
            return "抱歉，当前不适合进行价格查询，请先完成当前操作或重新开始。"

        # 更新价格参数
        self._update_price_params(entities)

        # 检查是否有足够的参数进行查询
        required_params = ["hotel_id", "room_id", "check_in_date", "check_out_date"]
        missing_params = [p for p in required_params if p not in self.context["price_params"]]

        if missing_params:
            # 参数不足，进入等待参数状态
            if current_state != DialogState.AWAITING_PRICE_PARAMS:
                self.state_machine.transition_to(DialogState.AWAITING_PRICE_PARAMS)
            return f"请提供以下信息：{', '.join(missing_params)}"

        # 参数齐全，查询价格
        return self._query_and_show_price()

    def _update_price_params(self, entities: Dict[str, Any]) -> None:
        """更新价格查询参数"""
        # 从实体中提取参数
        for key in ["hotel_id", "room_id", "check_in_date", "check_out_date", "room_count"]:
            if key in entities:
                self.context["price_params"][key] = entities[key]

    def _query_and_show_price(self) -> str:
        """查询价格并展示给用户"""
        params = self.context["price_params"]

        # 调用价格服务查询
        price_record = self.price_service.query_price(
            hotel_id=params["hotel_id"],
            room_id=params["room_id"],
            check_in_date=params["check_in_date"],
            check_out_date=params["check_out_date"]
        )

        if price_record:
            # 价格查询成功，进入确认状态
            self.state_machine.transition_to(DialogState.AWAITING_CONFIRMATION)
            self.context["booking_params"] = params.copy()
            return (
                f"查询到价格：{price_record['price']} {price_record.get('currency', 'CNY')}\n"
                f"是否确认预订？"
            )
        else:
            # 这里应该调用酒店执行器获取实时价格
            return "暂时无法查询到该酒店的价格，请稍后再试或联系客服。"

    def _handle_confirmation(self, entities: Dict[str, Any]) -> str:
        """处理确认意图"""
        current_state = self.state_machine.state
        logger.debug(f"Handling confirmation in state: {current_state}")

        if current_state == DialogState.AWAITING_CONFIRMATION:
            # 创建订单
            return self._create_order()
        elif current_state == DialogState.COMPLETED:
            # 重置对话
            self.state_machine.reset()
            return "好的，对话已重置，有什么可以帮您的？"
        else:
            return "抱歉，我不太确定您要确认什么，请重新说明。"

    def _create_order(self) -> str:
        """创建订单"""
        booking_params = self.context["booking_params"]

        try:
            order_data = {
                "chat_id": self.chat_id,
                "user_id": self.user_id,
                "hotel_id": booking_params["hotel_id"],
                "room_id": booking_params["room_id"],
                "check_in_date": booking_params["check_in_date"],
                "check_out_date": booking_params["check_out_date"],
                "room_count": booking_params.get("room_count", 1),
            }

            order = self.order_service.create_order(order_data)
            self.context["current_order_id"] = order["order_id"]

            # 更新状态为等待付款
            self.state_machine.transition_to(DialogState.AWAITING_PAYMENT)

            return (
                f"订单已创建，订单号：{order['order_id']}\n"
                f"请在付款后告知我，以便继续处理预订。"
            )
        except Exception as e:
            logger.exception(f"Failed to create order: {e}")
            return "创建订单失败，请稍后再试或联系客服。"

    def _handle_payment(self, entities: Dict[str, Any]) -> str:
        """处理付款通知"""
        current_state = self.state_machine.state
        logger.debug(f"Handling payment in state: {current_state}")

        if current_state != DialogState.AWAITING_PAYMENT:
            return "抱歉，当前没有待付款的订单。"

        order_id = self.context.get("current_order_id")
        if not order_id:
            return "抱歉，找不到当前订单信息。"

        try:
            # 更新订单状态为已付款
            self.order_service.update_status(order_id, "PAID")
            self.state_machine.transition_to(DialogState.PROCESSING_BOOKING)

            # 这里应该调用酒店执行器进行实际预订
            # 简化处理，直接假设预订成功
            self.order_service.update_status(order_id, "BOOKED")
            self.state_machine.transition_to(DialogState.COMPLETED)

            return "已收到您的付款通知，预订成功！祝您入住愉快！"
        except Exception as e:
            logger.exception(f"Failed to process payment: {e}")
            return "处理付款通知失败，请稍后再试或联系客服。"

    def _handle_cancellation(self) -> str:
        """处理取消意图"""
        current_state = self.state_machine.state
        logger.debug(f"Handling cancellation in state: {current_state}")

        # 如果有进行中的订单，尝试取消
        order_id = self.context.get("current_order_id")
        if order_id and current_state in [
            DialogState.AWAITING_CONFIRMATION,
            DialogState.AWAITING_PAYMENT
        ]:
            try:
                self.order_service.update_status(order_id, "CANCELLED")
            except Exception as e:
                logger.warning(f"Failed to cancel order {order_id}: {e}")

        # 重置状态
        self.state_machine.reset()
        self.context["current_order_id"] = None
        self.context["price_params"] = {}
        self.context["booking_params"] = {}

        return "好的，已取消当前操作。有什么可以帮您的？"

    def _handle_refund(self, entities: Dict[str, Any]) -> str:
        """处理退款申请"""
        current_state = self.state_machine.state
        logger.debug(f"Handling refund in state: {current_state}")

        # 简化实现
        return "退款申请需要人工处理，请联系客服办理退款。"

    def _handle_booking_request(self, entities: Dict[str, Any]) -> str:
        """处理预订请求（直接预订而不先询价）"""
        logger.debug("Handling direct booking request")

        # 简化处理，先处理为价格查询
        self._update_price_params(entities)
        return self._handle_price_query(entities)

    def _handle_unknown_intent(self, message: str) -> str:
        """处理未知意图"""
        current_state = self.state_machine.state
        logger.debug(f"Handling unknown intent in state: {current_state}")

        # 根据当前状态给出不同的回复
        if current_state == DialogState.IDLE:
            return (
                "您好，我是酒店预订助手。\n"
                "您可以告诉我您想查询的酒店、房型和日期来获取价格。"
            )
        elif current_state == DialogState.AWAITING_PRICE_PARAMS:
            return "请继续提供查询价格所需的信息，或者说\"取消\"来重新开始。"
        elif current_state == DialogState.AWAITING_CONFIRMATION:
            return "请确认是否预订，或者说\"取消\"来重新开始。"
        elif current_state == DialogState.AWAITING_PAYMENT:
            return "请在付款后告诉我，或者说\"取消\"来取消订单。"
        elif current_state == DialogState.COMPLETED:
            return "您的订单已处理完成。如需其他帮助，请告诉我。"
        else:
            return "抱歉，我不太理解您的意思。请重新说明或说\"取消\"来重新开始。"
