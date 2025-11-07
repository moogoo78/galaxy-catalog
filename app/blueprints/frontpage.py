from flask import (
    Blueprint,
    request,
    render_template,
    jsonify,
    abort,
    g,
    redirect,
    url_for,
    current_app,
)
from app.database import session
from app.helpers.collection import get_collections
from app.helpers.item import get_items
from app.models import (
    Library,
)

bp = Blueprint('frontpage', __name__)

@bp.route('/')
def index():
    current_lib = None
    if request and request.headers:
        if host := request.headers.get('Host'):
            if lib := Library.query.filter(Library.host==host).scalar():
                current_lib = lib
            elif current_app.config['WEB_ENV'] == 'dev': # dev just match Site.name
                hostname = host.split('.')[0]
                if lib := Library.query.filter(Library.name==hostname).scalar():
                    current_lib = lib


    if current_lib:
        return render_template('index.html', current_lib=current_lib)
    else:
        return abort(404)

@bp.route('/api/library/<int:library_id>/collections')
def api_collections(library_id):
    #conf = get_config(library_id)
    data = get_collections(library_id, 2)
    return jsonify(data)

@bp.route('/api/library/<int:library_id>/items')
def api_items(library_id):
    q = request.args.get('q', '')
    collection_id = request.args.get('collection_id', '')
    limit = request.args.get('limit', 20)
    offset = request.args.get('offset', 0)
    filtr = {}
    if q:
        filtr['q'] = q
    if collection_id:
        filtr['collection_id'] = collection_id
    results = get_items(library_id, filtr, limit, offset)
    data = {
        'items': [],
        'total': results['total'],
    }

    for row in results['items']:
        data['items'].append({
            'id': row.id,
            'name': row.name,
            'name_zh': row.name_zh,
            'name_zh_other': row.source_data['Chinese_name_other'],
            'status_id': row.source_data['status_id'],
        })
    return jsonify(data)
