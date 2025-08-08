import threading
from datetime import datetime
from typing import Dict, Any

# Hardcode-olt userek (20 darab)
USERS: Dict[str, str] = {f"user{i}": f"password{i}" for i in range(1, 21)}

# Szerver oldali munkamenetek (Flask cookie csak a SID-t viszi)
sessions: Dict[str, Dict[str, Any]] = {}
sessions_lock = threading.RLock()

# Idő
def now() -> datetime:
    return datetime.utcnow()
