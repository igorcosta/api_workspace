from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Auxiliary table for many-to-many relationship between users and workspaces
user_workspace_association = Table('user_workspace', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('workspace_id', Integer, ForeignKey('workspaces.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    profiles = relationship("Profile", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    workspaces = relationship("Workspace", secondary=user_workspace_association, back_populates="users")

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    bio = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="profiles")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="tasks")

class Workspace(Base):
    __tablename__ = 'workspaces'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", secondary=user_workspace_association, back_populates="workspaces")
