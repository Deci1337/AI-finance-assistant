#!/bin/bash
# Скрипт для запуска Gemini прокси сервера

export GEMINI_API_KEY="AIzaSyCzNvvW3Hxw7LAive8vD8adn4nt-Sh4yT0"
export PORT=8080

echo "Запуск Gemini прокси сервера..."
echo "API ключ: ${GEMINI_API_KEY:0:20}..."
echo "Порт: $PORT"
echo "URL: http://localhost:$PORT/v1"
echo ""

npm start

