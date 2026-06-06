import os
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("123abc")

    from game import game_bp
    app.register_blueprint(game_bp)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
