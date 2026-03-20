"""工具基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """工具执行结果"""
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


class BaseTool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 执行参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    def validate_params(self, required_params: list, provided_params: dict, require_at_least_one: bool = False) -> Optional[str]:
        """
        验证参数

        Args:
            required_params: 必需参数列表
            provided_params: 提供的参数
            require_at_least_one: 是否至少需要提供一个参数（而不是全部）

        Returns:
            错误信息，如果验证通过返回None
        """
        if require_at_least_one:
            # 检查是否至少提供了一个参数
            has_valid_param = any(
                provided_params.get(p) is not None for p in required_params
            )
            if not has_valid_param:
                return f"At least one of the following parameters is required: {', '.join(required_params)}"
        else:
            # 检查所有参数是否都提供了
            missing = [p for p in required_params if p not in provided_params or provided_params[p] is None]
            if missing:
                return f"Missing required parameters: {', '.join(missing)}"
        return None
