#!/data/data/com.termux/files/usr/bin/bash
# Скрипт автозапуска для Termux:Boot
# Разместите в ~/.termux/boot/termux_boot.sh

# Ожидание загрузки системы
sleep 5

# Переход в директорию проекта
cd ~/AI-finance-assistant/backend 2>/dev/null || cd ~/backend 2>/dev/null || exit 1

# Запуск backend сервера в фоне
nohup python3 main.py > ~/backend.log 2>&1 &

# Сохранение PID для возможности остановки
echo $! > ~/backend.pid

