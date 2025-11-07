import json
from sqlalchemy.exc import IntegrityError
from sqlalchemy import (
    select,
    func,
)

from app.models import (
    Collection,
    Item,
    ItemData,
    CollectionClosure,
    CollectionItem
)
from app.database import session
from app.helpers.library import get_config

def import_collection(json_file, library_id):
    with open(json_file) as f:
        data = json.load(f)

        collection_map = {}
        item_map = {}
        # create Collection & Item
        def process_level(items_dict, current_rank_idx):
            """Recursively convert dict structure to array structure."""
            result = []

            for key, node in items_dict.items():
                #print(key, node['rank'], current_rank_idx)
                item = {
                    'name': node['name'],
                    'rank': node['rank']
                }
                if 'records' in node:
                    # Last level - include the records
                    item['records'] = node['records']
                    item['count'] = len(node['records'])

                    for i in node['records']:
                        x = Item(
                            name=node['name'],
                            name_zh=node['name_zh'],
                            item_type_id=1,
                            source_data=i,
                            key=node['key'],
                            library_id=library_id
                        )
                        session.add(x)
                        session.commit()

                        item_data = ItemData(item_id=x.id, field_id=1, value=i.get('is_accepted', '0'))
                        session.add(item_data)
                        item_map[node['key']] = x.id

                elif 'children' in node:
                    # Intermediate level - recurse
                    item['children'] = process_level(node['children'], current_rank_idx + 1)
                    item['count'] = sum(child['count'] for child in item['children'])
                    col = Collection(
                        name=node['name'],
                        name_zh=node['name_zh'],
                        key=node['key'],
                        library_id=library_id,
                        level=node['rank'].lower())
                    session.add(col)
                    session.commit()
                    collection_map[node['key']] = col.id
                result.append(item)

            return result

        hierarchy_array = process_level(data, 0)



        species_list = []

        def traverse(node_dict, current_path=''):
            """Recursively traverse and build paths."""
            for key, node in node_dict.items():
                # Build the path with this node's UUID
                node_uuid = node.get('key', '')
                new_path = f"{current_path}/{node_uuid}" if current_path else node_uuid

                if 'records' in node:
                    # Leaf node - add all records with the complete path
                    for record in node['records']:
                        species_list.append({
                            'path': new_path,
                            'name': node.get('name', ''),
                            'name_zh': node.get('name_zh', ''),
                            'rank': node.get('rank', ''),
                            'record': record
                        })
                elif 'children' in node:
                    # Intermediate node - continue traversing
                    traverse(node['children'], new_path)

        traverse(data)
        #print(len(species_list))

        # Create CollectionClosure & CollectionItem
        ## not a good way..., lots of integrity exception
        count = 0
        for i in species_list:
            count += 1
            paths = i['path'].split('/')
            species_key = paths[-1]
            #item = Item.query.filter(Item.key==species_key).scalar()
            item_id = item_map[species_key]
            #col = Collection.query.filter(Collection.key==paths[-2]).scalar()
            col_id = collection_map[paths[-2]]
            #if item and col:
            #    ci = CollectionItem(library_id=1, item_id=item.id, collection_id=col.id)
            if item_id and col_id:
                try:
                    ci = CollectionItem(library_id=1, item_id=item_id, collection_id=col_id)
                    session.add(ci)
                    session.commit()
                except IntegrityError as e:
                    session.rollback()
            else:
                print(f'item:{item_id} or {col_id} not found')

            for depth in range(0, len(paths)-1):
                for depth2 in range(0, len(paths)-1):
                    if depth <= depth2:
                        #x = Collection.query.filter(Collection.key==paths[depth]).scalar()
                        #y = Collection.query.filter(Collection.key==paths[depth2]).scalar()
                        ## mapping much faster
                        xid = collection_map[paths[depth]]
                        yid = collection_map[paths[depth2]]
                        if xid and yid:
                            try:
                                cc = CollectionClosure(
                                    ancestor_id=xid,
                                    descendant_id=yid,
                                    depth=depth2-depth,
                                )
                                session.add(cc)
                                session.commit()
                            except IntegrityError as e:
                                session.rollback()
                                #print(f"IntegrityError caught: {e}")
                        else:
                            print(f'{paths[depth]} or {paths[depth2]} not found')
            #print(count)

        return species_list


def get_collections(library_id, to_depth):
    data = []
    conf = get_config(library_id)
    levels = conf['collection'].get('levels').split(',')
    last_collection_level = len(levels)-2

    def get_closures(ancestor_id, current_level):
        current_level += 1
        if current_level <= to_depth:
            children = []
            descendants = CollectionClosure.query.filter(CollectionClosure.ancestor_id==ancestor_id, CollectionClosure.depth==1).all()
            for d in descendants:
                child = {
                    'name': d.descendant.name,
                    'name_zh': d.descendant.name_zh,
                    'id': d.descendant.id,
                    'children': get_closures(d.descendant_id, current_level),
                    'level': levels[current_level],
                    'count': count_collection_items(d.descendant_id),
                }
                children.append(child)

            return children

    collections = Collection.query.filter(Collection.level==levels[0], Collection.library_id==library_id).order_by(Collection.name).all()
    for i in collections:
        children = get_closures(i.id, 0)
        data.append({
            'name': i.name,
            'name_zh': i.name_zh,
            'id': i.id,
            'children': children,
            'level': levels[0],
            'count': count_collection_items(i.id),
        })

    return data


def count_collection_items(ancestor_id):
    collection = session.get(Collection, ancestor_id)
    if collection.library_id == 1: # species rules, filter field_id=1 and value = 1
        stmt = (
            select(
                func.count(CollectionItem.id)
            )
            .select_from(CollectionClosure)
            .join(
                CollectionItem,
                CollectionItem.collection_id == CollectionClosure.descendant_id,
                isouter=True
            )
            .join(
                ItemData,
                ItemData.item_id == CollectionItem.item_id,
                isouter=True
            )
            .where(
                CollectionClosure.ancestor_id == ancestor_id,
                ItemData.value == '1'
            )
        )
    else:
        stmt = (
            select(
                func.count(CollectionItem.id)
            )
            .select_from(CollectionClosure)
            .join(
                CollectionItem,
                CollectionItem.collection_id == CollectionClosure.descendant_id,
                isouter=True
            )
            .where(
                CollectionClosure.ancestor_id == ancestor_id
            )
        )

    count = session.execute(stmt).scalar()
    return count
