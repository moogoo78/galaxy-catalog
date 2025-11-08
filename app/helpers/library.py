from pathlib import Path
import configparser

from app.models import Library
from app.database import session

def get_config(library_id):
    if lib := session.get(Library, library_id):
        conf_path = Path('app', 'settings', f'{lib.name}.ini')
        config = configparser.ConfigParser()
        config.optionxform = str # case-sensitive
        config.read(conf_path)
        return config


def get_library(request):
    #if request and request.headers:
    if host := request.headers.get('Host'):
        if lib := Library.query.filter(Library.host==host).scalar():
            current_lib = lib
        elif current_app.config['WEB_ENV'] == 'dev': # dev just match Site.name
            hostname = host.split('.')[0]
            if lib := Library.query.filter(Library.name==hostname).scalar():
                current_lib = lib

        return current_lib
