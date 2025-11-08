from typing import (
    Optional,
    Dict,
    Any,
)
import uuid
import json
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Text,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    Table,
    desc,
    select,
    func,
    UUID,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import (
    relationship,
    backref,
    validates,
    Mapped,
    mapped_column,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.database import (
    Base,
    session,
)

# Mapped[Optional[str]] 會自動設定 nullable=True
# nickname: Mapped[Optional[str]]


class TimestampMixin(object):
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncMixin(object):
    key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4
    )
    version: Mapped[int] = mapped_column(default=1)

class ItemTypeField(Base):
    __tablename__ = 'item_type_field'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type_id: Mapped[int] = mapped_column(ForeignKey('item_type.id'))
    field_id: Mapped[int] = mapped_column(ForeignKey('field.id'))
    sort: Mapped[Optional[int]] = mapped_column(SmallInteger)
    control_id: Mapped[Optional[int]] = mapped_column(SmallInteger) # 0: hide, 1: display
    # sort value
    # 0-9: taxon, nomenclature
    # 10-19: description, distribution..
    # 20-29: annotation

    field: Mapped['Field'] = relationship('Field')


class Field(Base):
    __tablename__ = 'field'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    label: Mapped[Optional[str]] = mapped_column(String(500))


class ItemType(Base):
    __tablename__ = 'item_type'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))


    fields: Mapped[list['Field']] = relationship(
        'Field',
        secondary='item_type_field',
        primaryjoin='ItemType.id == ItemTypeField.item_type_id',
        viewonly=True,
        lazy='selectin',
        order_by='ItemTypeField.sort'
    )


class Item(Base, TimestampMixin, SyncMixin):
    __tablename__ = 'item'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    name_zh: Mapped[Optional[str]] = mapped_column(String(500))
    item_type_id: Mapped[int] = mapped_column(ForeignKey('item_type.id'))
    library_id: Mapped[int] = mapped_column(ForeignKey('library.id'))
    source_data: Mapped[Dict[str, Any]] = mapped_column(JSONB)

    item_type: Mapped['ItemType'] = relationship('ItemType')

    # Relationship to collections through CollectionItem
    collection_items: Mapped[list['CollectionItem']] = relationship(
        'CollectionItem',
        back_populates='item',
        lazy='selectin'
    )

    # Direct access to collections via the association table
    collections: Mapped[list['Collection']] = relationship(
        'Collection',
        secondary='collection_item',
        primaryjoin='Item.id == CollectionItem.item_id',
        secondaryjoin='Collection.id == CollectionItem.collection_id',
        viewonly=True,
        lazy='selectin'
    )

    data_values: Mapped[list['ItemData']] = relationship('ItemData')

    @property
    def pretty_source_data(self):
        if x := self.source_data:
            return json.dumps(x, indent=2)


    @property
    def higher_collections(self):
        if a := self.collections:
            cc = CollectionClosure.query.filter(CollectionClosure.descendant_id==a[0].id).order_by(desc(CollectionClosure.depth)).all()
            return [x.ancestor for x in cc]

    @property
    def field_data(self):
        from app.helpers.library import get_config
        data = []
        field_values = {}

        for x in self.data_values:
            field_values[x.field_id] = x.value

        config = get_config(self.library_id)

        # apply values, by item_type (like template)
        item_type_fields = ItemTypeField.query.filter(ItemTypeField.item_type_id==self.item_type_id).all()
        #for field in self.item_type.fields: # I need control_id
        for m in item_type_fields:
            field = m.field

            value = ''
            if field.id in field_values:
                value = field_values[field.id]

            # overwrite by source_data
            if 'item_source_data_field' in config :
                for key, field_id in config['item_source_data_field'].items():
                    if str(field_id) == str(field.id):
                        if x := self.source_data.get(key):
                            value = x
                            break

            data.append({
                'id': field.id,
                'name': field.name,
                'label': field.label,
                'value': value,
                'control_id': m.control_id,
            })

        return data

class ItemData(Base):
    __tablename__ = 'item_data'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'))
    field_id: Mapped[int] = mapped_column(ForeignKey('field.id'))
    value: Mapped[str] = mapped_column(Text)


class Library(Base):
    __tablename__ = 'library'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    host: Mapped[Optional[str]] = mapped_column(String(500))
    title: Mapped[Optional[str]] = mapped_column(String(500))

class Collection(Base, SyncMixin):
    __tablename__ = 'collection'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    name_zh: Mapped[Optional[str]] = mapped_column(String(500))
    library_id: Mapped[int] = mapped_column(ForeignKey('library.id'))
    level: Mapped[str] = mapped_column(String(500))

    # Relationships to traverse the hierarchy through the closure table
    # These are 'viewonly' because we will manage the closure table manually.
    descendants: Mapped[list['Collection']] = relationship(
        'Collection',
        secondary='collection_closure',
        primaryjoin='Collection.id == CollectionClosure.ancestor_id',
        secondaryjoin='Collection.id == CollectionClosure.descendant_id',
        viewonly=True,
    )

    ancestors: Mapped[list['Collection']] = relationship(
        'Collection',
        secondary='collection_closure',
        primaryjoin='Collection.id == CollectionClosure.descendant_id',
        secondaryjoin='Collection.id == CollectionClosure.ancestor_id',
        viewonly=True,
    )

    # Relationship to items through CollectionItem
    collection_items: Mapped[list['CollectionItem']] = relationship(
        'CollectionItem',
        back_populates='collection',
        lazy='selectin'
    )

    # Direct access to items via the association table
    items: Mapped[list['Item']] = relationship(
        'Item',
        secondary='collection_item',
        primaryjoin='Collection.id == CollectionItem.collection_id',
        secondaryjoin='Item.id == CollectionItem.item_id',
        viewonly=True,
        lazy='selectin'
    )

class CollectionItem(Base, SyncMixin):
    __tablename__ = 'collection_item'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'))
    collection_id: Mapped[int] = mapped_column(ForeignKey('collection.id'))
    library_id: Mapped[int] = mapped_column(ForeignKey('library.id'))

    # Bidirectional relationships with back_populates
    collection: Mapped['Collection'] = relationship(
        'Collection',
        back_populates='collection_items'
    )
    item: Mapped['Item'] = relationship(
        'Item',
        back_populates='collection_items'
    )


class CollectionClosure(Base):
    __tablename__ = 'collection_closure'

    ancestor_id: Mapped[int] = mapped_column(ForeignKey('collection.id'))
    descendant_id: Mapped[int] = mapped_column(ForeignKey('collection.id'))
    depth: Mapped[int] = mapped_column(SmallInteger)

    ancestor: Mapped['Collection'] = relationship('Collection', primaryjoin='Collection.id == CollectionClosure.ancestor_id')
    descendant: Mapped['Collection'] = relationship('Collection', primaryjoin='Collection.id == CollectionClosure.descendant_id')

    __table_args__ = (
        PrimaryKeyConstraint('ancestor_id', 'descendant_id', name='collection_closure_pk'),
    )
