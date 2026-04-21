"""
OKO + FastAPI пример

Запуск:
    pip install fastapi uvicorn
    uvicorn examples.fastapi_example:app --reload
"""

import oko
from fastapi import FastAPI

# --- Инициализация OKO ---
oko.init(
    telegram_token="8642162012:AAHLsMcVsM-MHiPB025jxhENrgb5i2uxcHY",
    telegram_chat_id="7931884852",
    project="myapp",
    environment="development",
    silence=0,
    capture_logs=True,
)

# --- Приложение ---
app = FastAPI(title="OKO FastAPI Example")

# Подключаем ASGI middleware — одна строка
app.add_middleware(oko.ASGIMiddleware)
app.include_router(oko.dashboard_router('/oko'))


@app.get("/")
async def root():
    return {"status": "ok", "message": "OKO is watching 👁️"}


@app.get("/error")
async def trigger_500():
    """Эндпоинт который падает — OKO должен поймать."""
    raise ValueError("Something went wrong")


@app.get("/not-found")
async def trigger_404():
    """404 не мониторится по умолчанию."""
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/bad-request")
async def trigger_400():
    """400 мониторится — OKO уведомит."""
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="Bad request")


@app.post("/capture")
async def manual_capture(message: str = "test"):
    """Ручной захват события."""
    oko.capture_log(message, level="warning", context={"source": "manual"})
    return {"captured": message}