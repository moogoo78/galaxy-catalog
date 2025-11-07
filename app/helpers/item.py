from sqlalchemy import (
    select,
    func,
    or_,
)

from app.models import (
    Item,
    ItemData,
    CollectionClosure,
    CollectionItem,
)
from app.database import session

def get_items(library_id, filtr={}, limit=0, offset=0):

    stmt = (
        select(
            Item
        )
        .join(
            ItemData,
            ItemData.item_id == Item.id,
        )
        .where(
            Item.library_id == library_id,
        )
    )
    ## TODO!
    if library_id == 1:
        stmt = stmt.where(
            ItemData.value == '1',
            ItemData.field_id == 1
        )


    if q := filtr.get('q'):
        stmt = stmt.where(or_(
            Item.name.ilike(f'%{q}%'),
            Item.name_zh.ilike(f'%{q}%'),
        ))
    if collection_id := filtr.get('collection_id'):
        stmt_c = (
            select(
                CollectionClosure.descendant_id
            )
            .where(
                CollectionClosure.ancestor_id == collection_id
            )
        )
        collection_ids = session.execute(stmt_c).scalars().all()
        stmt_i = (
            select(
                CollectionItem.item_id,
            )
            .where(
                CollectionItem.collection_id.in_(collection_ids)
            )
        )
        item_ids = session.execute(stmt_i).scalars().all()
        if len(item_ids):
            stmt = stmt.where(Item.id.in_(item_ids))

    base_stmt = stmt
    subquery = base_stmt.subquery()
    count_stmt = select(func.count()).select_from(subquery)
    total = session.execute(count_stmt).scalar()
    stmt = base_stmt.limit(limit).offset(offset)
    items = session.execute(stmt).scalars().all()

    return {
        'items': items,
        'total': total,
    }
