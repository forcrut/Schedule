from flask import Flask
import os


def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='../static')
    # Загружает основные настройки
    app.config.from_object('config.Config')
    # Загружает настройки из instance/config.py (если есть)
    app.config.from_pyfile('config.py', silent=True)

    with app.app_context():
        from . import routes, models

    return app


app = create_app()
