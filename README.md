# Full stack developer próbaalkalmazás

Ez a projekt a próbafeladat mintamegoldása. A cél egy Flask alapú webalkalmazás készítése, amely
bejelentkezést, munkamenetkezelést és egy külső szolgáltatás felé irányuló kapcsolati poolt tartalmaz.

## Követelmények
- Python 3.10
- telepített Python csomagok a `requirements.txt` alapján

## Telepítés és futtatás
1. Hozz létre virtuális környezetet és telepítsd a csomagokat:
   ```bash
   python -m venv .venv
   # Windows: .\venv\Scripts\activate
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Indítsd el a szervert:
   ```bash
   python run.py
   ```
   Az alkalmazás a `http://localhost:5000` címen érhető el.

## Használat
- A kezdőoldal egy login form. A példában 20 előre definiált felhasználó
  szerepel (`user1`/`password1` ... `user20`/`password20`).
- Sikeres belépés után a `/home` oldal jelenik meg, ahol egy gomb AJAX hívással
  lekér a felhasználóhoz rendelt kapcsolat segítségével a `reqres.in` által biztosított API-ról egy mintaválaszt.
- A felhasználói munkamenet inaktivitás esetén 20 perc után lejár.
- A szerver részletes naplókat ír a `logs/app.log` fájlba.

## Mappastruktúra
```
app/                – Flask modulok
  __init__.py       – alkalmazás inicializálása és logging
  auth.py           – autentikáció és munkamenetek
  api.py            – autentikált API végpontok
  views.py          – HTML oldalak megjelenítése
  pool.py           – külső szolgáltatáshoz tartozó connection pool
  maintenance.py    – háttérfolyamat a pingeléshez és újraindításhoz
  config.py         – konfigurációs értékek
  store.py          – felhasználók és szerver oldali session tár
templates/          – HTML sablonok (login, home)
tests/              – egyszerű script a külső API kipróbálásához
run.py              – belépési pont az alkalmazás indításához
requirements.txt    – szükséges Python csomagok
```

## Konfiguráció
Alapértelmezés szerint a szükséges értékek az `app/config.py` fájlban szereplő
környezeti változókból olvashatók. Szükség esetén állítsd be például:
```bash
export SECRET_KEY=valami_titok
export LOG_PATH=logs/app.log
```

