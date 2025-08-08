import logging
from flask import Blueprint, abort, jsonify
from .auth import current_session
from .pool import pool

logger = logging.getLogger("app")
api_bp = Blueprint("api", __name__)

# Példa felhasználó adatainak lekérése a külső API-ról
@api_bp.get("/me")
def api_me():
    s = current_session()
    if not s:
        abort(401)
    username = s["username"]
    conn_id = s["assigned_conn"]

    # Felhasználóhoz rendelt kapcsolat ellenőrzése
    with pool.with_lock():
        conn = next((c for c in pool.conns if c.id == conn_id), None)
        if not conn or conn.status != "online":
            logger.warning(f"api_me_no_online_conn user={username} conn_id={conn_id}")
            abort(503)

    # Külső API hívása
    try:
        r = pool.call_external(conn, "GET", "/api/users/2")
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.exception(f"api_me_exception conn_id={conn.id} err={e}")
        abort(502)

    logger.info(f"api_me_ok user={username} conn_id={conn.id}")
    return jsonify({"user": username, "conn_id": conn.id, "external_sample": data})