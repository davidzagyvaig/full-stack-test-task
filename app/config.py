import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Külső API (reqres)
    REQRES_EMAIL = os.environ.get("REQRES_EMAIL", "eve.holt@reqres.in")
    REQRES_PASSWORD = os.environ.get("REQRES_PASSWORD", "cityslicka")

    # Időzítések
    SESSION_IDLE_MINUTES = int(os.environ.get("SESSION_IDLE_MINUTES", "20"))
    PING_INTERVAL_SECONDS = int(os.environ.get("PING_INTERVAL_SECONDS", "60"))
    RECYCLE_INTERVAL_SECONDS = int(os.environ.get("RECYCLE_INTERVAL_SECONDS", str(2 * 60 * 60)))
    RECYCLE_SLEEP_BETWEEN_LOGOUT_LOGIN = int(os.environ.get("RECYCLE_SLEEP_BETWEEN_LOGOUT_LOGIN", "60"))

    LOG_PATH = os.environ.get("LOG_PATH", "logs/app.log")
