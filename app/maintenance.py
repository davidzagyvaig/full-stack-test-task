import time
import atexit
import logging
import threading
from datetime import datetime, timedelta
from flask import current_app
from .pool import pool
from .store import sessions, sessions_lock, now

logger = logging.getLogger("app")
_stop_event = threading.Event()

# Karbantartó loop
def _maintenance_loop(app):
    with app.app_context():
        last_recycle = now()

        # Induláskor mindhárom connection login
        with pool.with_lock():
            while True:
                online_ok = 0
                for c in pool.conns:
                    if pool.login_connection(c):
                        online_ok += 1
                if online_ok != len(pool.conns):
                    time.sleep(1)
                else:
                    break

        # Karbantartó loop
        while not _stop_event.is_set():

            # 60 mp-enként ping
            try:
                with pool.with_lock():
                    for c in pool.conns:
                        if c.status == "online":
                            try:
                                r = pool.call_external(c, "GET", "/api/users/2")
                                if r.status_code == 200:
                                    c.last_ping = now()
                                    logger.info(f"ping_ok conn_id={c.id}")
                                else:
                                    logger.warning(f"ping_non200 conn_id={c.id} status={r.status_code}")
                            except Exception as e:
                                logger.exception(f"ping_exception conn_id={c.id} err={e}")
            except Exception:
                logger.exception("ping_cycle_exception")

            # 2 óránként újraindítás
            if (now() - last_recycle).total_seconds() >= current_app.config["RECYCLE_INTERVAL_SECONDS"]:
                try:
                    # Logout az üres connectionökön (kivéve hagyjunk 1 online-t)
                    with pool.with_lock():
                        empties = [c for c in pool.conns if c.status == "online" and len(c.assigned_users) == 0]
                        online_cnt = sum(1 for c in pool.conns if c.status == "online")
                        max_recycle = max(0, online_cnt - 1)
                        to_recycle = empties[:max_recycle]
                        for c in to_recycle:
                            logger.info(f"recycle_start conn_id={c.id}")
                            pool.logout_connection(c)

                    if to_recycle:
                        time.sleep(current_app.config["RECYCLE_SLEEP_BETWEEN_LOGOUT_LOGIN"])

                    with pool.with_lock():
                        for c in to_recycle:
                            pool.login_connection(c)
                            logger.info(f"recycle_done conn_id={c.id}")

                    last_recycle = now()
                except Exception as e:
                    logger.exception(f"recycle_cycle_exception err={e}")

            # 60 mp-enként munkamenetek takarítása, ha kell (idle-timeout)
            try:
                idle_minutes = current_app.config["SESSION_IDLE_MINUTES"]
                cutoff = now() - timedelta(minutes=idle_minutes)

                # Jelöltek kigyűjtése
                with sessions_lock:
                    candidates = [(sid, s.get("username"), s.get("assigned_conn"))
                                for sid, s in sessions.items()
                                if s.get("last_activity") and s["last_activity"] < cutoff]

                # Ha vannak jelöltek, akkor újraellenőrizzük és töröljük a munkameneteket
                if candidates:
                    with pool.with_lock():
                        with sessions_lock:
                            for sid, username, conn_id in candidates:
                                s = sessions.get(sid)
                                if not s or not s.get("last_activity") or s["last_activity"] >= cutoff:
                                    continue

                                # Felhasználó eltávolítása kapcsolatról
                                if username and conn_id:
                                    conn = next((c for c in pool.conns if c.id == conn_id), None)
                                    if conn and username in conn.assigned_users:
                                        pool.detach_user(username, conn)

                                # Munkamenet törlése
                                sessions.pop(sid, None)
                                logger.info(f"session_timeout_maintenance user={username} conn_id={conn_id} sid={sid}")
            except Exception as e:
                logger.exception(f"session_cleanup_exception err={e}")

            _stop_event.wait(current_app.config["PING_INTERVAL_SECONDS"])

# Karbantartó thread indítása
def start_maintenance_thread(app):
    t = threading.Thread(target=_maintenance_loop, args=(app,), name="maintenance", daemon=True)
    t.start()

    @atexit.register
    def _cleanup():
        _stop_event.set()

    return t