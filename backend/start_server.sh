#!/bin/bash
# Скрипт для автоматического запуска backend сервера
# Использование: ./start_server.sh

cd "$(dirname "$0")"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не найден. Установите Python3."
    exit 1
fi

# Проверка зависимостей
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Установка зависимостей
echo "Проверка зависимостей..."
pip install -q -r requirements.txt

# Определение IP адреса для доступа из сети
HOST="0.0.0.0"
PORT=8000

# Запуск сервера
echo "Запуск сервера на http://$HOST:$PORT"
python3 main.py

