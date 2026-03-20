"""酒店价格查询Agent模块"""

from .agent import HotelPriceAgent, StateManager
from .models import QueryState, QueryStep, Hotel, RoomPrice
from .tools import SearchHotelTool, QueryPriceTool, ParseImageTool
from .adapters import HuaZhuAdapter, HuaZhuAPIError
from .services import ImageRecognitionService

__version__ = "1.0.0"
__author__ = "Xianyu Hotel Agent"

__all__ = [
    'HotelPriceAgent',
    'StateManager',
    'QueryState',
    'QueryStep',
    'Hotel',
    'RoomPrice',
    'SearchHotelTool',
    'QueryPriceTool',
    'ParseImageTool',
    'HuaZhuAdapter',
    'HuaZhuAPIError',
    'ImageRecognitionService',
]
