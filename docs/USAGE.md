# OKO 📖 Руководство по эксплуатации

> Полное руководство по использованию OKO — от установки до кастомизации

---

## Содержание

1. [Установка](#1-установка)
2. [Быстрый старт](#2-быстрый-старт)
3. [Подключение к фреймворкам](#3-подключение-к-фреймворкам)
4. [Конфигурация](#4-конфигурация)
5. [Telegram уведомления](#5-telegram-уведомления)
6. [Dashboard](#6-dashboard)
7. [Ручной захват событий](#7-ручной-захват-событий)
8. [Logging интеграция](#8-logging-интеграция)
9. [Кастомизация](#9-кастомизация)
10. [Хранение данных](#10-хранение-данных)
11. [Устранение проблем](#11-устранение-проблем)

---

## 1. Установка

```bash
pip install oko
```

Для полной функциональности (с Dashboard):

```bash
pip install oko[fastapi,flask]
```

---

## 2. Быстрый старт

Минимальная конфигурация — OKO начнёт записывать ошибки в SQLite:

```python
import oko

oko.init()
```

Теперь OKO автоматически:
- перехватывает исключения
- записывает в `oko.db`

---

## 3. Подключение к фреймворкам

### FastAPI / Starlette / AIOHTTP (ASGI)

```python
import oko
from fastapi import FastAPI

# 1. Инициализация до создания app
engine = oko.init(
    telegram_token="YOUR_BOT_TOKEN",  # Получить у @BotFather
    telegram_chat_id="YOUR_CHAT_ID",   # Получить @userinfobot
    project="my-api",
    environment="production",
)

# 2. Создаём app
app = FastAPI()

# 3. Подключаем middleware
app.add_middleware(oko.ASGIMiddleware)
```

**Что перехватывает:** 400, 405, 500-504 (настраивается)

### Flask / Django (WSGI)

```python
import oko
from flask import Flask

# 1. Инициализация
engine = oko.init(
    telegram_token="...",
    telegram_chat_id="...",
    project="my-flask-app",
)

app = Flask(__name__)

# 2. Оборачиваем WSGI приложение
app.wsgi_app = oko.WSGIMiddleware(app.wsgi_app)
```

### Django (альтернатива)

```python
# В your_project/wsgi.py
import oko

engine = oko.init(...)

application = oko.WSGIMiddleware(get_wsgi_application())
```

---

## 4. Конфигурация

### Полный список параметров `oko.init()`

```python
oko.init(
    # --- Telegram ---
    telegram_token="...",      # Токен бота @BotFather
    telegram_chat_id="...",   # ID чата @userinfobot
    
    # --- Dashboard ---
    dashboard_url="https://myapp.com",  # Для ссылок на события
    
    # --- Storage ---
    storage=None,              # Кастомный storage
    db_path="oko.db",         # Путь к БД
    retention_days=7,          # Хранение дней
    
    # --- Connectors ---
    connector=None,          # Кастомный connector
    extra_connectors=[],       # Дополнительные connectors
    
    # --- Pipeline ---
    silence=900.0,           # Дубликаты: 15 минут молчания
    rate_limit_max=10.0,      # Макс. уведомлений
    rate_limit_refill=1.0,    # Восстановление токенов/сек
    
    # --- Enrichment ---
    project="myapp",         # Название проекта
    environment="dev",      # Окружение
    version="1.0.0",        # Версия
    
    # --- Logging ---
    capture_logs=False,       # Перехватывать logging.error()
    log_level=logging.ERROR,# Уровень для перехвата
    
    # --- Engine ---
    batch_size=10,          # Размер пачки
    poll_interval=1.0,      # Опрос очереди (сек)
)
```

### Параметры окружения

| Параметр | Тип | По умолчанию | Описание |
|---------|-----|-------------|-----------|
| `silence` | float | 900.0 | Секунды игнорирования дубликатов |
| `rate_limit_max` | float | 10.0 | Макс. уведомлений за раз |
| `retention_days` | int | 7 | Дней хранения в БД |
| `batch_size` | int | 10 | Событий за пачку |

---

## 5. Telegram уведомления

### Получение токена

1. Откройте @BotFather в Telegram
2. Создайте бота: `/newbot`
3. Скопируйте токен (формат: `123456:ABC-DEF...`)

### Получение chat_id

1. Откройте @userinfobot
2. Отправьте любое сообщение
3. Скопируйте ваш ID

### Пример

```python
engine = oko.init(
    telegram_token="",
    telegram_chat_id="",
    project="myapp",
    environment="production",
    silence=60,          # 1 минута молчания между повторами
    capture_logs=True,   # Перехватывать ERROR логи
)
```

### Формат уведомлений

```
👁 OKO ALERT — PRODUCTION

❌ *500* | POST `/api/users`

💬 _RuntimeError: User not found_

📦 *Project:* `myapp`
🕒 *Time:* 14:23:05

🔗 https://myapp.com/oko/42

Traceback (last 10 lines):
```python
...
```

---

## 6. Dashboard

### Подключение к FastAPI

```python
import oko
from fastapi import FastAPI

# Инициализация
engine = oko.init(
    telegram_token="...",
    telegram_chat_id="...",
    db_path="oko.db",
)

app = FastAPI()

# Подключаем Dashboard
app.include_router(oko.dashboard_router())
```

### Эндпоинты

| URL | Описание |
|-----|----------|
| `/oko/` | Список событий |
| `/oko/{id}` | Детальный просмотр |

### Параметры фильтрации

```
/oko/?type=error&limit=20&offset=0
```

- `type`: error, http_error, log
- `limit`: кол-во (макс 200)
- `offset`: для пагинации

---

## 7. Ручной захват событий

### Захват исключения

```python
import oko

# Вариант 1: через oko
try:
    risky_operation()
except Exception as e:
    oko.capture_exception(e)

# Вариант 2: с контекстом
try:
    risky_operation()
except Exception as e:
    oko.capture_exception(e, context={"user_id": 123})
```

### Захват лога

```python
# Уровни: debug, info, warning, error, critical
oko.capture_log("Payment failed", level="warning")
oko.capture_log("User logged in", context={"user_id": 42})
```

### Захват HTTP ошибки

```python
oko.capture_http_error(
    status_code=500,
    method="POST",
    path="/api/payment",
    context={"client_ip": request.client.host}
)
```

---

## 8. Logging интеграция

### Стандартный logging

```python
import logging
import oko

engine = oko.init(
    telegram_token="...",
    capture_logs=True,  # Автоматически
)
```

### Ручная установка

```python
import logging
import oko

engine = oko.init(
    telegram_token="...",
    capture_logs=False,
)

# Подключаем хендлер к конкретному логгеру
handler = oko.install_logging_handler(
    engine=engine,
    level=logging.ERROR,  # ERROR и выше
    logger_name="myapp",  # или None для root
)

# Удаление хендлера
logging.getLogger("myapp").removeHandler(handler)
```

### Loguru

```python
from loguru import logger
import oko

engine = oko.init(telegram_token="...")

logger.add(oko.loguru_sink(), level="ERROR")
```

---

## 9. Кастомизация

### Кастомный Connector

```python
import asyncio
from oko.connectors.base import BaseConnector
from oko.core.event import OkoEvent

class SlackConnector(BaseConnector):
    """Отправка уведомлений в Slack"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, event: OkoEvent) -> None:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                self.webhook_url,
                json={"text": f"🚨 {event.message}"}
            )

# Использование
oko.init(
    connector=SlackConnector("https://hooks.slack.com/..."),
)
```

### Кастомный Storage

```python
import json
from oko.storage.base import BaseStorage

class JsonFileStorage(BaseStorage):
    """Хранение в JSON файле"""
    
    def __init__(self, path: str = "events.json"):
        self.path = path
        self._events = []
    
    def save_batch(self, events) -> None:
        self._events.extend([
            {
                "type": e.type,
                "message": e.message,
                "timestamp": e.timestamp,
            }
            for e in events
        ])
        with open(self.path, "w") as f:
            json.dump(self._events, f, indent=2)
    
    def fetch(self, limit=100, offset=0, event_type=None):
        return self._events[offset:offset+limit]
    
    def count(self, event_type=None):
        return len(self._events)

# Использование
oko.init(storage=JsonFileStorage("my_events.json"))
```

### Кастомный Webhook Connector

```python
from oko.connectors.webhook import WebhookConnector

# Создание webhook connector
webhook = WebhookConnector(
    url="https://your-server.com/hook",
    headers={"Authorization": "Bearer secret"},
    method="POST",  # или PUT
)

# Добавление к OKO
oko.init(
    connector=TelegramConnector(...),
    extra_connectors=[webhook],  # Несколько connectors
)
```

### Кастомный Adapter

```python
from oko.adapters.base import BaseAdapter

class MyFrameworkAdapter(BaseAdapter):
    def install(self, app, engine):
        # Подключение к вашему фреймворку
        app.on_error(self._handle_error)
    
    def _handle_error(self, error, request):
        self.engine.capture_exception(error, context={
            "request": str(request)
        })
```

---

## 10. Хранение данных

### SQLite (по умолчанию)

- Файл: `oko.db`
- автоматически создаётся
- WAL mode включён
- автоматическая чистка старых записей

### Кастомный путь

```python
oko.init(db_path="/var/lib/oko/errors.db")
```

### In-memory (для тестов)

```python
from oko.storage.sqlite import SQLiteStorage

storage = SQLiteStorage(":memory:")
oko.init(storage=storage)
```

### Ручная работа с Storage

```python
import oko

# Получение storage
storage = oko.get_storage()

# Сохранение событий
from oko.core.event import OkoEvent

event = OkoEvent(
    type="error",
    message="Test error"
)
storage.save_batch([event])

# Чтение событий
events = storage.fetch(limit=10)
count = storage.count()

# Получить конкретное событие
event = storage.fetch_by_id(1)
```

---

## 11. Устранение проблем

### Ошибка: "OKO not initialized"

```python
# Вы должны сначала вызвать oko.init()
oko.init()
# Теперь можно использовать
oko.capture_log("test")
```

### Не приходят уведомления в Telegram

1. Проверьте токен и chat_id
2. Проверьте что бот имеет право писать вам
3. Убедитесь что `silence` не слишком большой

### Ошибки в Dashboard

1. Убедитесь что FastAPI установлен: `pip install fastapi jinja2`
2. Проверьте что storage инициализирован

### Медленная работа

- Уменьшите `poll_interval`: `poll_interval=0.1`
- Увеличьте `batch_size`: `batch_size=50`

### Утечка памяти при долгой работе

- Убедитесь что cleanup работает: `retention_days=7` (по умолчанию)
- Проверьте что `silence` не слишком большой — в памяти хранятся fingerprint'ы

### Тесты

```bash
# Запуск тестов
python -m pytest tests/ -v

# конкретный слой
python -m pytest tests/core/ -v
python -m pytest tests/pipeline/ -v
python -m pytest tests/connectors/ -v
```

---

## Примеры проектов

Смотрите в `examples/`:

- `fastapi_example.py` — FastAPI + Telegram
- `flask_examples.py` — Flask + Telegram
- `fastapi_logging_example.py` — FastAPI + Logging

---

## Часто задаваемые вопросы

**В: Нужно ли настраивать базу данных?**  
Н: Нет, SQLite работает из коробки.

**В: Можно ли использовать без Telegram?**  
О: Да, просто не передавайте `telegram_token` и `telegram_chat_id`.

**В: Как отключить Dashboard?**  
О: Не подключайте `dashboard_router()` к вашему app.

**В: Безопасно ли использовать в production?**  
О: Да, OKO использует `daemon` thread — умирает вместе с процессом.

**В: Что если фреймворк не поддерживается?**  
О: Используйте ручной захват: `oko.capture_exception(e)`

---

## Итог

Одна строка для старта:

```python
import oko
oko.init(telegram_token="...", telegram_chat_id="...")
```

Одна строка для middleware:

```python
# FastAPI
app.add_middleware(oko.ASGIMiddleware)

# Flask  
app.wsgi_app = oko.WSGIMiddleware(app.wsgi_app)
```