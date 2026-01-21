"""Тесты для utils/matcher.py"""
import pytest
import database
from utils import matcher


@pytest.mark.asyncio
async def test_find_matches_no_user(mock_config):
    """Тест поиска мэтчей для несуществующего пользователя"""
    await database.init_db()
    
    matches = await matcher.find_matches(99999)
    assert matches == []


@pytest.mark.asyncio
async def test_find_matches_no_desired_groups(mock_config):
    """Тест поиска мэтчей без желаемых групп"""
    await database.init_db()
    
    await database.create_user(111, "user1", "User 1", 1)
    
    matches = await matcher.find_matches(111)
    assert matches == []


@pytest.mark.asyncio
async def test_find_matches_simple_match(mock_config):
    """Тест поиска простого мэтча"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 1
    assert matches[0]['telegram_id'] == 222
    assert matches[0]['current_group'] == 2
    assert matches[0]['desired_group'] == 1


@pytest.mark.asyncio
async def test_find_matches_multiple_matches(mock_config):
    """Тест поиска нескольких мэтчей"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2 или 3
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2, 3])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # User 3: группа 3, хочет в группу 1
    await database.create_user(333, "user3", "User 3", 3)
    await database.set_desired_groups(333, [1])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 2
    assert {m['telegram_id'] for m in matches} == {222, 333}


@pytest.mark.asyncio
async def test_find_matches_no_match(mock_config):
    """Тест поиска мэтчей когда их нет"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 3 (не в группу 1)
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [3])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 0


@pytest.mark.asyncio
async def test_find_matches_exclude_self(mock_config):
    """Тест что мэтч не включает самого пользователя"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 1 (сам в себя)
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [1])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 0


@pytest.mark.asyncio
async def test_send_match_notification(mock_config):
    """Тест отправки уведомления о мэтче"""
    from unittest.mock import AsyncMock
    
    mock_bot = AsyncMock()
    match_user = {
        'username': 'testuser',
        'first_name': 'Test User',
        'current_group': 2,
        'desired_group': 1
    }
    
    result = await matcher.send_match_notification(mock_bot, 111, match_user)
    
    assert result is True
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_match_notification_no_username(mock_config):
    """Тест отправки уведомления без username"""
    from unittest.mock import AsyncMock
    
    mock_bot = AsyncMock()
    match_user = {
        'username': None,
        'first_name': 'Test User',
        'current_group': 2,
        'desired_group': 1
    }
    
    result = await matcher.send_match_notification(mock_bot, 111, match_user)
    
    assert result is True
    mock_bot.send_message.assert_called_once()

