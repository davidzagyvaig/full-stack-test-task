import requests
r = requests.post("https://reqres.in/api/login",
                  headers={"Content-Type": "application/json", "x-api-key": "reqres-free-v1"},
                  json={"email":"eve.holt@reqres.in","password":"cityslicka"}, timeout=10)
print(r.status_code, r.url, r.text, "history:", [h.headers.get("Location") for h in r.history])