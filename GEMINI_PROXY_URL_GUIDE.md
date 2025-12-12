# Где взять GEMINI_PROXY_URL

## Вариант 1: Локальный прокси (уже работает) ✅

Если прокси запущен локально на порту 8080, используйте:

```
http://localhost:8080/v1
```

**Это уже настроено по умолчанию** в `backend/gemini_integration.py`

### Проверка работы локального прокси:

```bash
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer YOUR_GEMINI_API_KEY"
```

Если прокси не запущен, запустите его:
```bash
cd gemini-proxy
npm start
```

---

## Вариант 2: Vercel (рекомендуется для production)

### Шаг 1: Разверните прокси на Vercel

**Способ А: Через кнопку (самый простой)**
1. Перейдите: https://vercel.com/new/clone?repository-url=https://github.com/PublicAffairs/openai-gemini
2. Авторизуйтесь в Vercel
3. Нажмите "Deploy"
4. После развертывания вы получите URL вида: `https://your-project-name.vercel.app`

**Способ Б: Через CLI**
```bash
cd gemini-proxy
npm i -g vercel
vercel login
vercel deploy
```

### Шаг 2: Добавьте переменную окружения на Vercel

1. Откройте проект на Vercel
2. Settings → Environment Variables
3. Добавьте: `GEMINI_API_KEY` = ваш API ключ Gemini
4. Сохраните и перезапустите deployment

### Шаг 3: Используйте URL в формате:

```
https://your-project-name.vercel.app/v1
```

Замените `your-project-name` на имя вашего проекта на Vercel.

---

## Как установить GEMINI_PROXY_URL

### Способ 1: Через переменную окружения (рекомендуется)

```bash
# Для локального прокси
export GEMINI_PROXY_URL="http://localhost:8080/v1"

# Для Vercel
export GEMINI_PROXY_URL="https://your-project-name.vercel.app/v1"
```

### Способ 2: В файле gemini_integration.py

Откройте `backend/gemini_integration.py` и измените строку 18:

```python
# Для локального прокси
GEMINI_PROXY_URL = os.getenv("GEMINI_PROXY_URL", "http://localhost:8080/v1")

# Для Vercel (замените your-project-name на ваш проект)
GEMINI_PROXY_URL = os.getenv("GEMINI_PROXY_URL", "https://your-project-name.vercel.app/v1")
```

### Способ 3: В .env файле (если используете)

Создайте файл `.env` в папке `backend/`:

```bash
# Для локального прокси
GEMINI_PROXY_URL=http://localhost:8080/v1

# Для Vercel
GEMINI_PROXY_URL=https://your-project-name.vercel.app/v1
```

---

## Как узнать URL вашего Vercel проекта

1. Войдите на https://vercel.com
2. Откройте ваш проект
3. В разделе "Domains" или на главной странице проекта будет указан URL
4. Обычно формат: `https://[имя-проекта].vercel.app`

---

## Рекомендации

- **Для разработки**: используйте локальный прокси (`http://localhost:8080/v1`)
- **Для production**: используйте Vercel (`https://your-project.vercel.app/v1`)
- **Для регионов вне поддерживаемых**: обязательно используйте Vercel

---

## Проверка работы

После настройки проверьте работу:

```bash
cd backend
python3 test_gemini.py
```

Или напрямую:

```bash
curl https://your-project-name.vercel.app/v1/models \
  -H "Authorization: Bearer YOUR_GEMINI_API_KEY"
```

Должен вернуться список доступных моделей.

