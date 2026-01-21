"""Логика поиска мэтчей"""
from typing import List, Dict
import database
from keyboards.keyboards import format_group_text


async def find_matches(telegram_id: int) -> List[Dict]:
    """
    Поиск мэтчей для пользователя.
    
    Мэтч = когда:
    1. User A в группе X, хочет в группу Y
    2. User B в группе Y, хочет в группу X
    """
    user = await database.get_user(telegram_id)
    if not user:
        return []
    
    user_desired_groups = await database.get_desired_groups(telegram_id)
    if not user_desired_groups:
        return []
    
    matches = []
    user_current_group = user['current_group']
    
    # Для каждой желаемой группы ищем людей, которые хотят в нашу группу
    for desired_group in user_desired_groups:
        # Получаем всех пользователей из желаемой группы
        candidates = await database.get_users_from_group(desired_group)
        
        for candidate in candidates:
            if candidate['telegram_id'] == telegram_id:
                continue  # Пропускаем себя
            
            # Получаем желаемые группы кандидата
            candidate_desired = await database.get_desired_groups(candidate['telegram_id'])
            
            # Проверяем, хочет ли кандидат в нашу группу
            if user_current_group in candidate_desired:
                # Это мэтч!
                matches.append({
                    'telegram_id': candidate['telegram_id'],
                    'username': candidate['username'],
                    'first_name': candidate['first_name'],
                    'current_group': candidate['current_group'],
                    'desired_group': user_current_group
                })
    
    return matches


async def send_match_notification(bot, user_id: int, match_user: Dict):
    """Отправка уведомления о мэтче пользователю"""
    try:
        username_display = f"@{match_user['username']}" if match_user['username'] else match_user['first_name']
        
        await bot.send_message(
            user_id,
            f"🎉 Есть мэтч!\n\n"
            f"Нашёлся человек для обмена:\n\n"
            f"👤 {username_display}\n"
            f"📍 Сейчас в: {format_group_text(match_user['current_group'])}\n"
            f"🎯 Хочет в: {format_group_text(match_user['desired_group'])} (твою группу!)\n\n"
            f"💬 Напиши ему и договоритесь об обмене!"
        )
        return True
    except Exception:
        # Если не удалось отправить (пользователь заблокировал бота и т.д.)
        return False


async def check_and_notify_new_matches(telegram_id: int, bot):
    """
    Проверка новых мэтчей после изменения данных и отправка уведомлений.
    Отправляет уведомления обоим участникам мэтча.
    Возвращает список новых мэтчей.
    """
    matches = await find_matches(telegram_id)
    user = await database.get_user(telegram_id)
    
    if not user:
        return []
    
    # Отправляем уведомления о мэтчах
    for match in matches:
        # Уведомляем текущего пользователя
        await send_match_notification(bot, telegram_id, match)
        
        # Уведомляем второго участника мэтча
        match_user_info = {
            'username': user['username'],
            'first_name': user['first_name'],
            'current_group': user['current_group'],
            'desired_group': match['current_group']  # Он хочет в группу match'а
        }
        await send_match_notification(bot, match['telegram_id'], match_user_info)
    
    return matches

