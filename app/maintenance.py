import time
import atexit
import logging
import threading
from datetime import datetime
from flask import current_app
from .pool import pool

logger = logging.getLogger("app")
_stop_event = threading.Event()

def _maintenance_loop():
    """
    - induláskor mindhárom connection login
    - 60 mp-enként ping
    - 2 óránként recycle az üres connectionökön; mindig hagyj 1 online-t
    """
    last_recycle = datetime.utcnow()

    # initial login
    with pool.with_lock():
        online_ok = 0
        for c in pool.conns:
            if pool.login_connection(c):
                online_ok += 1
        if online_ok == 0:
            # próbáljuk meg legalább az egyiket életre kelteni
            for _ in range(5):
                for c in pool.conns:
                    if pool.login_connection(c):
                        online_ok = 1
                        break
                if online_ok:
                    break

    while not _stop_event.is_set():
        now = datetime.utcnow()

        # ping
        try:
            with pool.with_lock():
                for c in pool.conns:
                    if c.status == "online":
                        try:
                            r = pool.call_external(c, "GET", "/api/users/2")
                            if r.status_code == 200:
                                c.last_ping = now
                                logger.info(f"ping_ok conn_id={c.id}")
                            else:
                                logger.warning(f"ping_non200 conn_id={c.id} status={r.status_code}")
                        except Exception as e:
                            logger.exception(f"ping_exception conn_id={c.id} err={e}")
        except Exception:
            logger.exception("ping_cycle_exception")

        # recycle
        if (now - last_recycle).total_seconds() >= current_app.config["RECYCLE_INTERVAL_SECONDS"]:
            try:
                # logout az üres connectionökön (kivéve hagyjunk 1 online-t)
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

                last_recycle = now
            except Exception:
                logger.exception("recycle_cycle_exception")

        _stop_event.wait(current_app.config["PING_INTERVAL_SECONDS"])

def start_maintenance_thread():
    t = threading.Thread(target=_maintenance_loop, name="maintenance", daemon=True)
    t.start()

    @atexit.register
    def _cleanup():
        _stop_event.set()

    return t
