"""Хендлеры для проверки мэтчей"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import database
import keyboards.keyboards as kb
from keyboards.keyboards import format_group_text, format_groups_list_multiline
from utils.matcher import find_matches

router = Router()


@router.message(F.text == "🔍 Проверить мэтчи")
async def check_matches(message: Message):
    """Проверка актуальных мэтчей"""
    user_id = message.from_user.id
    
    if not await database.user_exists(user_id):
        await message.answer("❌ Ты ещё не зарегистрирован. Используй /start")
        return
    
    matches = await find_matches(user_id)
    
    if not matches:
        await message.answer(
            "😔 Пока мэтчей нет\n\n"
            "Но не переживай! Как только кто-то захочет в твою группу — я сразу напишу."
        )
        return
    
    # Формируем список мэтчей
    text = f"🔍 Твои актуальные мэтчи:\n\n"
    
    for i, match in enumerate(matches, 1):
        username = match['username'] if match['username'] else match['first_name']
        username_display = f"@{username}" if match['username'] else username
        
        text += (
            f"{i}️⃣ {username_display}\n"
            f"   📍 Сейчас в: {format_group_text(match['current_group'])}\n"
            f"   🎯 Хочет в: {format_group_text(match['desired_group'])} (твою группу!)\n\n"
        )
    
    text += "💬 Свяжись с ними!"
    
    await message.answer(text)


@router.message(Command("matches"))
async def cmd_matches(message: Message):
    """Команда /matches"""
    await check_matches(message)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu - показать главное меню"""
    user_id = message.from_user.id
    
    if not await database.user_exists(user_id):
        await message.answer("❌ Ты ещё не зарегистрирован. Используй /start")
        return
    
    user = await database.get_user(user_id)
    desired = await database.get_desired_groups(user_id)
    desired_str = format_groups_list_multiline(desired)
    
    await message.answer(
        f"🏠 Главное меню\n\n"
        f"👤 Твоя группа: {format_group_text(user['current_group'])}\n\n"
        f"🎯 Ищешь:\n{desired_str}\n\n"
        f"Что хочешь сделать?",
        reply_markup=kb.get_main_menu_keyboard()
    )

