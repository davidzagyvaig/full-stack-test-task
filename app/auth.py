import uuid
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
from flask import Blueprint, current_app, request, session as flask_session, redirect, url_for, render_template
from .store import USERS, sessions, sessions_lock, now
from .pool import pool

logger = logging.getLogger("app")
auth_bp = Blueprint("auth", __name__)

# Aktuális munkamenet lekérése
def current_session() -> Optional[Dict[str, Any]]:
    sid = flask_session.get("sid")
    if not sid:
        return None
    with sessions_lock:
        return sessions.get(sid)

# Hiányzó munkamenet esetén átirányítás login oldalra
def require_auth_or_redirect():
    if not current_session():
        return redirect(url_for("auth.login_page"))
    return None

# Idle-timeout check minden kérés előtt
@auth_bp.before_app_request
def enforce_idle_timeout():
    s = current_session()
    if not s:
        return
    last = s.get("last_activity")
    if last and (now() - last) > timedelta(minutes=current_app.config["SESSION_IDLE_MINUTES"]):
        # timeout -> detach + session clear
        username = s.get("username")
        conn_id = s.get("assigned_conn")
        with pool.with_lock():
            conn = next((c for c in pool.conns if c.id == conn_id), None)
            if conn and username:
                pool.detach_user(username, conn)
        sid = flask_session.get("sid")
        with sessions_lock:
            sessions.pop(sid, None)
        flask_session.pop("sid", None)
        logger.info(f"session_timeout user={username} conn_id={conn_id}")
        return redirect(url_for("auth.login_page"))
    # refresh activity
    s["last_activity"] = now()

# Login oldal megjelenítése
@auth_bp.get("/")
def login_page():
    # Ha már van munkamenet, akkor átirányítás home oldalra
    s = current_session()
    if s:
        return redirect(url_for("views.home_page"))
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg)

# Login kérés kezelése
@auth_bp.post("/login")
def do_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Hibás felhasználónév vagy jelszó
    if USERS.get(username) != password:
        logger.info(f"login_failed user={username}")
        return render_template("login.html", msg="Hibás felhasználónév vagy jelszó."), 401

    # Felhasználó kapcsolathoz rendelése
    with pool.with_lock():
        conn = pool.pick_least_loaded_online()
        if not conn:
            logger.error("login_no_connection_available")
            return render_template("login.html", msg="Jelenleg nem érhető el kapcsolat, próbáld később."), 503
        pool.assign_user(username, conn)

    # Munkamenet létrehozása
    sid = str(uuid.uuid4())
    with sessions_lock:
        sessions[sid] = {
            "username": username,
            "assigned_conn": conn.id,
            "last_activity": now()
        }
    flask_session["sid"] = sid
    flask_session.permanent = False

    logger.info(f"login_ok user={username} conn_id={conn.id}")
    return redirect(url_for("views.home_page"))

# Kijelentkezés kérés kezelése
@auth_bp.get("/logout")
def do_logout():
    s = current_session()
    if s:
        username = s.get("username")
        conn_id = s.get("assigned_conn")
        with pool.with_lock():
            conn = next((c for c in pool.conns if c.id == conn_id), None)
            if conn and username:
                pool.detach_user(username, conn)
        sid = flask_session.get("sid")
        with sessions_lock:
            sessions.pop(sid, None)
        flask_session.pop("sid", None)
        logger.info(f"logout_ok user={username} conn_id={conn_id}")
    return redirect(url_for("auth.login_page", msg="Kijelentkeztél."))