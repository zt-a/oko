# OKO RULES 👁️

**Strict Development Rules**

Этот документ описывает строгие правила разработки OKO.
Нарушение этих правил считается архитектурным дефектом.

---

# 🧠 1. Главный принцип

> OKO — это event-driven система с фиксированными слоями.
> Поток данных всегда однонаправленный.
## 📊 Observation separation rule

Processing system и Observation system всегда разделены.

* Processing = изменяет и перемещает события
* Observation = только читает данные

---

# ⚙️ 2. Архитектурный поток (ЗАКОН)

```text id="flow_core"
Adapter → Core → Pipeline → Connectors + Storage
```

## ❌ Запрещено:

* обратные зависимости
* обход Core
* прямые вызовы Connectors из Adapter
* запись в DB вне Storage layer

---

# 🧱 3. Core 5-layer architecture (PROCESSING SYSTEM)

## 1. API Layer

* только `oko.init()`
* сборка системы
* конфигурация

## 2. Adapter Layer

* перехват ошибок (ASGI / WSGI / logging)
* преобразование в Event
* передача в Core

❌ нельзя:

* писать в DB
* вызывать Telegram
* выполнять бизнес-логику

---

## 3. Core Layer

* управление очередью
* worker execution
* orchestration pipeline

❌ нельзя:

* знать FastAPI / Django / Flask
* знать Telegram / DB implementation

---

## 4. Pipeline Layer

* обработка событий
* deduplication
* grouping
* rate limiting
* enrichment

❌ нельзя:

* выполнять I/O (DB, HTTP)
* отправлять уведомления

---

## 5. Connectors Layer

* Telegram
* Webhooks
* future integrations

## Storage Layer (часть output side effects)

* SQLite (default)

❌ нельзя:

* изменять Core
* влиять на pipeline logic

---

---

## 👁️ 6. Observation System (Dashboard)

Dashboard — отдельная подсистема наблюдения (НЕ часть processing pipeline).

### Поток данных:

> Storage → Dashboard (read-only)

❌ Dashboard НЕ:
* не участвует в Core
* не вызывает Pipeline
* не отправляет события в Connectors
* не изменяет данные системы

✔ Dashboard может:
* читать Storage
* фильтровать события
* отображать stack traces
* строить статистику

---

# 📦 4. Event — единственный контракт

Все данные проходят через `Event`.

```python id="event_rule"
OkoEvent(
    type="error",
    message="string",
    stack="string",
    context={}
)
```

## ❌ Запрещено:

* передавать raw dict между слоями
* использовать “произвольные структуры”

---

# 🔁 5. Однонаправленный поток данных

```text id="flow_rule"
Adapter → Core → Pipeline → Connectors + Storage
                              ↓
                         Dashboard (read-only)
```

## ❌ Запрещено:

* Output → Core
* Pipeline → Adapter
* Storage → Pipeline

---

# ⚡ 6. Производительность (ОБЯЗАТЕЛЬНО)

## Core обязан:

* использовать `queue.Queue`
* работать через background worker
* НЕ блокировать request thread

## Connectors обязаны:

* быть async-friendly
* поддерживать rate limit

## Storage обязан:

* использовать batching
* НЕ писать в DB на каждый event

---

# 📲 7. Telegram / Connectors правила

* Telegram нельзя вызывать напрямую из Core
* только через Connector interface
* обязательно:

  * rate limiting
  * deduplication
  * batching (если возможно)

---

# 💾 8. Storage правила

* SQLite — default storage
* только через Storage interface
* bulk insert обязателен
* WAL mode обязателен

---

# 🔌 9. Расширяемость (STRICT)

Любая новая функциональность должна:

## ✔ добавляться через:

* Adapter
* Pipeline processor
* Connector
* Storage implementation

## ❌ запрещено:

* модифицировать Core под новые use-cases
* добавлять framework-specific код в Core
* хардкод Telegram / DB логики

---

# 🧪 10. Тестируемость

Каждый слой должен быть:

* изолирован
* тестируем без внешних сервисов
* mockable

## ❌ запрещено:

* тесты, зависящие от Telegram API
* тесты, зависящие от реальной DB

---

# 🧱 11. Dependency Injection (ОБЯЗАТЕЛЬНО)

Все зависимости передаются через `oko.init()`:

```python id="di_rule"
oko.init(
    connector=...,
    storage=...,
    pipeline=...
)
```

## ❌ запрещено:

* глобальные singletons без контроля
* импорт реализаций внутри Core

---

# 🚫 12. Запрещённые практики

* import FastAPI внутри Core
* прямой Telegram API вызов вне Connector
* SQL запросы вне Storage layer
* blocking I/O в Adapter
* синхронная тяжелая логика в request path

---

# 📈 13. Эволюция системы

Любое изменение должно:

* сохранять backward compatibility
* не ломать `oko.init()`
* не изменять поток данных
* не разрушать слои

---

# 🧭 14. Философия

> OKO может становиться сложнее внутри,
> но снаружи всегда остаётся простым:

```python id="simple_api"
import oko
oko.init()
```

---

# 🔚 Итог

Если правило усложняет использование OKO — правило неверное.
Если правило ломает слои — правило запрещено.
