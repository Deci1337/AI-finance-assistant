# Быстрый старт - Развертывание Gemini Proxy на Vercel

Согласно [инструкции на Habr](https://habr.com/ru/articles/798123/), для регионов вне поддерживаемых рекомендуется использовать **Vercel**.

## Вариант 1: Развертывание через кнопку (самый простой)

1. Перейдите по ссылке: https://vercel.com/new/clone?repository-url=https://github.com/PublicAffairs/openai-gemini
2. Авторизуйтесь в Vercel (можно через GitHub)
3. Нажмите "Deploy"
4. После развертывания:
   - Откройте проект на Vercel
   - Settings → Environment Variables
   - Добавьте: `GEMINI_API_KEY` = ваш API ключ Gemini
   - Сохраните и перезапустите deployment

## Вариант 2: Развертывание через CLI

```bash
# Установите Vercel CLI
npm i -g vercel

# Войдите в Vercel
vercel login

# Перейдите в папку прокси
cd gemini-proxy

# Разверните проект
vercel deploy

# Установите переменную окружения
vercel env add GEMINI_API_KEY
# Введите ваш API ключ когда попросит
```

## После развертывания

Вы получите URL вида: `https://your-project-name.vercel.app`

Используйте его в формате: `https://your-project-name.vercel.app/v1`

### Обновление backend

В `backend/gemini_integration.py` или через переменные окружения:

```python
GEMINI_PROXY_URL = "https://your-project-name.vercel.app/v1"
```

Или через переменную окружения:
```bash
export GEMINI_PROXY_URL="https://your-project-name.vercel.app/v1"
```

## Локальная разработка

Для локальной разработки с Vercel:
```bash
cd gemini-proxy
vercel dev
```

## Проверка работы

```bash
curl https://your-project-name.vercel.app/v1/models \
  -H "Authorization: Bearer YOUR_GEMINI_API_KEY"
```

## Модели

- По умолчанию используется `gemini-flash-latest` для chat/completions
- Если имя модели начинается с "gemini-", используется указанная модель
- Для веб-поиска добавьте ":search" к имени модели (например: `gemini-2.5-flash:search`)

## Преимущества Vercel

✅ Работает в регионах вне поддерживаемых Gemini API  
✅ Бесплатный тариф с щедрыми лимитами  
✅ Автоматическое развертывание при push в GitHub  
✅ Edge runtime для быстрой работы  
✅ Не требует обслуживания сервера

