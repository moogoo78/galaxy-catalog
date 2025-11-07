import os
import re
import json
import logging
from logging.handlers import RotatingFileHandler
#from logging.config import dictConfig

from flask import (
    g,
    Flask,
    jsonify,
    render_template,
    redirect,
    request,
    flash,
    url_for,
    abort,
)
#from flask_login import (
#    LoginManager,
#)
#from flask_babel import (
#    Babel,
#    gettext,
    #ngettext,
#)
# from babel.support import Translations
#from flask_jwt_extended import JWTManager

#from app.database import init_db
from app.database import session

#from app.models.site import (
#    User,
#    Site,
#)
#from app.utils import find_date
#from app.jinja_func import *

#from scripts import load_data


# dictConfig({
#     'version': 1,
#     'formatters': {'default': {
#         'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
#     }},
#     'handlers': {'wsgi': {
#         'class': 'logging.StreamHandler',
#         'stream': 'ext://flask.logging.wsgi_errors_stream',
#         'formatter': 'default'
#     }},
#     'root': {
#         'level': 'DEBUG',
#         'handlers': ['wsgi']
#     }
# })

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('[CONSOLE] %(levelname)s: %(message)s'))

#file_handler = RotatingFileHandler('/var/log/naturedb/flask.log', maxBytes=5 * 1024 * 1024, backupCount=10)
#file_handler.setLevel(logging.DEBUG)
#file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))

logger.addHandler(console_handler)
#logger.addHandler(file_handler)


def apply_blueprints(app):
    #from app.blueprints.base import base as base_bp
    from app.blueprints.frontpage import bp as frontpage_bp
    #from app.blueprints.admin import admin as admin_bp;
    #from app.blueprints.api import api as api_bp;

    #app.register_blueprint(base_bp)
    app.register_blueprint(frontpage_bp)
    #app.register_blueprint(admin_bp, url_prefix='/admin')
    #app.register_blueprint(api_bp, url_prefix='/api/v1')

def apply_extensions(app):
    # flask extensions

    # babel
    #babel = Babel(app, locale_selector=get_locale)
    #app.jinja_env.globals['get_locale'] = get_locale
    #app.jinja_env.globals['get_lang_path'] = get_lang_path
    #app.jinja_env.globals['str_to_date'] = str_to_date

    # login
    #login_manager = LoginManager()
    #login_manager.init_app(app)

    #@login_manager.user_loader
    #def load_user(id):
    #    return User.query.get(id)

    #@login_manager.unauthorized_handler
    #def unauthorized():
        # do stuff
    #    return redirect(url_for('admin.login') + '?next=' + request.path)

    # jwt
    #jwt = JWTManager(app)
    pass

#session = init_db(flask_app.config)

def create_app():
    #app = Flask(__name__, subdomain_matching=True, static_folder=None)
    app = Flask(__name__)
    if os.getenv('WEB_ENV') == 'dev':
        app.config.from_object('app.config.DevelopmentConfig')
    elif os.getenv('WEB_ENV') == 'prod':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.Config')

    #app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations' # default translations
    app.config['BABEL_DEFAULT_LOCALE'] = app.config['DEFAULT_LANG_CODE']

    # print(app.config, flush=True)
    # subdomain
    #app.config['SERVER_NAME'] = 'sh21.ml:5000'
    #app.url_map.default_subdomain = 'www'
    #app.static_folder='static'
    #app.add_url_rule('/static/<path:filename>',
    #                 endpoint='static',
    #                 subdomain='static',
    #                 view_func=app.send_static_file)

    app.url_map.strict_slashes = False
    #print(app.config, flush=True)

    apply_blueprints(app)
    apply_extensions(app)

    return app

flask_app = create_app()


@flask_app.route('/')
def cover():
    host = request.headers.get('Host', '')
    if host == os.getenv('PORTAL_HOST'):
        return render_template('cover.html')

    if site := Site.find_by_host(host):
        return redirect(url_for('frontpage.index', lang_code='zh'))

    return 'naturedb: no site' #abort(404)


@flask_app.route('/url_maps')
def debug_url_maps():
    rules = []
    for rule in flask_app.url_map.iter_rules():
        rules.append([str(rule), str(rule.methods), rule.endpoint])
    return jsonify(rules)

@flask_app.teardown_appcontext
def shutdown_session(exception=None):
    # SQLAlchemy won`t close connection, will occupy pool
    session.remove()

with flask_app.app_context():
    # needed to make CLI commands work
    from .commands import *
