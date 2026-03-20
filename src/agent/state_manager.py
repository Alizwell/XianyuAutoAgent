"""状态管理器"""

import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.models import QueryState, QueryStep


class StateManager:
    """查询状态管理器"""

    DEFAULT_TTL = 1800  # 30分钟

    def __init__(
        self,
        redis_host: str = 'localhost',
        redis_port: int = 6379,
        redis_db: int = 0,
        password: Optional[str] = None,
        ttl: int = DEFAULT_TTL
    ):
        """
        初始化状态管理器

        Args:
            redis_host: Redis主机
            redis_port: Redis端口
            redis_db: Redis数据库
            password: Redis密码
            ttl: 状态过期时间（秒）
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=password,
            decode_responses=True
        )
        self.ttl = ttl

    def _get_key(self, session_id: str) -> str:
        """生成Redis键"""
        return f"hotel_query:{session_id}"

    def save_state(self, state: QueryState) -> bool:
        """
        保存查询状态

        Args:
            state: 查询状态

        Returns:
            是否保存成功
        """
        try:
            key = self._get_key(state.session_id)
            data = json.dumps(state.to_dict())
            self.redis_client.setex(key, self.ttl, data)
            return True
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False

    def get_state(self, session_id: str) -> Optional[QueryState]:
        """
        获取查询状态

        Args:
            session_id: 会话ID

        Returns:
            查询状态，不存在返回None
        """
        try:
            key = self._get_key(session_id)
            data = self.redis_client.get(key)
            if data:
                state_dict = json.loads(data)
                # 刷新TTL
                self.redis_client.expire(key, self.ttl)
                return QueryState.from_dict(state_dict)
            return None
        except Exception as e:
            print(f"获取状态失败: {e}")
            return None

    def delete_state(self, session_id: str) -> bool:
        """
        删除查询状态

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        try:
            key = self._get_key(session_id)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"删除状态失败: {e}")
            return False

    def create_state(self, session_id: str) -> QueryState:
        """
        创建新的查询状态

        Args:
            session_id: 会话ID

        Returns:
            新的查询状态
        """
        state = QueryState(session_id=session_id)
        self.save_state(state)
        return state

    def update_state_step(
        self,
        session_id: str,
        step: QueryStep,
        **kwargs
    ) -> Optional[QueryState]:
        """
        更新查询状态步骤

        Args:
            session_id: 会话ID
            step: 新步骤
            **kwargs: 其他要更新的字段

        Returns:
            更新后的状态
        """
        state = self.get_state(session_id)
        if not state:
            return None

        state.update_step(step)

        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)

        self.save_state(state)
        return state

    def clear_all_states(self) -> int:
        """
        清除所有查询状态（谨慎使用）

        Returns:
            清除的状态数量
        """
        try:
            keys = self.redis_client.keys("hotel_query:*")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"清除状态失败: {e}")
            return 0
