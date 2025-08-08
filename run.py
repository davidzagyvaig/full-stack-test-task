from app import create_app

app = create_app()

# Program indítása
if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=False, threaded=True)