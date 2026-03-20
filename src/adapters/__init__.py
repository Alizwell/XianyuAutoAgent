"""适配器模块"""

from .base_adapter import HotelAdapter
from .huazhu_adapter import HuaZhuAdapter, HuaZhuAPIError

__all__ = [
    'HotelAdapter',
    'HuaZhuAdapter',
    'HuaZhuAPIError',
]
