"""
OKO + Flask Dashboard пример

Запуск:
    pip install flask
    python examples/flask_dashboard_example.py
"""

import oko
from flask import Flask

# --- Инициализация OKO ---
# Примечание: telegram_token и telegram_chat_id нужно получить у @BotFather и @userinfobot
oko.init(
    telegram_token="...",  # Замените на ваш токен от @BotFather
    telegram_chat_id="...",  # Замените на ваш chat_id от @userinfobot
    project="myapp",
    environment="development",
    db_path="oko.db",
)

# --- Приложение ---
app = Flask(__name__)

# Подключаем WSGI middleware — одна строка
app.wsgi_app = oko.WSGIMiddleware(app.wsgi_app)

# Подключаем Dashboard (Flask Blueprint)
app.register_blueprint(oko.dashboard_blueprint(url_prefix="/oko"))


@app.route("/")
def root():
    return {"status": "ok", "message": "OKO is watching 👁️"}


@app.route("/error")
def trigger_500():
    """Эндпоинт который падает — OKO должен поймать."""
    raise ValueError("Something went wrong")


@app.route("/not-found")
def trigger_404():
    """404 не мониторится по умолчанию."""
    return {"detail": "Not found"}, 404


@app.route("/bad-request")
def trigger_400():
    """400 мониторится — OKO уведомит."""
    return {"detail": "Bad request"}, 400


@app.post("/capture")
def manual_capture():
    """Ручной захват события."""
    from flask import request
    message = request.args.get("message", "test")
    oko.capture_log(message, level="warning", context={"source": "manual"})
    return {"captured": message}


if __name__ == "__main__":
    app.run(debug=False, port=8000)
