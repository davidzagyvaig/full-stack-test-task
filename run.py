from app import create_app

app = create_app()

if __name__ == "__main__":
    # threaded=True -> több szál, ezért kellett a lockolás
    app.run("0.0.0.0", 5000, debug=False, threaded=True)
