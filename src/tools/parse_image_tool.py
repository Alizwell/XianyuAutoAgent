"""解析酒店预订图片工具 —— LangChain 集成"""

import json
from typing import Optional, Any, Type

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from src.services import LLMExtractionService
from .base_tool import ToolResult


class ParseImageInput(BaseModel):
    """解析图片输入参数（LangChain args_schema）"""
    image_url: Optional[str] = Field(default=None, description="图片URL（与image_base64至少提供一个）")
    image_base64: Optional[str] = Field(default=None, description="图片Base64编码（与image_url至少提供一个）")


class ParseImageTool(BaseTool):
    """
    解析酒店预订图片工具

    同时支持：
    - LangChain 调用：ainvoke({"image_url": ..., ...}) → 返回JSON字符串
    - 内部直接调用：execute(image_url=..., ...) → 返回ToolResult
    """

    name: str = "parse_hotel_image"
    description: str = "解析酒店预订界面图片/截图，提取酒店名称、日期、房型信息"
    args_schema: Type[BaseModel] = ParseImageInput

    # 提取服务实例（Pydantic字段）
    extraction_service: Any = None

    def __init__(self, extraction_service: Optional[LLMExtractionService] = None, **kwargs):
        super().__init__(**kwargs)
        if self.extraction_service is None:
            self.extraction_service = LLMExtractionService()

    def _run(self, **kwargs) -> str:
        """同步入口（不支持，仅异步调用）"""
        raise NotImplementedError("该工具仅支持异步调用，请使用 ainvoke()")

    async def _arun(self, image_url: Optional[str] = None,
                    image_base64: Optional[str] = None) -> str:
        """LangChain 异步入口，返回JSON字符串"""
        result = await self.execute(
            image_url=image_url,
            image_base64=image_base64,
        )
        return result.to_json()

    async def execute(self, image_url: Optional[str] = None,
                      image_base64: Optional[str] = None, **kwargs) -> ToolResult:
        """
        直接调用入口，返回 ToolResult（供 HotelPriceAgent 等内部使用）

        Args:
            image_url: 图片URL（可选）
            image_base64: 图片Base64编码（可选）

        Returns:
            ToolResult: 解析结果
        """
        # 参数验证：至少提供一个图片来源
        if not image_url and not image_base64:
            return ToolResult.error_result("至少需要提供 image_url 或 image_base64 之一")

        try:
            result = await self.extraction_service.extract_from_image(
                image_url=image_url,
                image_base64=image_base64,
            )
            return ToolResult.success_result(data=result.__dict__)
        except Exception as e:
            return ToolResult.error_result(f"图片解析失败: {str(e)}")

    async def close(self):
        """关闭提取服务"""
        await self.extraction_service.close()
