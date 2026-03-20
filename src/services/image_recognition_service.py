"""图片识别服务"""

import os
import base64
import json
from typing import Optional, Dict, Any
import httpx


class ImageRecognitionService:
    """图片识别服务 - 使用多模态LLM识别图片中的酒店信息"""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("VISION_MODEL", "gpt-4-vision-preview")
        self.timeout = 60

    async def recognize(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_type: str = "screenshot"
    ) -> Dict[str, Any]:
        """
        识别图片中的酒店信息

        Args:
            image_url: 图片URL
            image_base64: 图片base64编码
            image_type: 图片类型

        Returns:
            识别的酒店信息
        """
        # 构建图片内容
        if image_url:
            image_content = {
                "type": "image_url",
                "image_url": {"url": image_url}
            }
        elif image_base64:
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }
        else:
            raise ValueError("请提供图片URL或base64编码")

        # 构建提示词
        prompt = self._build_prompt(image_type)

        # 调用API
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content
                ]
            }
        ]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 1000,
                        "temperature": 0.1
                    }
                )
                response.raise_for_status()
                result = response.json()

                # 解析响应
                content = result['choices'][0]['message']['content']
                return self._parse_response(content)

        except Exception as e:
            # 返回空结果
            return {
                'hotel_name': None,
                'check_in_date': None,
                'check_out_date': None,
                'room_type': None,
                'price': None,
                'confidence': {},
                'raw_text': str(e)
            }

    def _build_prompt(self, image_type: str) -> str:
        """构建提示词"""
        return f"""请分析这张酒店预订相关的图片，提取以下信息：

1. 酒店名称（hotel_name）
2. 入住日期（check_in_date，格式：YYYY-MM-DD）
3. 离店日期（check_out_date，格式：YYYY-MM-DD）
4. 房型（room_type，如：高级大床房、双床房等）
5. 价格（price，数字，单位元）

请以JSON格式返回结果：
{{
    "hotel_name": "酒店名称",
    "check_in_date": "2024-01-01",
    "check_out_date": "2024-01-02",
    "room_type": "房型名称",
    "price": 299,
    "confidence": {{
        "hotel_name": 0.95,
        "check_in_date": 0.98,
        "check_out_date": 0.98,
        "room_type": 0.90,
        "price": 0.95
    }}
}}

如果某字段无法识别，请设置为null。confidence字段表示每个字段的识别置信度（0-1之间的小数）。"""

    def _parse_response(self, content: str) -> dict:
        """解析API响应"""
        try:
            # 尝试直接解析JSON
            result = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从文本中提取JSON
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(content[start:end])
                else:
                    result = {}
            except Exception:
                result = {}

        # 确保返回格式正确
        return {
            'hotel_name': result.get('hotel_name'),
            'check_in_date': result.get('check_in_date'),
            'check_out_date': result.get('check_out_date'),
            'room_type': result.get('room_type'),
            'price': result.get('price'),
            'confidence': result.get('confidence', {}),
            'raw_text': content
        }
