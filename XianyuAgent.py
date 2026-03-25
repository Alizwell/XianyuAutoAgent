"""
闲鱼自动回复Agent系统 —— 基于LangChain重构

使用 LangChain 统一管理各领域 Agent 的提示词、LLM调用、工具和意图路由。
每个 Agent 通过 AgentConfig 配置，支持可选绑定 tools。
工具类已原生集成 LangChain BaseTool，无需额外包装。
"""

import re
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger

from src.agent.hotel_price_agent import HotelPriceAgent
from src.tools import SearchHotelTool, QueryPriceTool, ParseImageTool


# ============================================================
# Agent 配置数据类
# ============================================================

@dataclass
class AgentConfig:
    """
    Agent 配置项

    Attributes:
        chain: LangChain Runnable Chain（prompt | llm | parser）
        tools: 该Agent可使用的工具列表（LangChain BaseTool 子类）
        handler: 自定义处理器（用于需要特殊处理逻辑的Agent，如hotel_query）
        system_prompt: 系统提示词原文
        temperature: LLM温度参数
    """
    chain: Any = None
    tools: List[Any] = field(default_factory=list)
    handler: Any = None
    system_prompt: str = ""
    temperature: float = 0.4


# ============================================================
# 主Bot类
# ============================================================

class XianyuReplyBot:
    """闲鱼自动回复Bot（LangChain版）"""

    def __init__(self):
        # 初始化LangChain LLM
        self.llm = ChatOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            model=os.getenv("MODEL_NAME", "qwen-max"),
            max_tokens=500,
            top_p=0.8,
        )
        self._init_system_prompts()
        self._init_agents()
        self.router = IntentRouter(self.agents['classify'].chain, self.llm)
        self.last_intent = None  # 记录最后一次意图

    def _init_agents(self):
        """
        初始化各领域Agent，统一存储在 self.agents 字典中。
        每个Agent是一个 AgentConfig 实例，包含 chain、tools、handler 等配置。
        工具类已原生集成 LangChain BaseTool，直接实例化即可。
        """
        # 初始化 LangChain 原生工具实例
        search_hotel_tool = SearchHotelTool()
        query_price_tool = QueryPriceTool()
        parse_image_tool = ParseImageTool()

        # 酒店相关工具列表
        hotel_tools = [search_hotel_tool, query_price_tool, parse_image_tool]

        # 初始化 HotelPriceAgent（复用工具实例，避免重复创建适配器）
        hotel_agent = HotelPriceAgent(
            search_hotel_tool=search_hotel_tool,
            query_price_tool=query_price_tool,
            parse_image_tool=parse_image_tool,
        )

        self.agents: Dict[str, AgentConfig] = {
            # 分类Agent：用于意图识别兜底
            'classify': AgentConfig(
                chain=self._build_chain(self.classify_prompt, temperature=0.4),
                system_prompt=self.classify_prompt,
                temperature=0.4,
            ),
            # 议价Agent
            'price': AgentConfig(
                chain=self._build_chain(self.price_prompt, temperature=0.4),
                system_prompt=self.price_prompt,
                temperature=0.4,
            ),
            # 技术咨询Agent
            'tech': AgentConfig(
                chain=self._build_chain(self.tech_prompt, temperature=0.4),
                system_prompt=self.tech_prompt,
                temperature=0.4,
            ),
            # 默认Agent
            'default': AgentConfig(
                chain=self._build_chain(self.default_prompt, temperature=0.7),
                system_prompt=self.default_prompt,
                temperature=0.7,
            ),
            # 酒店价格查询Agent：使用 LangChain AgentExecutor + handler
            'hotel_query': AgentConfig(
                chain=self._build_chain(self.hotel_query_prompt, temperature=0.4),
                tools=hotel_tools,
                handler=hotel_agent,
                system_prompt=self.hotel_query_prompt,
                temperature=0.4,
            ),
        }

    def _build_chain(self, system_prompt: str, temperature: float = 0.4):
        """
        构建一个 LangChain Chain（prompt | llm | parser）

        Args:
            system_prompt: 系统提示词模板
            temperature: LLM温度参数

        Returns:
            可执行的 Runnable Chain
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "【商品信息】{item_desc}\n【你与客户对话历史】{context}\n{system_prompt}"),
            ("human", "{user_msg}"),
        ])

        llm_with_temp = self.llm.bind(temperature=temperature)
        return prompt | llm_with_temp | StrOutputParser()

    def _init_system_prompts(self):
        """初始化各Agent专用提示词，优先加载用户自定义文件，否则使用Example默认文件"""
        prompt_dir = "prompts"

        def load_prompt_content(name: str) -> str:
            """尝试加载提示词文件"""
            target_path = os.path.join(prompt_dir, f"{name}.txt")
            if os.path.exists(target_path):
                file_path = target_path
            else:
                file_path = os.path.join(prompt_dir, f"{name}_example.txt")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                logger.debug(f"已加载 {name} 提示词，路径: {file_path}, 长度: {len(content)} 字符")
                return content

        try:
            self.classify_prompt = load_prompt_content("classify_prompt")
            self.price_prompt = load_prompt_content("price_prompt")
            self.tech_prompt = load_prompt_content("tech_prompt")
            self.default_prompt = load_prompt_content("default_prompt")
            self.hotel_query_prompt = load_prompt_content("hotel_query_prompt")
            logger.info("成功加载所有提示词")
        except Exception as e:
            logger.error(f"加载提示词时出错: {e}")
            raise

    def _safe_filter(self, text: str) -> str:
        """安全过滤模块"""
        blocked_phrases = ["微信", "QQ", "支付宝", "银行卡", "线下"]
        return "[安全提醒]请通过平台沟通" if any(p in text for p in blocked_phrases) else text

    def format_history(self, context: List[Dict]) -> str:
        """格式化对话历史，返回完整的对话记录"""
        user_assistant_msgs = [msg for msg in context if msg['role'] in ['user', 'assistant']]
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in user_assistant_msgs])

    async def generate_reply(self, user_msg: str, item_desc: str, context: List[Dict],
                             image_url: Optional[str] = None, image_base64: Optional[str] = None) -> str:
        """
        生成回复主流程（接口保持不变，兼容 main.py 调用）
        """
        formatted_context = self.format_history(context)

        # 1. 路由决策
        detected_intent = self.router.detect(user_msg, item_desc, formatted_context)

        # 2. 无需回复
        if detected_intent == 'no_reply':
            logger.info('意图识别完成: no_reply - 无需回复')
            self.last_intent = 'no_reply'
            return "-"

        # 3. 获取对应 AgentConfig
        internal_intents = {'classify'}
        if detected_intent in self.agents and detected_intent not in internal_intents:
            agent_config = self.agents[detected_intent]
            logger.info(f'意图识别完成: {detected_intent}')
            self.last_intent = detected_intent
        else:
            agent_config = self.agents['default']
            logger.info('意图识别完成: default')
            self.last_intent = 'default'

        # 4. 如果Agent配置了自定义handler，优先使用handler处理
        if agent_config.handler is not None:
            return await self._handle_with_handler(agent_config, user_msg, context, image_url, image_base64)

        # 5. 使用标准Chain处理
        return self._handle_with_chain(agent_config, detected_intent, user_msg, item_desc, formatted_context, context)

    async def _handle_with_handler(self, agent_config: AgentConfig, user_msg: str,
                                   context: List[Dict], image_url: Optional[str],
                                   image_base64: Optional[str]) -> str:
        """使用自定义handler处理消息（如酒店价格查询Agent）"""
        session_id = self._get_session_id(context)
        result = await agent_config.handler.process_message(
            session_id=session_id,
            user_message=user_msg,
            image_url=image_url,
            image_base64=image_base64,
        )

        reply = result['reply']
        logger.info(f'Agent处理完成: 状态={result["state"]["current_step"]}')

        # 记录该Agent可用的工具信息
        if agent_config.tools:
            logger.debug(f'该Agent配置了 {len(agent_config.tools)} 个工具: '
                        f'{[t.name for t in agent_config.tools]}')

        return self._safe_filter(reply)

    def _handle_with_chain(self, agent_config: AgentConfig, intent: str,
                           user_msg: str, item_desc: str, formatted_context: str,
                           context: List[Dict]) -> str:
        """使用LangChain Chain处理消息"""
        bargain_count = self._extract_bargain_count(context)
        logger.info(f'议价次数: {bargain_count}')

        chain = agent_config.chain

        chain_input = {
            "user_msg": user_msg,
            "item_desc": item_desc,
            "context": formatted_context,
            "system_prompt": agent_config.system_prompt,
        }

        # 对议价Agent追加议价轮次信息并动态调整温度
        if intent == 'price':
            chain_input["system_prompt"] += f"\n▲当前议价轮次：{bargain_count}"
            dynamic_temp = min(0.3 + bargain_count * 0.15, 0.9)
            chain = self._build_chain(chain_input["system_prompt"], temperature=dynamic_temp)

        response = chain.invoke(chain_input)
        return self._safe_filter(response)

    def _get_session_id(self, context: List[Dict]) -> str:
        """从上下文中获取会话ID"""
        if context:
            first_msg = context[0].get('content', '')
            return str(hash(first_msg))[:16]
        return 'default'

    def _extract_bargain_count(self, context: List[Dict]) -> int:
        """从上下文中提取议价次数信息"""
        for msg in context:
            if msg['role'] == 'system' and '议价次数' in msg['content']:
                try:
                    match = re.search(r'议价次数[:：]\s*(\d+)', msg['content'])
                    if match:
                        return int(match.group(1))
                except Exception:
                    pass
        return 0

    def reload_prompts(self):
        """重新加载所有提示词"""
        logger.info("正在重新加载提示词...")
        self._init_system_prompts()
        self._init_agents()
        self.router = IntentRouter(self.agents['classify'].chain, self.llm)
        logger.info("提示词重新加载完成")

    def get_agent_tools(self, intent: str) -> list:
        """
        获取指定Agent的工具列表

        Args:
            intent: Agent名称/意图名

        Returns:
            LangChain BaseTool 子类实例列表
        """
        if intent in self.agents:
            return self.agents[intent].tools
        return []


# ============================================================
# 意图路由器
# ============================================================

class IntentRouter:
    """
    意图路由决策器

    三级路由策略：
    1. 规则匹配（关键词 + 正则）
    2. 图片消息特殊处理
    3. LangChain Chain 大模型兜底分类
    """

    def __init__(self, classify_chain, llm):
        self.rules = {
            'tech': {
                'keywords': ['参数', '规格', '型号', '连接', '对比'],
                'patterns': [r'和.+比']
            },
            'price': {
                'keywords': ['便宜', '价', '砍价', '少点'],
                'patterns': [r'\d+元', r'能少\d+']
            },
            'hotel_query': {
                'keywords': ['酒店', '代订', '价格', '查询', '哪天', '日期', '房型', '入住'],
                'patterns': [
                    r'.*酒店.*价格',
                    r'.*入住.*日期',
                    r'.*房型.*多少钱',
                    r'.*什么房型'
                ]
            }
        }
        self.classify_chain = classify_chain

    def detect(self, user_msg: str, item_desc: str, context: str) -> str:
        """三级路由策略（技术优先）"""
        if '[图片]' in user_msg:
            logger.debug("用户发送图片，默认按酒店价格查询处理")
            return 'hotel_query'

        text_clean = re.sub(r'[^\w\u4e00-\u9fa5]', '', user_msg)

        # 1. 技术类关键词优先检查
        if any(kw in text_clean for kw in self.rules['tech']['keywords']):
            return 'tech'

        # 2. 技术类正则优先检查
        for pattern in self.rules['tech']['patterns']:
            if re.search(pattern, text_clean):
                return 'tech'

        # 3. 酒店查询检查
        if any(kw in text_clean for kw in self.rules['hotel_query']['keywords']):
            logger.debug(f"酒店查询关键词匹配: {[kw for kw in self.rules['hotel_query']['keywords'] if kw in text_clean]}")
            return 'hotel_query'

        for pattern in self.rules['hotel_query']['patterns']:
            if re.search(pattern, text_clean):
                logger.debug(f"酒店查询正则匹配: {pattern}")
                return 'hotel_query'

        # 4. 价格类检查
        if any(kw in text_clean for kw in self.rules['price']['keywords']):
            return 'price'

        for pattern in self.rules['price']['patterns']:
            if re.search(pattern, text_clean):
                return 'price'

        # 5. 大模型兜底
        logger.debug("使用大模型进行意图分类")
        result = self.classify_chain.invoke({
            "user_msg": user_msg,
            "item_desc": item_desc,
            "context": context,
            "system_prompt": "",
        })
        return result.strip().lower()