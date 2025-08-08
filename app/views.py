from flask import Blueprint, render_template
from .auth import require_auth_or_redirect

views_bp = Blueprint("views", __name__)

# Home oldal megjelenítése
@views_bp.get("/home")
def home_page():
    redirect_resp = require_auth_or_redirect()
    if redirect_resp:
        return redirect_resp
    return render_template("home.html")
