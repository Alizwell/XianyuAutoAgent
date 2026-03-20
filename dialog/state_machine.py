#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对话状态机模块
管理对话状态流转
"""

from enum import Enum, auto
from typing import Set, Dict, List, Optional
from loguru import logger


class DialogState(Enum):
    """对话状态枚举"""
    IDLE = auto()                    # 空闲
    AWAITING_PRICE_PARAMS = auto()  # 等待价格查询参数
    AWAITING_CONFIRMATION = auto()  # 等待确认
    AWAITING_PAYMENT = auto()       # 等待付款
    PROCESSING_BOOKING = auto()     # 预订中
    COMPLETED = auto()               # 完成


class InvalidStateTransitionError(Exception):
    """无效的状态转换错误"""
    pass


class StateMachine:
    """对话状态机"""

    # 允许的状态转换规则
    _ALLOWED_TRANSITIONS: Dict[DialogState, Set[DialogState]] = {
        DialogState.IDLE: {
            DialogState.AWAITING_PRICE_PARAMS,
            DialogState.AWAITING_CONFIRMATION
        },
        DialogState.AWAITING_PRICE_PARAMS: {
            DialogState.AWAITING_CONFIRMATION,
            DialogState.IDLE
        },
        DialogState.AWAITING_CONFIRMATION: {
            DialogState.AWAITING_PAYMENT,
            DialogState.IDLE
        },
        DialogState.AWAITING_PAYMENT: {
            DialogState.PROCESSING_BOOKING,
            DialogState.IDLE
        },
        DialogState.PROCESSING_BOOKING: {
            DialogState.COMPLETED,
            DialogState.IDLE
        },
        DialogState.COMPLETED: {
            DialogState.IDLE
        }
    }

    def __init__(self, initial_state: DialogState = DialogState.IDLE):
        """
        初始化状态机
        Args:
            initial_state: 初始状态，默认为 IDLE
        """
        self._state = initial_state
        self._history: List[DialogState] = [initial_state]
        logger.debug(f"StateMachine initialized with state: {self._state}")

    @property
    def state(self) -> DialogState:
        """获取当前状态"""
        return self._state

    @property
    def history(self) -> List[DialogState]:
        """获取状态历史"""
        return self._history.copy()

    def can_transition_to(self, target_state: DialogState) -> bool:
        """
        检查是否可以转换到目标状态
        Args:
            target_state: 目标状态
        Returns:
            是否允许转换
        """
        allowed_states = self._ALLOWED_TRANSITIONS.get(self._state, set())
        return target_state in allowed_states

    def transition_to(self, target_state: DialogState) -> None:
        """
        转换到目标状态
        Args:
            target_state: 目标状态
        Raises:
            InvalidStateTransitionError: 当状态转换不允许时抛出
        """
        if not self.can_transition_to(target_state):
            raise InvalidStateTransitionError(
                f"Invalid state transition from {self._state} to {target_state}"
            )

        old_state = self._state
        self._state = target_state
        self._history.append(target_state)
        logger.debug(f"State transition: {old_state} -> {target_state}")

    def reset(self) -> None:
        """重置状态机到初始状态"""
        self._state = DialogState.IDLE
        self._history = [DialogState.IDLE]
        logger.debug("StateMachine reset to IDLE state")
