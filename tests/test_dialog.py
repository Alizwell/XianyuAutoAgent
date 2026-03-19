#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话层测试
测试意图识别、实体提取、状态流转和完整对话流程
"""

import pytest
import tempfile
import os

from dialog.nlu import IntentRecognizer, EntityExtractor, Intent
from dialog.state_machine import StateMachine, DialogState, InvalidStateTransitionError
from dialog.dialog_agent import DialogAgent
from services import OrderService
from services.price_service import PriceService


class TestIntentRecognizer:
    """意图识别测试"""

    def test_recognize_price_query(self):
        """测试识别价格查询意图"""
        assert IntentRecognizer.recognize("这个酒店多少钱？") == Intent.PRICE_QUERY
        assert IntentRecognizer.recognize("查一下价格") == Intent.PRICE_QUERY
        assert IntentRecognizer.recognize("询价") == Intent.PRICE_QUERY

    def test_recognize_booking(self):
        """测试识别预订意图"""
        assert IntentRecognizer.recognize("我要预订") == Intent.BOOKING
        assert IntentRecognizer.recognize("订一个房间") == Intent.BOOKING
        assert IntentRecognizer.recognize("想订房") == Intent.BOOKING

    def test_recognize_confirm(self):
        """测试识别确认意图"""
        assert IntentRecognizer.recognize("确认") == Intent.CONFIRM
        assert IntentRecognizer.recognize("是的") == Intent.CONFIRM
        assert IntentRecognizer.recognize("好的") == Intent.CONFIRM

    def test_recognize_cancel(self):
        """测试识别取消意图"""
        assert IntentRecognizer.recognize("取消") == Intent.CANCEL
        assert IntentRecognizer.recognize("不要了") == Intent.CANCEL
        assert IntentRecognizer.recognize("取消订单") == Intent.CANCEL

    def test_recognize_payment(self):
        """测试识别付款通知意图"""
        assert IntentRecognizer.recognize("已付款") == Intent.PAYMENT
        assert IntentRecognizer.recognize("付了钱了") == Intent.PAYMENT
        assert IntentRecognizer.recognize("转账了") == Intent.PAYMENT

    def test_recognize_refund(self):
        """测试识别退款申请意图"""
        assert IntentRecognizer.recognize("退款") == Intent.REFUND
        assert IntentRecognizer.recognize("申请退款") == Intent.REFUND

    def test_recognize_unknown(self):
        """测试识别未知意图"""
        assert IntentRecognizer.recognize("你好") == Intent.UNKNOWN
        assert IntentRecognizer.recognize("天气怎么样") == Intent.UNKNOWN


class TestEntityExtractor:
    """实体提取测试"""

    def test_extract_room_count(self):
        """测试提取房间数量"""
        entities = EntityExtractor.extract("我要2间房")
        assert entities.get("room_count") == 2

        entities = EntityExtractor.extract("3个房间")
        assert entities.get("room_count") == 3

    def test_extract_room_type(self):
        """测试提取房型"""
        entities = EntityExtractor.extract("我要大床房")
        assert entities.get("room_type") == "大床房"

        entities = EntityExtractor.extract("双床房")
        assert entities.get("room_type") == "双床房"

    def test_extract_hotel_name(self):
        """测试提取酒店名称"""
        entities = EntityExtractor.extract("希尔顿酒店")
        assert "hotel_name" in entities


class TestStateMachine:
    """状态机测试"""

    def test_initial_state(self):
        """测试初始状态"""
        sm = StateMachine()
        assert sm.state == DialogState.IDLE

    def test_valid_transitions(self):
        """测试有效状态转换"""
        sm = StateMachine()

        # IDLE -> AWAITING_PRICE_PARAMS
        assert sm.can_transition_to(DialogState.AWAITING_PRICE_PARAMS)
        sm.transition_to(DialogState.AWAITING_PRICE_PARAMS)
        assert sm.state == DialogState.AWAITING_PRICE_PARAMS

        # AWAITING_PRICE_PARAMS -> AWAITING_CONFIRMATION
        assert sm.can_transition_to(DialogState.AWAITING_CONFIRMATION)
        sm.transition_to(DialogState.AWAITING_CONFIRMATION)
        assert sm.state == DialogState.AWAITING_CONFIRMATION

        # AWAITING_CONFIRMATION -> AWAITING_PAYMENT
        assert sm.can_transition_to(DialogState.AWAITING_PAYMENT)
        sm.transition_to(DialogState.AWAITING_PAYMENT)
        assert sm.state == DialogState.AWAITING_PAYMENT

    def test_invalid_transitions(self):
        """测试无效状态转换"""
        sm = StateMachine()

        # 不能从 IDLE 直接到 AWAITING_PAYMENT
        assert not sm.can_transition_to(DialogState.AWAITING_PAYMENT)
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_to(DialogState.AWAITING_PAYMENT)

        # 不能从 IDLE 直接到 PROCESSING_BOOKING
        assert not sm.can_transition_to(DialogState.PROCESSING_BOOKING)
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_to(DialogState.PROCESSING_BOOKING)

        # 不能从 IDLE 直接到 COMPLETED
        assert not sm.can_transition_to(DialogState.COMPLETED)
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_to(DialogState.COMPLETED)

    def test_state_history(self):
        """测试状态历史记录"""
        sm = StateMachine()
        sm.transition_to(DialogState.AWAITING_PRICE_PARAMS)
        sm.transition_to(DialogState.AWAITING_CONFIRMATION)

        history = sm.history
        assert len(history) == 3
        assert history[0] == DialogState.IDLE
        assert history[1] == DialogState.AWAITING_PRICE_PARAMS
        assert history[2] == DialogState.AWAITING_CONFIRMATION

    def test_reset(self):
        """测试状态重置"""
        sm = StateMachine()
        sm.transition_to(DialogState.AWAITING_PRICE_PARAMS)
        sm.reset()
        assert sm.state == DialogState.IDLE
        assert len(sm.history) == 1


class TestDialogAgent:
    """对话Agent完整测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        yield db_path
        # 清理
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)

    @pytest.fixture
    def agent(self, temp_db):
        """创建测试用的DialogAgent"""
        order_service = OrderService(temp_db)
        price_service = PriceService(temp_db)
        return DialogAgent(
            chat_id="test_chat_123",
            user_id="test_user_456",
            order_service=order_service,
            price_service=price_service
        )

    def test_initial_message(self, agent):
        """测试初始消息"""
        reply = agent.process_message("你好")
        assert "酒店预订助手" in reply

    def test_price_query_insufficient_params(self, agent):
        """测试价格查询参数不足"""
        reply = agent.process_message("查询价格")
        assert agent.state_machine.state == DialogState.AWAITING_PRICE_PARAMS
        assert "请提供以下信息" in reply

    def test_cancel(self, agent):
        """测试取消操作"""
        agent.process_message("查询价格")
        reply = agent.process_message("取消")
        assert agent.state_machine.state == DialogState.IDLE
        assert "已取消" in reply

    def test_complete_dialog_flow(self, agent):
        """测试完整对话流程（简化）"""
        # 这个测试需要模拟完整的价格查询和预订流程
        # 因为需要数据库中存在价格记录，这里只测试基本的对话流程

        # 初始状态
        assert agent.state_machine.state == DialogState.IDLE

        # 开始价格查询
        reply = agent.process_message("查询价格")
        assert agent.state_machine.state == DialogState.AWAITING_PRICE_PARAMS

        # 取消
        reply = agent.process_message("取消")
        assert agent.state_machine.state == DialogState.IDLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
