import logging
import requests
import threading
from datetime import datetime
from typing import Optional, List, Set
from flask import current_app

logger = logging.getLogger("app")

# Kapcsolat osztály
class Connection:
    def __init__(self, conn_id: int):
        self.id: int = conn_id
        self.token: Optional[str] = None
        self.assigned_users: Set[str] = set()
        self.last_ping: Optional[datetime] = None
        self.status: str = "offline"  # offline|online|recycling
        self.created_at: datetime = datetime.utcnow()

# Kapcsolatok poolja
class Pool:
    def __init__(self, size: int = 3):
        self._lock = threading.RLock()
        self._conns: List[Connection] = [Connection(i + 1) for i in range(size)]

    # Lock lekérése
    def with_lock(self):
        return self._lock

    # Kapcsolatok listája
    @property
    def conns(self) -> List[Connection]:
        return self._conns

    # ---- Kapcsolatok életciklusa ----
    # Kapcsolat login
    def login_connection(self, c: Connection) -> bool:
        try:
            r = requests.post(
                "https://reqres.in/api/login",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": current_app.config.get("REQRES_API_KEY", "reqres-free-v1"),
                },
                json={
                    "email": current_app.config["REQRES_EMAIL"],
                    "password": current_app.config["REQRES_PASSWORD"],
                },
                timeout=10,
            )
            if r.status_code == 200:
                token = r.json().get("token")
                if token:
                    c.token = token
                    c.status = "online"
                    c.last_ping = datetime.utcnow()
                    logger.info(f"conn_login_ok conn_id={c.id}")
                    return True
            logger.error(f"conn_login_failed conn_id={c.id} status={r.status_code} body={r.text}")
            return False
        except Exception as e:
            logger.exception(f"conn_login_exception conn_id={c.id} err={e}")
            return False

    # Kapcsolat logout
    def logout_connection(self, c: Connection) -> None:
        c.token = None
        c.status = "offline"
        logger.info(f"conn_logout conn_id={c.id}")

    # ---- Kiválasztás és hozzárendelés ----
    # Legkevesebb felhasználóhoz rendelt online kapcsolat kiválasztása
    def pick_least_loaded_online(self) -> Optional[Connection]:
        online = [c for c in self._conns if c.status == "online"]
        if not online:
            return None
        return min(online, key=lambda x: len(x.assigned_users))

    # Felhasználó hozzárendelése kapcsolathoz
    def assign_user(self, username: str, conn: Connection) -> None:
        conn.assigned_users.add(username)
        logger.info(f"assigned_user conn_id={conn.id} user={username} count={len(conn.assigned_users)}")

    # Felhasználó eltávolítása kapcsolatról
    def detach_user(self, username: str, conn: Connection) -> None:
        if username in conn.assigned_users:
            conn.assigned_users.remove(username)
            logger.info(f"detached_user conn_id={conn.id} user={username} count={len(conn.assigned_users)}")

    # ---- Külső API hívás ----
    def call_external(self, conn: Connection, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        headers.setdefault("x-api-key", current_app.config.get("REQRES_API_KEY", "reqres-free-v1"))
        if conn.token:
            headers["Authorization"] = f"Bearer {conn.token}"
        url = f"https://reqres.in{path}"
        return requests.request(method=method, url=url, headers=headers, timeout=10, **kwargs)

# Egyetlen, megosztott pool példány
pool = Pool(size=3)