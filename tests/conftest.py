"""Конфигурация для тестов"""
import pytest
import aiosqlite
import os
import asyncio
import uuid
from pathlib import Path


@pytest.fixture(scope="function")
async def test_db():
    """Создание тестовой базы данных для каждого теста"""
    # Создаём уникальное имя БД для каждого теста
    test_db_path = f"test_bot_database_{uuid.uuid4().hex[:8]}.db"
    
    # Удаляем старую тестовую БД если есть
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except:
            pass
    
    # Создаём новую БД
    async with aiosqlite.connect(test_db_path) as db:
        # Включаем поддержку внешних ключей для CASCADE
        await db.execute("PRAGMA foreign_keys = ON")
        
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
    
    yield test_db_path
    
    # Удаляем файл БД после теста
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except:
            pass


@pytest.fixture(scope="function")
def mock_config(monkeypatch, test_db):
    """Мок конфигурации с тестовой БД"""
    # Применяем monkeypatch до импорта database
    monkeypatch.setattr("config.DATABASE_PATH", test_db)
    monkeypatch.setattr("database.DATABASE_PATH", test_db)
    return test_db


@pytest.fixture
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

