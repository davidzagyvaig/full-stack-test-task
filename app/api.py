import logging
from flask import Blueprint, abort, jsonify
from .auth import current_session
from .pool import pool

logger = logging.getLogger("app")
api_bp = Blueprint("api", __name__)

@api_bp.get("/me")
def api_me():
    s = current_session()
    if not s:
        abort(401)
    username = s["username"]
    conn_id = s["assigned_conn"]

    with pool.with_lock():
        conn = next((c for c in pool.conns if c.id == conn_id), None)
        if not conn or conn.status != "online":
            logger.warning(f"api_me_no_online_conn user={username} conn_id={conn_id}")
            abort(503)

    try:
        r = pool.call_external(conn, "GET", "/api/users/2")
        if r.status_code in (401, 403):
            # egyszeri relogin + retry
            with pool.with_lock():
                logger.warning(f"api_me_token_invalid conn_id={conn.id}; relogin")
                pool.login_connection(conn)
            r = pool.call_external(conn, "GET", "/api/users/2")
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.exception(f"api_me_exception conn_id={conn.id} err={e}")
        abort(502)

    return jsonify({"user": username, "conn_id": conn.id, "external_sample": data})

@api_bp.get("/pool")
def api_pool_state():
    s = current_session()
    if not s:
        abort(401)
    with pool.with_lock():
        return jsonify({"connections": [c.to_public() for c in pool.conns]})

@api_bp.get("/healthz")
def healthz():
    return "ok", 200
