"""Parse hotel image tool - uses LLM extraction service"""

from typing import Optional, Dict, Any
from src.tools.base_tool import BaseTool, ToolResult
from src.services import LLMExtractionService, ExtractedInfo


class ParseImageTool(BaseTool):
    """解析酒店预订图片工具"""

    name = "parse_hotel_image"
    description = "解析酒店预订界面图片，提取酒店名称、日期、房型信息"

    def __init__(self, extraction_service: Optional[LLMExtractionService] = None):
        self.extraction_service = extraction_service or LLMExtractionService()

    async def execute(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_type: str = "screenshot",
        **kwargs
    ) -> ToolResult:
        try:
            result = await self.extraction_service.extract_from_image(
                image_url=image_url,
                image_base64=image_base64
            )
            # image_type is kept for backward compatibility but not used in new service
            return ToolResult.success_result(data=result.__dict__)
        except Exception as e:
            return ToolResult.error_result(f"图片解析失败: {str(e)}")

    async def close(self):
        await self.extraction_service.close()
