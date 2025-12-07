#!/bin/bash
# Скрипт для запуска backend на Android через Termux
# Установка: pkg install python git -y

cd ~/AI-finance-assistant/backend || cd "$(dirname "$0")"

# Установка зависимостей если нужно
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Установка зависимостей..."
    pip install -q -r requirements.txt
fi

# Получение локального IP адреса
LOCAL_IP=$(ip route get 1.1.1.1 | awk '{print $7; exit}' 2>/dev/null || echo "127.0.0.1")

# Запуск сервера
echo "Запуск сервера на http://$LOCAL_IP:8000"
echo "Для доступа из приложения используйте: http://$LOCAL_IP:8000"

python3 main.py

