#! /src/python/bin

import os
import sys
import datetime
# include sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# database will require 3 tables - one to store user data, one for item data, one for category data

# User Class
class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250))
    picture = Column(String(250))

    @property
    def seralize(self):
        return {
            'id'    : self.id,
            'name'  : self.name,
            'email' : self.email,
            'picture'  : self.picture
        }

# Category Class
class Category(Base):
    __tablename__ = 'Categories'

    name = Column(String(255), nullable=False)
    id = Column(Integer, primary_key = True)

# Item Class
class Item(Base):
    __tablename__ = 'Items'

    name = Column(String(255), nullable = False)
    id = Column(Integer, primary_key = True)
    category_id = Column(Integer,ForeignKey('Categories.id'))
    category = relationship(Category)
    owner_id = Column(Integer,ForeignKey('Users.id'))
    owner = relationship(User)
    mint = Column(String(255))
    description = Column(String(255))
    image = Column(String(255))

    @property
    def serialize(self):
        return {
        'name'          : self.name,
        'id'            : self.id,
        'category_id'   : self.category_id,
        'owner_id'      : self.owner_id,
        'description'   : self.description,
        'image'         : self.image,
        'mint'          : self.mint
        }
# create database engine
engine = create_engine('sqlite:///bullion.db')

Base.metadata.create_all(engine)