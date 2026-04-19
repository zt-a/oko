# OKO 👁️

**Simple, zero-config error tracking for Python**

OKO — лёгкая библиотека для отслеживания ошибок и логов в Python-приложениях.
Ориентирована на **solo разработчиков, небольшие проекты и стартапы**.

> Установил → подключил → сразу получаешь уведомления об ошибках.

---

# 🚀 Быстрый старт

```bash
pip install oko
```

```python
import oko

oko.init()
```

Готово ✅
Теперь OKO автоматически собирает ошибки и логи.

---

# ⚡ Поддержка ASGI и WSGI

OKO — framework-agnostic инструмент и работает с любыми Python приложениями.

---

## 🟢 ASGI (async frameworks)

* FastAPI
* Starlette
* AIOHTTP
* Litestar
* Sanic

```python
from fastapi import FastAPI
import oko

app = FastAPI()
oko.init(app=app)
```

---

## 🔵 WSGI (sync frameworks)

* Django
* Flask

```python
from flask import Flask
import oko

app = Flask(__name__)
oko.init(app=app)
```

---

# 📲 Telegram уведомления

```python
oko.init(
    telegram_token="YOUR_BOT_TOKEN",
    telegram_chat_id="YOUR_CHAT_ID"
)
```

---

# 🧠 Как это работает

```text
┌───────────────┬────────────────┬────────────────┐
↓               ↓                ↓
Storage       Connectors      Dashboard
(SQLite)      (Telegram)      (Read-only UI)
---

# 🧱 Архитектура OKO (5 слоёв)

OKO построен как event-driven система с 5 слоями:

---

## 1️⃣ API Layer

Точка входа:

```python
oko.init()
```

Отвечает за:

* конфигурацию
* сборку системы
* подключение компонентов

---

## 2️⃣ Adapter Layer

Отвечает за интеграцию с фреймворками:

* FastAPI middleware
* Flask/Django WSGI middleware
* logging / loguru handler

Функция:

> превратить exception/log → Event

---

## 3️⃣ Core Layer

Сердце системы:

* очередь событий
* worker
* управление жизненным циклом

Функция:

> принять event → обработать → отправить дальше

---

## 4️⃣ Pipeline Layer

Обработка событий:

* deduplication (убрать дубликаты ошибок)
* grouping (объединение одинаковых ошибок)
* rate limiting
* enrichment (контекст запроса)

Функция:

> Event → улучшенный Event

---

## 5️⃣ Connectors Layer

Выход системы (side effects):
Connectors Layer отвечает только за outbound delivery:

* Telegram уведомления
* Webhooks
* future integrations (Discord, Slack)

❌ НЕ включает Dashboard

Функция:

> доставить результат наружу

---
# 👁️ Dashboard Layer (Observation System)
### Dashboard — отдельный слой наблюдения за системой.

* ✅ Он НЕ участвует в обработке событий.
* ✅ Он только читает данные из Storage.

Функции:
* ✅ просмотр ошибок
* ✅ фильтрация
* ✅ поиск
* ✅ stack trace viewer
* ✅ статистика

> Поток данных:
Storage → Dashboard (read-only)

* ✅ ❌ Dashboard НЕ:
* ✅ не отправляет события
* ✅ не влияет на Core
* ✅ не участвует в Pipeline
* ✅ не является Connector

---

# 📦 Возможности

* ✅ ASGI & WSGI поддержка
* ✅ Middleware интеграция
* ✅ Logging / Loguru support
* ✅ Telegram уведомления
* ✅ SQLite storage (без установки)
* ✅ Zero-config запуск
* ✅ Расширяемая архитектура

---

# 🔌 Расширяемость

OKO можно расширять через интерфейсы.

---

## 📨 Custom Connector (Notifier)

```python
from oko.core.interfaces import BaseConnector

class MyConnector(BaseConnector):
    async def send(self, event):
        print(event.message)
```

```python
oko.init(connector=MyConnector())
```

---

## 💾 Custom Storage

```python
from oko.core.interfaces import BaseStorage

class MyStorage(BaseStorage):
    async def save(self, event):
        print("Saved:", event.message)
```

```python
oko.init(storage=MyStorage())
```

---

## 🔧 Custom Adapter

```python
from oko.adapters.base import BaseAdapter

class MyAdapter(BaseAdapter):
    def install(self, app, core):
        pass
```

---

# 🧾 Работа с событиями вручную

```python
core = oko.get_core()

core.capture_log("Something happened")

try:
    1 / 0
except Exception as e:
    core.capture_exception(e)
```

---

# 🗃 Storage

По умолчанию используется SQLite:

```
oko.db
```

Особенности:

* не требует установки
* работает локально
* быстрый старт

---

# ⚙️ Производительность

OKO использует:

* `queue.Queue`
* background worker
* batching
* rate limiting

👉 не блокирует приложение

---

# ⚠️ Ограничения

OKO — не enterprise система:

* ❌ нет distributed queue
* ❌ нет guaranteed delivery
* ❌ не для high-load систем

---

# 🎯 Для кого это

* solo разработчики
* небольшие стартапы
* MVP
* pet projects

---

# ❌ Для кого НЕ подходит

* enterprise системы
* high-load инфраструктура

---

# 🛠 Roadmap

* [x] ASGI / WSGI support
* [x] FastAPI integration
* [x] Telegram connector
* [x] SQLite storage
* [ ] Django / Flask improvements
* [ ] Dashboard UI
* [ ] Advanced grouping system
* [ ] Rate limiting improvements

---

# 🤝 Contributing

PRs welcome.

Можно добавлять:

* новые connectors
* adapters
* pipeline processors

---

# 📄 License

MIT

---

# 💡 Философия проекта

> Простота использования важнее внутренней сложности

OKO может становиться сложным внутри,
но для пользователя всегда остаётся:

```python
import oko
oko.init()
```

OKO теперь состоит из двух подсистем:

⚙️ Processing System
Adapter → Core → Pipeline → Storage + Connectors

👁 Observation System
Storage → Dashboard
