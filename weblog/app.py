from flask import Flask
from .handles import blueprint_list
from flask_bootstrap import Bootstrap
from .configs import configs
from .models import db, Role, User
from flask_moment import Moment
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_pagedown import PageDown

def register_blueprints(app):
    for bp in blueprint_list:
        app.register_blueprint(bp)

def register_extensions(app):
    Bootstrap(app)
    db.init_app(app)
    Moment(app)
    Migrate(app, db)
    PageDown().init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    @login_manager.user_loader
    def user_loader(id):
        return User.query.get(id)
    login_manager.login_view = 'front.login'
    login_manager.login_message = '你需要登录之后才能访问页面'
    login_manager.login_message_category = 'warning'


def create_app(config):
    app = Flask(__name__)

    app.config.from_object(configs.get(config))
    register_extensions(app)
    register_blueprints(app)
    app.debug = True
    return app