# Руководство по автоматическому запуску Backend

## Как это работает

При запуске приложения автоматически выполняется попытка запустить backend сервер. Это работает на всех платформах.

## Поддерживаемые платформы

### ✅ Windows
- Автоматически запускает Python backend при старте приложения
- Ищет Python в системе
- Запускает `python main.py` из папки backend

### ✅ Android
- Пытается запустить через Termux (если установлен)
- Ищет Python в стандартных путях Android
- Использует `127.0.0.1:8000` для подключения

### ✅ iOS / macOS
- Запускает Python backend локально
- Использует `localhost:8000` для подключения

## Настройка для Android (Termux)

1. **Установите Termux** из F-Droid или Google Play

2. **Установите Python и зависимости:**
```bash
pkg update && pkg upgrade
pkg install python git -y
cd ~
git clone https://github.com/Deci1337/AI-finance-assistant.git
cd AI-finance-assistant/backend
pip install -r requirements.txt
```

3. **Приложение автоматически найдет backend** если он находится в:
   - `/data/data/com.termux/files/home/AI-finance-assistant/backend`
   - `/data/data/com.termux/files/home/backend`

## Автозапуск при загрузке Android

Для автоматического запуска backend при включении устройства:

1. **Установите Termux:Boot** из F-Droid

2. **Создайте скрипт автозапуска:**
```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-backend.sh
```

3. **Добавьте содержимое:**
```bash
#!/data/data/com.termux/files/usr/bin/bash
sleep 5
cd ~/AI-finance-assistant/backend
nohup python3 main.py > ~/backend.log 2>&1 &
```

4. **Сделайте исполняемым:**
```bash
chmod +x ~/.termux/boot/start-backend.sh
```

5. **При следующей перезагрузке** backend запустится автоматически

## Проверка работы

После запуска приложения проверьте логи:
- Windows: Debug Output в Visual Studio
- Android: `adb logcat | grep Backend`
- Или проверьте доступность: `curl http://127.0.0.1:8000/health`

## Ручная настройка API URL

Если автоматический запуск не работает, можно настроить URL вручную:

В `FinanceService.cs` используйте Preferences:
```csharp
Preferences.Set("api_base_url", "http://192.168.1.100:8000");
```

## Альтернативные варианты

1. **Облачный сервер** (Render.com, Railway.app) - самый надежный вариант
2. **Локальный сервер на ПК** - для разработки
3. **Встроенный сервер** - требует переработки архитектуры

## Отладка

Если backend не запускается автоматически:

1. Проверьте наличие Python в системе
2. Проверьте наличие файла `main.py` в папке backend
3. Проверьте логи приложения
4. Попробуйте запустить backend вручную для проверки

## Остановка backend

Backend автоматически останавливается при закрытии приложения на всех платформах.

