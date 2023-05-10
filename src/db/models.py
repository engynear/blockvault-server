from sqlalchemy import Column, Integer, String, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship

from db.base import Base

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))


class Sound(Base):
    __tablename__ = "sounds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    description = Column(Text)


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