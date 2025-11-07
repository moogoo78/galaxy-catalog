import subprocess
from app.application import flask_app
import click

from app.helpers.collection import import_collection


@flask_app.cli.command('makemigrations')
@click.argument('message')
def makemigrations(message):
    cmd_list = ['alembic', 'revision', '--autogenerate', '-m', message]
    subprocess.call(cmd_list)


@flask_app.cli.command('migrate')
def migrate():
    cmd_list = ['alembic', 'upgrade', 'head']
    subprocess.call(cmd_list)

@flask_app.cli.command('importcollection')
@click.argument('json_file')
@click.argument('library_id')
def importcollection(json_file, library_id):
    import_collection(json_file, library_id)

