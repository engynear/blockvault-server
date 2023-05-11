from sqlalchemy import Column, Integer, String, Text, ForeignKey, ARRAY, Table
from sqlalchemy.orm import relationship

from db.base import Base

resourcepack_models = Table('resourcepack_models', Base.metadata,
    Column('resourcepack_id', Integer, ForeignKey('resourcepacks.id')),
    Column('model_id', Integer, ForeignKey('models.id'))
)

resourcepack_sounds = Table('resourcepack_sounds', Base.metadata,
    Column('resourcepack_id', Integer, ForeignKey('resourcepacks.id')),
    Column('sound_id', Integer, ForeignKey('sounds.id'))
)

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))

    resourcepacks = relationship(
        'Resourcepack',
        secondary=resourcepack_models,
        back_populates='models'
    )

class Sound(Base):
    __tablename__ = "sounds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    description = Column(Text)
    tags = Column(ARRAY(String))

    resourcepacks = relationship(
        'Resourcepack',
        secondary=resourcepack_sounds,
        back_populates='sounds'
    )

class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    version = Column(String)
    description = Column(Text)

class Resourcepack(Base):
    __tablename__ = "resourcepacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    version = Column(String)
    description = Column(Text)

    models = relationship(
        'Model',
        secondary=resourcepack_models,
        back_populates='resourcepacks'
    )
    sounds = relationship(
        'Sound',
        secondary=resourcepack_sounds,
        back_populates='resourcepacks'
    )