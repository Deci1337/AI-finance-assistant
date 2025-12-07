# Backend - AI Finance Assistant

## Настройка окружения

### 1. Активация виртуального окружения

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
```

Или если политика выполнения уже настроена:
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Установка зависимостей

После активации виртуального окружения:
```bash
pip install -r requirements.txt
```

### 3. Добавление новых зависимостей

После установки нового пакета:
```bash
pip freeze > requirements.txt
```

### 4. Запуск приложения

```bash
python main.py
```

### 5. Деактивация окружения

```bash
deactivate
```

