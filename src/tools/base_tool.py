"""工具基类与通用类型 —— LangChain 集成"""

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """
    工具执行结果

    供内部 Agent（如 HotelPriceAgent）直接调用 execute() 时使用，
    提供结构化的成功/失败信息。
    LangChain 的 _arun 入口会调用 to_json() 将结果序列化为字符串返回。
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def success_result(cls, data: Any, metadata: Optional[Dict] = None) -> 'ToolResult':
        """创建成功结果"""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict] = None) -> 'ToolResult':
        """创建错误结果"""
        return cls(success=False, error=error, metadata=metadata)

    def to_json(self) -> str:
        """
        序列化为JSON字符串。
        成功时返回 data 的JSON，失败时返回包含 error 的JSON。
        供 LangChain BaseTool._arun 返回值使用。
        """
        if self.success:
            return json.dumps(self.data, ensure_ascii=False)
        return json.dumps({"error": self.error}, ensure_ascii=False)
