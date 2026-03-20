"""酒店价格查询Agent"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from src.models import QueryState, QueryStep
from src.tools import (
    BaseTool,
    ToolResult,
    SearchHotelTool,
    QueryPriceTool,
    ParseImageTool
)
from src.agent.state_manager import StateManager


class HotelPriceAgent:
    """酒店价格查询Agent"""

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        search_hotel_tool: Optional[SearchHotelTool] = None,
        query_price_tool: Optional[QueryPriceTool] = None,
        parse_image_tool: Optional[ParseImageTool] = None
    ):
        """
        初始化Agent

        Args:
            state_manager: 状态管理器
            search_hotel_tool: 搜索酒店工具
            query_price_tool: 查询价格工具
            parse_image_tool: 解析图片工具
        """
        self.state_manager = state_manager or StateManager()
        self.search_hotel_tool = search_hotel_tool or SearchHotelTool()
        self.query_price_tool = query_price_tool or QueryPriceTool()
        self.parse_image_tool = parse_image_tool or ParseImageTool()

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            session_id: 会话ID
            user_message: 用户消息
            image_url: 图片URL（如果用户发送了图片）
            image_base64: 图片base64

        Returns:
            处理结果，包含回复内容和是否完成
        """
        # 获取或创建状态
        state = self.state_manager.get_state(session_id)
        if not state:
            state = self.state_manager.create_state(session_id)

        # 如果有图片，先解析图片
        if image_url or image_base64:
            await self._parse_image(state, image_url, image_base64)

        # 解析用户文本，提取信息
        self._extract_info_from_text(state, user_message)

        # 根据当前步骤处理
        result = await self._process_by_step(state)

        # 保存状态
        self.state_manager.save_state(state)

        return {
            'reply': result['reply'],
            'complete': state.current_step == QueryStep.COMPLETE,
            'state': state.to_dict(),
            'result': result.get('result')
        }

    async def _parse_image(
        self,
        state: QueryState,
        image_url: Optional[str],
        image_base64: Optional[str]
    ):
        """解析图片"""
        state.update_step(QueryStep.PARSING_IMAGE)

        result = await self.parse_image_tool.execute(
            image_url=image_url,
            image_base64=image_base64
        )

        if result.success:
            data = result.data
            # 填充提取的信息
            if data.get('hotel_name') and data['confidence'].get('hotel_name', 0) >= 0.5:
                state.hotel_name = data['hotel_name']
            if data.get('check_in_date') and data['confidence'].get('check_in_date', 0) >= 0.5:
                state.check_in_date = self._normalize_date(data['check_in_date'])
            if data.get('check_out_date') and data['confidence'].get('check_out_date', 0) >= 0.5:
                state.check_out_date = self._normalize_date(data['check_out_date'])
            if data.get('room_type') and data['confidence'].get('room_type', 0) >= 0.5:
                state.room_type = data['room_type']

            state.image_parse_result = data

    def _extract_info_from_text(self, state: QueryState, text: str):
        """从文本提取信息"""
        text_lower = text.lower()

        # 提取日期
        # 简单实现：匹配 YYYY-MM-DD 格式
        import re
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
        if len(dates) >= 2:
            if not state.check_in_date:
                state.check_in_date = dates[0]
            if not state.check_out_date:
                state.check_out_date = dates[1]
        elif len(dates) == 1:
            if not state.check_in_date:
                state.check_in_date = dates[0]
                # 默认离店日期是入住后一天
                next_day = datetime.strptime(dates[0], '%Y-%m-%d') + timedelta(days=1)
                if not state.check_out_date:
                    state.check_out_date = next_day.strftime('%Y-%m-%d')

        # 房型关键词
        room_type_keywords = [
            '大床', '双床', '套房', '家庭房', '标准间', '高级',
            '豪华', '行政', '景观', '城景', '海景'
        ]
        for keyword in room_type_keywords:
            if keyword in text_lower and not state.room_type:
                # 提取包含关键词的词组
                words = text.split()
                for word in words:
                    if keyword in word.lower():
                        state.room_type = word
                        break
                if not state.room_type:
                    state.room_type = f"{keyword}房"

        # 酒店名称 - 如果还没找到，尝试提取
        if not state.hotel_name:
            # 简单实现：去掉日期和房型关键词，剩下的作为酒店名称
            cleaned = text
            for date in dates:
                cleaned = cleaned.replace(date, '')
            for keyword in room_type_keywords:
                cleaned = cleaned.replace(keyword, '')
            cleaned = cleaned.strip()
            if cleaned:
                state.hotel_name = cleaned

        # 更新到下一个需要信息的步骤
        self._advance_to_missing_step(state)

    def _advance_to_missing_step(self, state: QueryState):
        """根据缺失信息前进到下一步骤"""
        if not state.hotel_name:
            state.update_step(QueryStep.AWAITING_HOTEL_NAME)
        elif not state.check_in_date:
            state.update_step(QueryStep.AWAITING_CHECKIN_DATE)
        elif not state.check_out_date:
            state.update_step(QueryStep.AWAITING_CHECKOUT_DATE)
        elif not state.room_type:
            state.update_step(QueryStep.AWAITING_ROOM_TYPE)
        else:
            state.update_step(QueryStep.SEARCHING)

    async def _process_by_step(self, state: QueryState) -> Dict[str, Any]:
        """根据当前步骤处理"""
        step = state.current_step

        if step == QueryStep.AWAITING_HOTEL_NAME:
            return {'reply': "未能从图片中识别出有效的酒店信息，请提供您要预订的酒店名称、入住日期、离店日期和房型信息。例如：汉庭厦门中山路轮渡酒店 2026-03-22 2026-03-23 高级大床房"}

        elif step == QueryStep.AWAITING_CHECKIN_DATE:
            return {'reply': f"好的，{state.hotel_name}。请问您的入住日期是哪天？请提供YYYY-MM-DD格式。"}

        elif step == QueryStep.AWAITING_CHECKOUT_DATE:
            if state.check_in_date:
                return {'reply': f"入住日期是{state.check_in_date}。请问离店日期是哪天？请提供YYYY-MM-DD格式。"}
            else:
                return {'reply': "请问离店日期是哪天？请提供YYYY-MM-DD格式。"}

        elif step == QueryStep.AWAITING_ROOM_TYPE:
            return {'reply': "请问您需要什么房型？比如大床房、双床房等。"}

        elif step == QueryStep.SEARCHING:
            return await self._execute_search(state)

        elif step == QueryStep.COMPLETE:
            # 返回最终结果
            return self._format_result(state)

        else:
            return {'reply': "请提供需要查询的酒店信息。"}

    async def _execute_search(self, state: QueryState) -> Dict[str, Any]:
        """执行搜索流程"""
        try:
            # 第一步：搜索酒店
            search_result = await self.search_hotel_tool.execute(
                keyword=state.hotel_name,
                check_in_date=state.check_in_date,
                check_out_date=state.check_out_date
            )

            if not search_result.success or not search_result.data:
                state.error_message = f"未找到酒店: {search_result.error}"
                state.update_step(QueryStep.AWAITING_HOTEL_NAME)
                return {'reply': f"未找到' {state.hotel_name}'，请检查酒店名称是否正确。"}

            state.search_results = search_result.data

            # 取第一个匹配结果
            if len(search_result.data) > 0:
                first_hotel = search_result.data[0]
                state.hotel_id = first_hotel['hotel_id']

            # 第二步：查询价格
            if state.hotel_id:
                price_result = await self.query_price_tool.execute(
                    hotel_id=state.hotel_id,
                    check_in_date=state.check_in_date,
                    check_out_date=state.check_out_date,
                    room_type=state.room_type
                )

                if not price_result.success:
                    state.error_message = f"查询价格失败: {price_result.error}"
                    return {'reply': f"查询价格失败: {price_result.error}"}

                price_data = price_result.data
                state.price_results = price_data.get('rooms', [])

            # 完成查询
            state.update_step(QueryStep.COMPLETE)
            return self._format_result(state)

        except Exception as e:
            state.error_message = str(e)
            return {'reply': f"查询过程中发生错误: {str(e)}"}

    def _format_result(self, state: QueryState) -> Dict[str, Any]:
        """格式化查询结果"""
        if not state.price_results:
            reply = f"查询完成，但未找到{state.hotel_name}在{state.check_in_date}至{state.check_out_date}的{state.room_type}价格。"
            return {'reply': reply, 'result': None}

        room = state.price_results[0] if len(state.price_results) > 0 else None
        if not room:
            reply = f"查询完成，但该日期没有可用的{state.room_type}。"
            return {'reply': reply, 'result': None}

        # 简洁报价模式
        hotel_name = state.hotel_name or (state.search_results and state.search_results[0]['hotel_name'])
        nights = self._calculate_nights(state.check_in_date, state.check_out_date)
        total_price = room['price'] * nights

        reply = f"""🏨 {hotel_name}
📅 {state.check_in_date} - {state.check_out_date} ({nights}晚)
💎 {room['room_type_name']}
💰 价格: ¥{int(room['price'])}/晚 | 总价: ¥{int(total_price)}
"""

        if room.get('breakfast'):
            reply += f"🍳 {room['breakfast']}\n"
        if room.get('cancel_policy'):
            reply += f"📝 {room['cancel_policy']}\n"

        if len(state.price_results) > 1:
            reply += f"\n还有其他房型可供选择哦~"

        return {
            'reply': reply.strip(),
            'result': {
                'hotel_name': hotel_name,
                'check_in_date': state.check_in_date,
                'check_out_date': state.check_out_date,
                'room_type': state.room_type,
                'price_per_night': room['price'],
                'total_price': total_price,
                'rooms': state.price_results
            }
        }

    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式"""
        # 如果已经是YYYY-MM-DD，直接返回
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # 尝试其他格式
        patterns = [
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', r'\1-\2-\3'),
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', r'\3-\1-\2'),
        ]
        import re
        for pattern, repl in patterns:
            match = re.match(pattern, date_str)
            if match:
                return re.sub(pattern, repl, date_str)

        return date_str

    def _calculate_nights(self, check_in: str, check_out: str) -> int:
        """计算晚数"""
        try:
            ci = datetime.strptime(check_in, '%Y-%m-%d')
            co = datetime.strptime(check_out, '%Y-%m-%d')
            delta = co - ci
            return max(1, delta.days)
        except Exception:
            return 1

    def get_missing_info_prompt(self, state: QueryState) -> str:
        """获取缺失信息提示"""
        missing = state.get_missing_fields()
        prompts = {
            'hotel_name': "请问您要查询哪家酒店？",
            'check_in_date': "请问入住日期是哪天？（请提供YYYY-MM-DD格式）",
            'check_out_date': "请问离店日期是哪天？（请提供YYYY-MM-DD格式）",
            'room_type': "请问您需要什么房型？",
        }

        for field in missing:
            if field in prompts:
                return prompts[field]

        return "请补充完整查询信息。"

    async def close(self):
        """关闭工具"""
        await self.search_hotel_tool.close()
        await self.query_price_tool.close()
