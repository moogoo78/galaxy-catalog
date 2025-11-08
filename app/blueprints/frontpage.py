from collections import OrderedDict

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
from app.helpers.library import get_library
from app.helpers.collection import get_collections
from app.helpers.item import get_items
from app.helpers.cache import get_cache, set_cache
from app.models import (
    Library,
    Item,
)

bp = Blueprint('frontpage', __name__)

@bp.route('/')
def index():

    if library := get_library(request):
        return render_template('index.html', library=library)
    else:
        return abort(404)

@bp.route('/items/<int:item_id>')
def item_detail(item_id):
    if item := session.get(Item, item_id):
        library = session.get(Library, item.library_id)
        item.proxy_field_data = OrderedDict()
        for fd in item.field_data:
            item.proxy_field_data[fd['name']] = fd
        return render_template('item_detail.html', item=item, library=library)
    else:
        return abort(404)

@bp.route('/api/library/<int:library_id>/collections')
def api_collections(library_id):
    cache_key = f'lib-{library_id}-collections'
    if x := get_cache(cache_key):
        data = x
    else:
        data = get_collections(library_id, 2)
        set_cache(cache_key, data, 86400) # 1 day: 60 * 60 * 24

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

    if len(filtr) == 0:
        cache_key = f'lib-{library_id}-items'
        if x := get_cache(cache_key):
            results = x
        else:
            results = get_items(library_id, filtr, limit, offset)
            set_cache(cache_key, results, 86400) # 1 day: 60 * 60 * 24
    else:
        results = get_items(library_id, filtr, limit, offset)

    data = {
        'items': [],
        'total': results['total'],
    }

    for row in results['items']:
        #TODO
        name_zh_other = ''
        status_id = '1'
        if x := row.source_data.get('Chinese_name_other'):
            name_zh_other = x
        if x := row.source_data.get('status_id'):
            status_id = 1
        data['items'].append({
            'id': row.id,
            'name': row.name,
            'name_zh': row.name_zh,
            'name_zh_other': name_zh_other,
            'status_id': status_id,
        })
    return jsonify(data)
