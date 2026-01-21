"""Конфигурация для тестов"""
import pytest
import aiosqlite
import os
import asyncio
from pathlib import Path

# Путь к тестовой базе данных
TEST_DB_PATH = "test_bot_database.db"


@pytest.fixture(scope="function")
async def test_db():
    """Создание тестовой базы данных для каждого теста"""
    # Удаляем старую тестовую БД если есть
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    # Создаём новую БД
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                current_group INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Таблица желаемых групп
        await db.execute("""
            CREATE TABLE IF NOT EXISTS desired_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                desired_group INTEGER,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        """)
        
        await db.commit()
    
    yield TEST_DB_PATH
    
    # Очистка после теста
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def mock_config(monkeypatch, test_db):
    """Мок конфигурации с тестовой БД"""
    monkeypatch.setattr("config.DATABASE_PATH", test_db)
    return test_db


@pytest.fixture
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

