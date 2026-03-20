"""解析酒店图片工具"""

import base64
from typing import Optional, Dict, Any
from src.services.image_recognition_service import ImageRecognitionService
from .base_tool import BaseTool, ToolResult


class ParseImageTool(BaseTool):
    """解析酒店预订图片工具"""

    name = "parse_hotel_image"
    description = "解析酒店预订界面图片，提取酒店名称、日期、房型信息"

    def __init__(self, recognition_service: Optional[ImageRecognitionService] = None):
        self.recognition_service = recognition_service or ImageRecognitionService()

    async def execute(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_type: str = "screenshot",
        **kwargs
    ) -> ToolResult:
        """
        执行图片解析

        Args:
            image_url: 图片URL（与image_base64二选一）
            image_base64: 图片base64编码（与image_url二选一）
            image_type: 图片类型（screenshot/ota/wechat等）

        Returns:
            ToolResult: 解析结果
        """
        # 验证参数
        if not image_url and not image_base64:
            return ToolResult.error_result(
                "请提供图片URL或图片base64编码"
            )

        try:
            # 调用图片识别服务
            result = await self.recognition_service.recognize(
                image_url=image_url,
                image_base64=image_base64,
                image_type=image_type
            )

            # 提取关键信息
            extracted_info = {
                'hotel_name': result.get('hotel_name'),
                'check_in_date': result.get('check_in_date'),
                'check_out_date': result.get('check_out_date'),
                'room_type': result.get('room_type'),
                'price': result.get('price'),
                'confidence': result.get('confidence', {}),
                'raw_text': result.get('raw_text', ''),
            }

            # 计算整体置信度
            confidence_scores = result.get('confidence', {})
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0

            return ToolResult.success_result(
                data=extracted_info,
                metadata={
                    'image_type': image_type,
                    'has_image_url': bool(image_url),
                    'has_image_base64': bool(image_base64),
                    'average_confidence': round(avg_confidence, 2),
                    'confidence_scores': confidence_scores,
                }
            )

        except Exception as e:
            return ToolResult.error_result(
                f"图片解析失败: {str(e)}",
                metadata={
                    'image_type': image_type,
                    'has_image_url': bool(image_url),
                    'has_image_base64': bool(image_base64),
                }
            )

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片文件编码为base64

        Args:
            image_path: 图片文件路径

        Returns:
            base64编码的字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
