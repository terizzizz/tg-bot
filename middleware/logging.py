"""
Middleware для логирования действий пользователей
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех действий"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Логируем входящее обновление
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else 0
            username = event.from_user.username if event.from_user and event.from_user.username else "Нет username"
            text = event.text or event.caption or "[Медиа]"
            
            logger.info(
                f"📨 Сообщение от {user_id} (@{username}): {text[:100]}"
            )
        
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else 0
            username = event.from_user.username if event.from_user and event.from_user.username else "Нет username"
            data_text = event.data or "Нет data"
            
            logger.info(
                f"🔘 Callback от {user_id} (@{username}): {data_text}"
            )
        
        # Выполняем handler
        result = await handler(event, data)
        
        return result


