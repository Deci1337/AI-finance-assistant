# Пошаговая инструкция по развертыванию на Vercel

## Шаг 1: Подготовка

1. Убедитесь, что у вас есть аккаунт на Vercel (https://vercel.com)
2. Убедитесь, что у вас есть API ключ Gemini (https://makersuite.google.com/app/apikey)

## Шаг 2: Развертывание через веб-интерфейс (рекомендуется)

1. Перейдите на https://vercel.com/new/clone?repository-url=https://github.com/PublicAffairs/openai-gemini
2. Авторизуйтесь в Vercel
3. Выберите ваш GitHub аккаунт (если нужно, создайте форк репозитория)
4. Нажмите "Deploy"
5. После развертывания перейдите в настройки проекта → Environment Variables
6. Добавьте переменную:
   - Key: `GEMINI_API_KEY`
   - Value: ваш API ключ Gemini
7. Сохраните и перезапустите deployment

## Шаг 3: Развертывание через CLI

### Установка Vercel CLI

```bash
npm i -g vercel
```

### Вход в Vercel

```bash
vercel login
```

### Развертывание

```bash
cd gemini-proxy
vercel deploy
```

При первом развертывании:
- Выберите "Set up and deploy"
- Выберите проект (или создайте новый)
- Подтвердите настройки

### Установка переменных окружения

```bash
vercel env add GEMINI_API_KEY
# Введите ваш API ключ когда попросит
```

Или через веб-интерфейс:
1. Откройте проект на Vercel
2. Settings → Environment Variables
3. Добавьте `GEMINI_API_KEY` с вашим ключом

## Шаг 4: Использование

После развертывания вы получите URL вида: `https://your-project-name.vercel.app`

Используйте его в формате: `https://your-project-name.vercel.app/v1`

### Обновление конфигурации backend

В файле `.env` или через переменные окружения установите:

```bash
export GEMINI_PROXY_URL="https://your-project-name.vercel.app/v1"
```

Или в `backend/gemini_integration.py` измените:
```python
GEMINI_PROXY_URL = os.getenv("GEMINI_PROXY_URL", "https://your-project-name.vercel.app/v1")
```

## Локальная разработка

Для локальной разработки с Vercel:

```bash
cd gemini-proxy
vercel dev
```

Это запустит локальный сервер с теми же настройками, что и на Vercel.

## Проверка работы

После развертывания проверьте:

```bash
curl https://your-project-name.vercel.app/v1/models \
  -H "Authorization: Bearer YOUR_GEMINI_API_KEY"
```

Должен вернуться список доступных моделей.

## Преимущества Vercel

- ✅ Работает в регионах вне поддерживаемых Gemini API
- ✅ Бесплатный тариф с щедрыми лимитами
- ✅ Автоматическое развертывание при push в GitHub
- ✅ Edge runtime для быстрой работы
- ✅ Не требует обслуживания сервера

## Ограничения

- Edge Functions имеют ограничения по времени выполнения
- Бесплатный тариф имеет лимиты на количество запросов

## Альтернативы

Если Vercel не подходит, можно использовать:
- **Netlify** (но не edge functions для регионов вне поддерживаемых)
- **Cloudflare Workers** (бесплатный тариф)
- **Deno Deploy**

