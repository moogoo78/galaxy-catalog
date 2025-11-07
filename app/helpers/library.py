from pathlib import Path
import configparser

from app.models import Library
from app.database import session

def get_config(library_id):
    if lib := session.get(Library, library_id):
        conf_path = Path('app', 'settings', f'{lib.name}.ini')
        config = configparser.ConfigParser()
        config.read(conf_path)
        return config

