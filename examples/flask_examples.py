"""
OKO + Flask пример

Запуск:
    pip install flask
    python examples/flask_example.py
"""

import oko
from flask import Flask, jsonify

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
app = Flask(__name__)

# Подключаем WSGI middleware — одна строка
app.wsgi_app = oko.WSGIMiddleware(app.wsgi_app)


@app.get("/")
def root():
    return jsonify({"status": "ok", "message": "OKO is watching 👁️"})


@app.get("/error")
def trigger_500():
    """Эндпоинт который падает — OKO должен поймать."""
    raise ValueError("Something went wrong")


@app.get("/not-found")
def trigger_404():
    """404 не мониторится по умолчанию."""
    return jsonify({"detail": "Not found"}), 404


@app.get("/bad-request")
def trigger_400():
    """400 мониторится — OKO уведомит."""
    return jsonify({"detail": "Bad request"}), 400


@app.post("/capture")
def manual_capture():
    """Ручной захват события."""
    from flask import request
    message = request.args.get("message", "test")
    oko.capture_log(message, level="warning", context={"source": "manual"})
    return jsonify({"captured": message})


if __name__ == "__main__":
    app.run(debug=False, port=8000)