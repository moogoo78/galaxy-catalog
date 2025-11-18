from pathlib import Path
import configparser

from flask import current_app

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


def get_web_analytics(library_id):
    """Get web analytics configuration for a library."""
    config = get_config(library_id)
    if config and config.has_section('web_analytics'):
        return {
            'type': config.get('web_analytics', 'type', fallback=None),
            'key': config.get('web_analytics', 'key', fallback=None),
        }
    return None


def get_storage_config(library_id):
    """Get storage configuration for a library."""
    config = get_config(library_id)
    if config and config.has_section('storage'):
        bucket = config.get('storage', 'bucket', fallback='')
        url = config.get('storage', 'url', fallback='')
        prefix = config.get('storage', 'prefix', fallback='')
        return {
            'bucket': bucket,
            'url': url,
            'prefix': prefix,
            'full_url': f'{url}{prefix}' if url and prefix else ''
        }
    return None
