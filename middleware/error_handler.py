"""
Middleware для обработки ошибок
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка при обработке обновления: {e}", exc_info=True)
            
            # Получаем объект события для отправки сообщения об ошибке
            bot: Bot = data.get("bot")
            
            if not bot:
                return None
            
            try:
                if isinstance(event, Message):
                    await bot.send_message(
                        event.chat.id,
                        "❌ Произошла ошибка при обработке запроса.\n\n"
                        "Попробуйте ещё раз или обратитесь в поддержку: /support"
                    )
                elif isinstance(event, CallbackQuery):
                    await bot.answer_callback_query(
                        event.id,
                        text="❌ Произошла ошибка. Попробуйте снова.",
                        show_alert=True
                    )
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            
            return None

