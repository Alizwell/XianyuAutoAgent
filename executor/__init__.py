#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行层模块
提供酒店API的抽象接口，封装具体的API调用细节
"""

from .hotel_executor import HotelExecutor, HotelError, HotelAPIError, HotelBookingError

__all__ = ["HotelExecutor", "HotelError", "HotelAPIError", "HotelBookingError"]
