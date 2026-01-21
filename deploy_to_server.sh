#!/bin/bash
# Скрипт для автоматического деплоя на сервер

SERVER="admin@your-server"
PROJECT_DIR="group_changer_bot"

echo "🚀 Деплой Group Changer Bot на сервер..."
echo ""

# Подключаемся к серверу и выполняем команды
ssh $SERVER << 'ENDSSH'
    echo "📁 Переходим в директорию проекта..."
    cd ~/group_changer_bot 2>/dev/null || cd group_changer_bot 2>/dev/null || {
        echo "📥 Репозиторий не найден, клонируем..."
        git clone git@github.com:dmitriy10291029/group_changer_bot.git
        cd group_changer_bot
    }
    
    echo "📥 Обновляем код из git..."
    git pull origin main
    
    echo "🐍 Проверяем виртуальное окружение..."
    if [ ! -d "venv" ]; then
        echo "📦 Создаём виртуальное окружение..."
        python3 -m venv venv
    fi
    
    echo "📦 Активируем окружение и обновляем зависимости..."
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    
    echo ""
    echo "✅ Деплой завершён!"
    echo ""
    echo "Для запуска бота используйте:"
    echo "  screen -S bot"
    echo "  source venv/bin/activate"
    echo "  python bot.py"
    echo "  # Нажмите Ctrl+A, затем D для отсоединения"
    echo ""
    echo "Или проверьте, не запущен ли уже бот:"
    echo "  screen -ls"
ENDSSH

echo ""
echo "✅ Деплой завершён!"


