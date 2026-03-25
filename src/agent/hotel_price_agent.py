"""
酒店价格查询Agent —— 基于LangChain重构

使用 LangChain AgentExecutor + Tool Calling 替代手写状态机：
- LLM 自动从对话中提取酒店名称、日期、房型等信息
- LLM 自主决定何时调用搜索/查价工具
- LLM 自动生成追问和格式化回复
- 会话历史在内存中按 session_id 管理
"""

import os
from typing import Optional, Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from loguru import logger

from src.tools import SearchHotelTool, QueryPriceTool, ParseImageTool


class HotelPriceAgent:
    """
    酒店价格查询Agent（LangChain版）

    核心改动：
    - 移除 StateManager（Redis）和 QueryState/QueryStep 状态机
    - 移除 LLMExtractionService（LLM 在 Agent 流程中自然完成信息提取）
    - 使用 LangChain Tool Calling Agent 自主调度工具
    - 会话历史按 session_id 在内存中管理
    """

    def __init__(
        self,
        search_hotel_tool: Optional[SearchHotelTool] = None,
        query_price_tool: Optional[QueryPriceTool] = None,
        parse_image_tool: Optional[ParseImageTool] = None,
    ):
        """
        初始化Agent

        Args:
            search_hotel_tool: 搜索酒店工具（LangChain BaseTool）
            query_price_tool: 查询价格工具（LangChain BaseTool）
            parse_image_tool: 解析图片工具（LangChain BaseTool）
        """
        # 初始化工具（支持外部注入，也可自动创建）
        self.search_hotel_tool = search_hotel_tool or SearchHotelTool()
        self.query_price_tool = query_price_tool or QueryPriceTool()
        self.parse_image_tool = parse_image_tool or ParseImageTool()
        self.tools = [self.search_hotel_tool, self.query_price_tool, self.parse_image_tool]

        # 会话历史（内存管理，key=session_id）
        self.session_histories: Dict[str, List] = {}

        # 加载系统提示词
        self.system_prompt = self._load_prompt()

        # 初始化 LLM
        self.llm = ChatOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            model=os.getenv("MODEL_NAME", "qwen-max"),
            max_tokens=800,
            temperature=0.1,
        )

        # 构建 LangChain Agent
        self.agent_executor = self._build_agent()

    def _load_prompt(self) -> str:
        """加载酒店查询提示词（优先 .txt，fallback 到 _example.txt）"""
        prompt_dir = "prompts"
        target_path = os.path.join(prompt_dir, "hotel_query_prompt.txt")
        if os.path.exists(target_path):
            file_path = target_path
        else:
            file_path = os.path.join(prompt_dir, "hotel_query_prompt_example.txt")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                logger.debug(f"已加载酒店查询提示词, 路径: {file_path}, 长度: {len(content)} 字符")
                return content

        logger.warning("未找到酒店查询提示词文件, 使用默认提示词")
        return "你是酒店价格查询助手，帮助用户查询酒店房间价格。"

    def _build_agent(self) -> AgentExecutor:
        """
        构建 LangChain Tool Calling Agent

        使用 ChatPromptTemplate + MessagesPlaceholder 管理多轮对话，
        LLM 通过 tool calling 自主调度搜索和查价工具。
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # 防止无限循环
        )

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理用户消息（接口与原版保持一致，兼容 XianyuAgent._handle_with_handler）

        Args:
            session_id: 会话ID
            user_message: 用户消息
            image_url: 图片URL（如果用户发送了图片）
            image_base64: 图片base64编码

        Returns:
            包含 reply, complete, state, result 的字典
        """
        # 获取会话历史
        chat_history = self.session_histories.get(session_id, [])

        # 构建输入消息
        input_msg = user_message

        # 如果有图片，先用工具解析再将结果注入消息
        if image_url or image_base64:
            input_msg = await self._preprocess_image(input_msg, image_url, image_base64)

        try:
            # 调用 LangChain Agent
            result = await self.agent_executor.ainvoke({
                "input": input_msg,
                "chat_history": chat_history,
            })

            reply = result.get("output", "")

            # 更新会话历史
            chat_history.append(HumanMessage(content=user_message))
            chat_history.append(AIMessage(content=reply))
            self.session_histories[session_id] = chat_history

            # 判断是否完成查询（回复中包含价格相关标志）
            is_complete = any(marker in reply for marker in ["💰", "¥", "价格"])

            logger.info(f"HotelPriceAgent 回复完成, session={session_id}, complete={is_complete}")

            return {
                'reply': reply,
                'complete': is_complete,
                'state': {
                    'current_step': 'complete' if is_complete else 'processing',
                    'session_id': session_id,
                    'history_length': len(chat_history),
                },
                'result': None,
            }

        except Exception as e:
            logger.error(f"HotelPriceAgent 处理异常: {e}")
            return {
                'reply': "查询过程中发生错误，请稍后重试。",
                'complete': False,
                'state': {'current_step': 'error', 'session_id': session_id},
                'result': None,
            }

    async def _preprocess_image(self, user_message: str, image_url: Optional[str],
                                image_base64: Optional[str]) -> str:
        """
        预处理图片：直接调用 parse_image_tool 解析图片，将提取结果注入消息。
        避免将巨大的 base64 字符串传给 LLM。

        Args:
            user_message: 原始用户消息
            image_url: 图片URL
            image_base64: 图片base64编码

        Returns:
            包含图片解析结果的增强消息
        """
        logger.info("检测到用户发送图片，预处理解析中...")
        try:
            parsed = await self.parse_image_tool.execute(
                image_url=image_url,
                image_base64=image_base64,
            )
            if parsed.success:
                logger.info(f"图片解析成功: {parsed.data}")
                return f"{user_message}\n[从用户发送的酒店截图中解析出以下信息: {parsed.to_json()}]"
            else:
                logger.warning(f"图片解析失败: {parsed.error}")
                return f"{user_message}\n[用户发送了一张图片但解析失败，请询问用户手动提供酒店信息]"
        except Exception as e:
            logger.error(f"图片预处理异常: {e}")
            return f"{user_message}\n[图片处理出错，请用户手动输入酒店信息]"

    def clear_session(self, session_id: str):
        """清除指定会话的历史"""
        if session_id in self.session_histories:
            del self.session_histories[session_id]
            logger.info(f"已清除会话历史: {session_id}")

    async def close(self):
        """关闭所有工具资源"""
        await self.search_hotel_tool.close()
        await self.query_price_tool.close()
        await self.parse_image_tool.close()
