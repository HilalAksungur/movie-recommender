from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    ratings = relationship("Rating", back_populates="user")
    watched_movies = relationship("WatchedMovie", back_populates="user")

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    genre = Column(String)
    ratings = relationship("Rating", back_populates="movie")
    watched_by = relationship("WatchedMovie", back_populates="movie")

class Rating(Base):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    rating = Column(Float)
    
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

class WatchedMovie(Base):
    __tablename__ = 'watched_movies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    watched_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="watched_movies")
    movie = relationship("Movie", back_populates="watched_by") 