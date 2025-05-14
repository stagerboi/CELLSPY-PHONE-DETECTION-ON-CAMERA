from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import path, makedirs

# Initialize database and migration
db = SQLAlchemy()
migrate = Migrate()
DB_NAME = "cellspy.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'

    # Define database path inside instance folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{path.join(app.instance_path, DB_NAME)}'
    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import main
    from .auth import auth

    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    create_database(app)

    return app

def create_database(app):
    with app.app_context():
        makedirs(app.instance_path, exist_ok=True)
        db.create_all()
        print("Database checked/created successfully!")
