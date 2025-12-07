# Настройка Backend для запуска на мобильном устройстве

## Вариант 1: Запуск через Termux (Android)

### Шаги установки:

1. **Установите Termux из Google Play Store или F-Droid**

2. **Откройте Termux и выполните:**
```bash
# Обновление пакетов
pkg update && pkg upgrade

# Установка Python и Git
pkg install python git -y

# Клонирование репозитория (или скопируйте файлы вручную)
cd ~
git clone https://github.com/Deci1337/AI-finance-assistant.git
cd AI-finance-assistant/backend

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python3 main.py
```

3. **Получите IP адрес устройства:**
```bash
ip route get 1.1.1.1 | awk '{print $7; exit}'
```

4. **Обновите API_BASE_URL в приложении:**
   - Используйте IP адрес вместо localhost
   - Например: `http://192.168.1.100:8000`

### Автозапуск при загрузке:

Создайте файл `~/.termux/boot/start-backend.sh`:
```bash
#!/data/data/com.termux/files/usr/bin/bash
cd ~/AI-finance-assistant/backend
python3 main.py &
```

Сделайте исполняемым:
```bash
chmod +x ~/.termux/boot/start-backend.sh
```

## Вариант 2: Использование облачного сервера (Рекомендуется)

### Варианты облачных платформ:

1. **Render.com** (бесплатный тариф)
2. **Railway.app** (бесплатный тариф)
3. **Heroku** (платный)
4. **PythonAnywhere** (бесплатный тариф)

### Настройка на Render.com:

1. Создайте аккаунт на render.com
2. Подключите GitHub репозиторий
3. Создайте новый Web Service
4. Укажите:
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && python main.py`
5. Получите URL (например: `https://your-app.onrender.com`)
6. Обновите API_BASE_URL в приложении

## Вариант 3: Локальный сервер на компьютере + доступ через сеть

### На компьютере:

1. **Запустите backend:**
```bash
cd backend
python3 main.py
```

2. **Узнайте IP адрес компьютера:**
   - Windows: `ipconfig` (IPv4 адрес)
   - Mac/Linux: `ifconfig` или `ip addr`

3. **Убедитесь, что порт 8000 открыт в файрволе**

### В мобильном приложении:

Измените `API_BASE_URL` в `FinanceService.cs`:
```csharp
private const string API_BASE_URL = "http://192.168.1.XXX:8000"; // IP вашего компьютера
```

## Вариант 4: Встроенный сервер в MAUI приложении

Можно встроить Python backend прямо в Android приложение используя:
- **Chaquopy** (плагин для Android)
- **BeeWare** (Python для мобильных приложений)

Это более сложный вариант, требующий переработки архитектуры.

## Рекомендации

**Для разработки:** Используйте Вариант 3 (локальный сервер на компьютере)

**Для продакшена:** Используйте Вариант 2 (облачный сервер)

**Для автономной работы:** Используйте Вариант 1 (Termux) или Вариант 4 (встроенный сервер)

## Настройка автоматического запуска в Termux

1. Установите Termux:Boot из F-Droid
2. Создайте скрипт автозапуска (см. выше)
3. При включении устройства Termux автоматически запустит backend

## Проверка работы

После запуска backend проверьте доступность:
```bash
curl http://localhost:8000/health
# или с другого устройства в той же сети:
curl http://IP_АДРЕС:8000/health
```

