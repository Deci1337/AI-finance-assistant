# Инструкция по развертыванию Gemini Proxy на Vercel

Согласно [инструкции на Habr](https://habr.com/ru/articles/798123/), для регионов вне поддерживаемых рекомендуется использовать Vercel.

## Быстрое развертывание через кнопку

1. Перейдите по ссылке: https://vercel.com/new/clone?repository-url=https://github.com/PublicAffairs/openai-gemini&repository-name=my-openai-gemini
2. Следуйте инструкциям на экране
3. При развертывании добавьте переменную окружения:
   - `GEMINI_API_KEY` = ваш API ключ Gemini

## Развертывание через CLI

1. Установите Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Войдите в Vercel:
   ```bash
   vercel login
   ```

3. Перейдите в папку прокси:
   ```bash
   cd gemini-proxy
   ```

4. Разверните проект:
   ```bash
   vercel deploy
   ```

5. Установите переменную окружения `GEMINI_API_KEY` в настройках проекта на Vercel

## Локальная разработка

Для локальной разработки используйте:
```bash
cd gemini-proxy
vercel dev
```

## Использование после развертывания

После развертывания вы получите URL вида: `https://your-project.vercel.app`

Используйте его в формате: `https://your-project.vercel.app/v1`

Обновите переменную окружения в backend:
```bash
export GEMINI_PROXY_URL="https://your-project.vercel.app/v1"
```

## Модели

- Если имя модели начинается с "gemini-", "gemma-", "learnlm-" или "models/", используется указанная модель
- Иначе по умолчанию используется `gemini-flash-latest` для chat/completions
- Для embeddings по умолчанию: `gemini-embedding-001`

## Встроенные инструменты

Для использования веб-поиска добавьте ":search" к имени модели:
- Например: `gemini-2.5-flash:search`

