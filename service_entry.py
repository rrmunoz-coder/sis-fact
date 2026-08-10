from waitress import serve

from sisfact import create_app

app = create_app()

if __name__ == "__main__":
    serve(
        app,
        host=app.config.get("APP_HOST", "0.0.0.0"),
        port=int(app.config.get("APP_PORT", 5060)),
        threads=8,
    )
