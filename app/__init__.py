import os
import logging
from flask import Flask
from .config import Config
from .auth import auth_bp, enforce_idle_timeout
from .api import api_bp
from .views import views_bp
from .maintenance import start_maintenance_thread

# Logging beállítása
def _setup_logging(log_path: str):
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger

# Flask app létrehozása
def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(Config)

    # Secret key beállítása
    app.secret_key = app.config["SECRET_KEY"]

    # Logging
    os.makedirs(os.path.dirname(app.config["LOG_PATH"] or "logs/") or ".", exist_ok=True)
    _setup_logging(app.config["LOG_PATH"])

    # Blueprintek (saját fájlokban definiáltak)
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Idle-timeout check minden kérés előtt (auth.py)
    app.before_request(enforce_idle_timeout)

    # Karbantartó thread (maintenance.py)
    start_maintenance_thread(app)

    return app