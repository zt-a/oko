# PROJECT_STRUCTURE.md

````md id="oko_struct_v2"
# OKO Project Structure 👁️

**Черновая структура проекта (MVP → growth ready)**

---

# 🧠 1. Общая идея структуры

Проект разделён по слоям архитектуры:

* API (точка входа)
* Adapters (фреймворки)
* Core (ядро системы)
* Pipeline (обработка событий)
* Connectors (выходные интеграции)
* Storage (сохранение данных)
* Dashboard (слой наблюдения / UI)

---

# 📁 2. Структура проекта

```text
oko/
│
├── oko/
│   │
│   ├── api/                 # публичный интерфейс (oko.init)
│   │   ├── __init__.py
│   │   └── builder.py
│   │
│   ├── core/               # ядро системы
│   │   ├── __init__.py
│   │   ├── engine.py       # core логика
│   │   ├── queue.py        # очередь событий
│   │   ├── worker.py       # background worker
│   │   └── event.py       # OkoEvent модель
│   │
│   ├── adapters/           # интеграции с фреймворками
│   │   ├── base.py
│   │   ├── fastapi.py
│   │   ├── flask.py
│   │   ├── django.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── pipeline/           # обработка событий
│   │   ├── processor.py
│   │   ├── deduplication.py
│   │   ├── grouping.py
│   │   ├── enrichment.py
│   │   └── rate_limit.py
│   │
│   ├── connectors/         # внешние системы (output)
│   │   ├── base.py
│   │   ├── telegram.py
│   │   └── webhook.py
│   │
│   ├── storage/            # сохранение событий
│   │   ├── base.py
│   │   └── sqlite.py
│   │
│   ├── dashboard/          # 👁️ слой наблюдения (READ ONLY)
│   │   │
│   │   ├── core/           # логика запросов (framework agnostic)
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── adapters/      # HTTP адаптеры под фреймворки
│   │   │   ├── fastapi.py
│   │   │   ├── flask.py
│   │   │   ├── django.py
│   │   │   └── starlette.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── config/             # конфигурация
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── utils/              # утилиты
│   │   ├── logger.py
│   │   └── time.py
│   │
│   └── __init__.py        # public API
│
├── tests/
├── examples/
├── docs/
│
├── pyproject.toml
├── README.md
└── LICENSE
````

---

# 🧠 3. Принципы структуры (обновлено)

## ✔ независимость слоёв

* adapters не знают core internals
* core не знает frameworks
* pipeline не делает I/O
* connectors не управляют логикой
* dashboard не влияет на систему (READ ONLY)

---

## ✔ event-driven core

```text
Event → Core → Pipeline → Output
                     ↓
                Dashboard (read-only)
```

---

## ✔ разделение потоков

### Processing flow:

* Adapter
* Core
* Pipeline
* Storage
* Connectors

### Observation flow:

* Storage → Dashboard

---

# ⚙️ 4. API слой (oko.init)

без изменений

---

# 🧱 5. Core слой

без изменений

---

# 🔌 6. Adapters

без изменений

---

# 🔁 7. Pipeline

без изменений

---

# 📡 8. Connectors

без изменений

---

# 💾 9. Storage

без изменений

---

# 👁️ 10. Dashboard (новый слой)

Dashboard — это **read-only система наблюдения**.

## функции:

* чтение данных из Storage
* фильтрация ошибок
* поиск по stack trace
* группировка ошибок
* статистика

## ❌ запрещено:

* писать в Core
* вызывать Pipeline
* отправлять события
* изменять данные

## поток:

```text
Storage → Dashboard
```

---

# 🧭 11. Важное правило (обновлено)

> структура может меняться, но разделение на Processing и Observation — нет

---

# 🚀 12. Эволюция проекта

Теперь система разделена на 2 подсистемы:

## ⚙️ Processing System

* Adapter
* Core
* Pipeline
* Storage
* Connectors

## 👁 Observation System

* Dashboard

---

# 🔚 Итог

Теперь архитектура OKO стала:

* ближе к реальным observability системам
* расширяемой по UI
* чисто разделённой на read/write зоны

```