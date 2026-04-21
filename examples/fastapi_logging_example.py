import logging
import oko
from fastapi import FastAPI
from oko.adapters.logging_handler import install_logging_handler

# 1. Настройка стандартного logging в Python
# Устанавливаем базовый уровень для всех логов
logging.basicConfig(level=logging.INFO)

# 2. Инициализация OKO
# Примечание: telegram_token и telegram_chat_id нужно получить у @BotFather и @userinfobot
engine = oko.init(
    telegram_token="...",  # Замените на ваш токен от @BotFather
    telegram_chat_id="...",  # Замените на ваш chat_id от @userinfobot
    project="city-problem-map",
    environment="development",
    capture_logs=False, # Отключаем внутренний авто-захват, так как ставим хендлер вручную ниже
    silence=0,
)

# 3. ПОДКЛЮЧЕНИЕ ХЕНДЛЕРА К LOGGING
# Теперь всё, что логируется через logging.error() или выше, улетит в OKO
install_logging_handler(engine=engine, level=logging.ERROR)

# --- Приложение ---
app = FastAPI(title="OKO + FastAPI + Logging")

# Подключаем middleware для перехвата HTTP-ошибок
app.add_middleware(oko.ASGIMiddleware)

@app.get("/")
async def root():
    # Пример обычного лога — в телеграм не уйдет (уровень INFO)
    logging.info("Root endpoint visited")
    return {"status": "ok"}

@app.get("/trigger-log-error")
async def log_error():
    """
    Пример: ошибка не роняет приложение, но мы пишем её в лог.
    Благодаря хендлеру, OKO это поймает.
    """
    try:
        x = 1 / 0
    except ZeroDivisionError:
        logging.exception("Упс! Деление на ноль в бизнес-логике") # .exception автоматически добавит стектрейс
    return {"status": "error_logged"}

@app.get("/runtime-error")
async def runtime_error():
    """Критическая ошибка, которую поймает Middleware."""
    raise RuntimeError("Критический сбой системы!")

@app.post("/manual")
async def manual():
    # Ручной вызов через библиотеку
    oko.capture_log("Manual alert", level="critical")
    return {"ok": True}