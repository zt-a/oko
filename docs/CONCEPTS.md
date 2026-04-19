
# 📌 CONCEPTS.md

````md
# OKO Concepts 👁️

**Базовые понятия системы**

---

# 🧠 1. Event (Событие)

Всё в OKO начинается с Event.

```python id="c1"
OkoEvent(
    type="error",
    message="строка",
    stack="строка",
    context={}
)
````

Event — это:

* ошибка
* лог
* исключение
* системное событие

---

# 🧩 2. Adapter (Адаптер)

Адаптер — это входная точка системы.

Он:

* перехватывает события фреймворка
* преобразует их в Event
* отправляет в Core

Примеры:

* middleware FastAPI
* WSGI middleware Flask/Django
* logging handler

---

# ⚙️ 3. Core (Ядро)

Core — это двигатель системы.

Он:

* принимает события
* кладёт их в очередь
* запускает worker
* передаёт в pipeline

Core НЕ:

* знает о фреймворках
* знает о Telegram
* знает о базе данных

---

# 🔁 4. Pipeline (Пайплайн обработки)

Pipeline обрабатывает события.

Он:

* убирает дубликаты
* группирует ошибки
* обогащает контекст
* применяет rate limit

Преобразует:

```text id="p1"
Event → Улучшенный Event
```

---

# 📡 5. Connector (Коннектор)

Connector — это выход системы.

Он:

* отправляет события наружу
* Telegram уведомления
* webhook интеграции
* будущие сервисы

---

# 💾 6. Storage (Хранилище)

Storage отвечает за сохранение данных.

Он:

* сохраняет события
* использует SQLite по умолчанию
* поддерживает batch-запись

---

# 👁️ 7. Dashboard (Слой наблюдения)

Dashboard — это слой **только для чтения данных**.

Он:

* читает события из Storage
* отображает ошибки в UI
* позволяет фильтровать и искать
* показывает stack trace и детали

---

## 📊 Поток данных для Dashboard

```text id="dash_flow"
Storage → Dashboard (read-only)
```

---

## ❌ Dashboard НЕ:

* не отправляет события в Core
* не участвует в Pipeline
* не вызывает Connectors
* не изменяет данные системы

---

## 🧠 Важно

Dashboard — это **наблюдательный слой**, а не часть обработки.

---

# 🧵 8. Worker (Фоновый процесс)

Worker:

* читает очередь
* запускает pipeline
* отправляет в storage и connectors

---

# 📦 9. Queue (Очередь)

Очередь:

* временно хранит события
* отделяет adapter от core
* предотвращает блокировки

---

# 🔄 10. Общий поток данных

```text id="flow_ru"
Adapter → Event → Core → Queue → Worker → Pipeline → Storage + Connector

Storage → Dashboard (read-only)
```

---

# 🧭 11. Главный принцип

> У каждого слоя — одна ответственность.

Никакой слой не должен знать реализацию другого слоя.

---

# 🧠 12. Расширенное разделение системы

Теперь OKO состоит из двух частей:

## ⚙️ Processing System

* Adapter
* Core
* Queue
* Worker
* Pipeline
* Storage
* Connector

## 👁️ Observation System

* Dashboard (read-only UI)

```
