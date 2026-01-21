"""Главный файл бота"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest

import config
import database
from handlers import start, profile, matches, help

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def handle_errors(update: Update, exception: Exception):
    """Обработка ошибок, включая блокировку бота"""
    if isinstance(exception, TelegramBadRequest):
        error_message = str(exception)
        # Если пользователь заблокировал бота, удаляем его из базы
        if "bot was blocked" in error_message.lower() or "chat not found" in error_message.lower():
            if update.message:
                user_id = update.message.from_user.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id
            else:
                return
            
            try:
                await database.delete_user(user_id)
                logger.info(f"Пользователь {user_id} заблокировал бота, удалён из базы")
            except Exception as e:
                logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
    
    return True


async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация обработчика ошибок
    dp.errors.register(handle_errors)
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(matches.router)
    dp.include_router(help.router)
    
    # Инициализация базы данных
    await database.init_db()
    logger.info("База данных инициализирована")
    
    # Запуск бота
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
