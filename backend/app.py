from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    # Flask
    app = Flask(__name__, template_folder='../frontend', static_folder='../frontend', static_url_path='/')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./database.db'
    app.secret_key = 'temporary' #TODO: Change to be secure

    # Database
    db.init_app(app)

    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    from models import User
    @login_manager.user_loader
    def load_user(uid):
        return db.session.get(User, uid)
    
    # Hashing passwords
    bcrypt = Bcrypt(app)

    # Register Flask routes
    from routes import register_routes
    register_routes(app, db, bcrypt)

    # Migrate for modifying database
    migrate = Migrate(app, db)

    return app