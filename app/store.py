import threading
from datetime import datetime
from typing import Dict, Any

# Hardcode-olt userek (≥20)
USERS: Dict[str, str] = {f"user{i}": f"pass{i}" for i in range(1, 21)}

# Szerver oldali session store (Flask cookie csak a SID-et viszi)
sessions: Dict[str, Dict[str, Any]] = {}
sessions_lock = threading.RLock()

def now() -> datetime:
    return datetime.utcnow()
