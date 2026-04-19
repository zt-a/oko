---

# 📌 Обновлённая версия ARCHITECTURE.md (с Dashboard)

````md
# OKO Architecture 👁️

**Event-driven error tracking system**

OKO — это lightweight event-driven система для перехвата ошибок, логов и их доставки в внешние системы (Connectors + Storage + Dashboard).

---

# 🧠 1. Общая архитектура

OKO построен как pipeline обработки событий.

```text
        ┌──────────────┐
        │  APPLICATION │
        │ FastAPI/DJ   │
        └──────┬───────┘
               ↓
        ┌──────────────┐
        │  ADAPTER     │
        │ middleware   │
        └──────┬───────┘
               ↓
        ┌──────────────┐
        │    CORE      │
        │ queue/worker │
        └──────┬───────┘
               ↓
        ┌──────────────┐
        │  PIPELINE    │
        │ processing   │
        └──────┬───────┘
               ↓
   ┌───────────┼──────────────┐
   ↓           ↓              ↓
┌──────────┐ ┌──────────┐ ┌──────────────┐
│ CONNECTORS│ │ STORAGE  │ │ DASHBOARD    │
│ Telegram  │ │ SQLite   │ │ UI Layer     │
└──────────┘ └──────────┘ └──────────────┘
````

---

# 🔁 2. Data Flow (главный поток системы)

```text
Exception / Log
        ↓
Adapter Layer
        ↓
Core (Event Queue)
        ↓
Pipeline Processing
        ↓
┌──────────────┬──────────────┬──────────────┐
↓              ↓              ↓
Storage     Connectors     Dashboard
(SQLite)    (Telegram)     (Read-only UI)
```

---

# 📦 3. Слои системы

---

## 3.1 API Layer

📌 точка входа

```python
oko.init(...)
```

### Ответственность:

* конфигурация системы
* сборка зависимостей
* регистрация адаптеров

❌ не содержит логики обработки

---

## 3.2 Adapter Layer

📌 входной слой интеграции

### Поддержка:

* ASGI (FastAPI, Starlette, AIOHTTP, Litestar, Sanic)
* WSGI (Django, Flask)
* logging / loguru handlers

### Функции:

* перехват ошибок
* преобразование в Event
* передача в Core

```text
Framework → Exception → Event → Core
```

❌ запрещено:

* доступ к DB
* отправка Telegram
* бизнес логика

---

## 3.3 Core Layer

📌 ядро системы

### Функции:

* очередь событий (queue.Queue)
* background worker
* orchestration pipeline
* управление lifecycle событий

```text
capture() → Queue → Worker → Pipeline
```

❌ запрещено:

* знать фреймворки
* знать Telegram / DB
* выполнять I/O напрямую

---

## 3.4 Pipeline Layer

📌 обработка событий

### Функции:

* deduplication
* grouping ошибок
* rate limiting
* enrichment (context injection)
* normalization

```text
Event → Processors → Enhanced Event
```

❌ запрещено:

* HTTP calls
* DB writes
* Telegram calls

---

# 📤 3.5 Output Layer

---

## 3.5.1 Connectors Layer

📌 внешние доставки (push model)

* Telegram
* Webhooks
* future integrations (Discord, Slack)

```text
Event → Telegram / Webhook / API
```

---

## 3.5.2 Storage Layer

📌 хранение событий (source of truth)

Default: SQLite

```text
Event → SQLite DB
```

---

# 👁️ 3.6 Dashboard Layer (OBSERVATION LAYER)

📌 слой наблюдения и чтения данных

Dashboard — это **read-only система визуализации ошибок**

---

### Функции:

* чтение данных из Storage
* отображение ошибок
* фильтрация и поиск
* просмотр stack trace
* группировка ошибок (UI level)

---

### Поток данных:

```text
Storage → Dashboard (READ ONLY)
```

---

### ❌ Dashboard НЕ:

* не отправляет события
* не влияет на Core
* не участвует в pipeline
* не является connector

---

### 📊 Тип реализации:

Dashboard может иметь разные адаптеры:

* FastAPI Router
* Django views
* Flask Blueprint
* Starlette routes

---

# 🧾 4. Event Model (ядро контракта)

```python
OkoEvent(
    type="error",
    message="string",
    stack="string",
    context=dict,
    timestamp=float
)
```

---

# ⚙️ 5. Runtime Architecture

## Worker model

```text
Main Thread
     ↓
Queue (in-memory)
     ↓
Background Worker
     ↓
Pipeline → Output (Storage / Connectors)
```

---

## Concurrency model

* single-process
* thread-based worker
* async-safe connectors

---

# 🧠 6. Design Principles

## 6.1 Unidirectional flow

```text
Adapter → Core → Pipeline → Output
                    ↓
                Dashboard (read-only)
```

---

## 6.2 Dependency Inversion

Core не зависит от:

* frameworks
* storage implementations
* connectors
* dashboard

---

## 6.3 Event-first design

Любое взаимодействие = Event

---

# ⚡ 7. Performance Model

OKO оптимизирован для:

* low/medium traffic apps
* developer tooling
* debugging workloads

---

# 💾 8. Storage Design

Default: SQLite

* WAL mode
* batch inserts
* async-safe writes

---

# 📲 9. Connector Design

* async compatible
* rate limit aware
* deduplication support

---

# 👁️ 10. Dashboard Design Rules

Dashboard обязан:

* работать только через Storage
* не вызывать Core
* не влиять на pipeline
* быть replaceable (plug-in UI layer)

---

# 🔌 11. Extension Model

| Component | Extension point      |
| --------- | -------------------- |
| Adapter   | BaseAdapter          |
| Pipeline  | Processor            |
| Storage   | BaseStorage          |
| Connector | BaseConnector        |
| Dashboard | BaseDashboardAdapter |

---

# 🚫 12. Hard Constraints

* Core не знает Dashboard
* Dashboard не знает Core
* Connectors не пишут в Storage
* Pipeline не делает I/O
* Adapter не содержит бизнес логики

---

# 🧭 13. System Philosophy

> OKO is a layered event pipeline with a separate observation layer.

External API:

```python
import oko
oko.init()
```

Internal system:

* layered
* event-driven
* extensible
* deterministic flow

---

# 📈 14. Future extensions

* Django / Flask dashboard adapters
* Error grouping engine
* Advanced analytics pipeline
* Plugin system

```

---

# 🔥 Что ты сейчас получил

Ты перешёл на следующий уровень архитектуры:

### Было:
- 5 слоёв

### Стало:
- 5 слоёв + 1 наблюдательный слой

```

Core System:
Adapter → Core → Pipeline → Output

Side System:
Storage → Dashboard

```

---
