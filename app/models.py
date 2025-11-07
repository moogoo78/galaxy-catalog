from datetime import datetime
from typing import (
    Optional,
    Dict,
    Any,
)
import uuid

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

class Field(Base):
    __tablename__ = 'field'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))


class ItemType(Base):
    __tablename__ = 'item_type'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))


class Item(Base, TimestampMixin, SyncMixin):
    __tablename__ = 'item'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    name_zh: Mapped[Optional[str]] = mapped_column(String(500))
    item_type_id: Mapped[int] = mapped_column(ForeignKey('item_type.id'))
    library_id: Mapped[int] = mapped_column(ForeignKey('library.id'))
    source_data: Mapped[Dict[str, Any]] = mapped_column(JSONB)

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

class CollectionItem(Base, SyncMixin):
    __tablename__ = 'collection_item'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'))
    collection_id: Mapped[int] = mapped_column(ForeignKey('collection.id'))
    library_id: Mapped[int] = mapped_column(ForeignKey('library.id'))


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
