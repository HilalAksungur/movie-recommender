from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from app.models.models import Base, User, Movie, Rating, WatchedMovie
from app.recommender import MovieRecommender
from pydantic import BaseModel
import random
import string
from sqlalchemy import func
import numpy as np
from datetime import datetime, timedelta
from typing import List

load_dotenv()

app = FastAPI(title="Movie Recommender API")

# Database setup
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize recommender
recommender = None

def get_recommender(db: Session = Depends(get_db)):
    global recommender
    if recommender is None:
        recommender = MovieRecommender(db)
    return recommender

class UserCreate(BaseModel):
    username: str

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/movies/")
def create_movie(title: str, genre: str, db: Session = Depends(get_db)):
    db_movie = Movie(title=title, genre=genre)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.post("/ratings/")
def create_rating(user_id: int, movie_id: int, rating: float, db: Session = Depends(get_db)):
    db_rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

def get_user_ratings(db: Session, user_id: int):
    return db.query(Rating).filter(Rating.user_id == user_id).all()

def get_user_watched_movies(db: Session, user_id: int):
    return db.query(WatchedMovie).filter(WatchedMovie.user_id == user_id).all()

def get_movie_ratings(db: Session, movie_id: int):
    return db.query(Rating).filter(Rating.movie_id == movie_id).all()

def get_movie(db: Session, movie_id: int):
    return db.query(Movie).filter(Movie.id == movie_id).first()

def get_all_movies(db: Session):
    return db.query(Movie).all()

def calculate_similarity(user1_ratings: List[Rating], user2_ratings: List[Rating]):
    # Convert ratings to dictionaries for easier lookup
    user1_ratings_dict = {r.movie_id: r.rating for r in user1_ratings}
    user2_ratings_dict = {r.movie_id: r.rating for r in user2_ratings}
    
    # Find common movies
    common_movies = set(user1_ratings_dict.keys()) & set(user2_ratings_dict.keys())
    
    # En az 2 ortak film olmalı
    if len(common_movies) < 2:
        return 0.0
    
    # Calculate similarity using Pearson correlation
    user1_ratings_list = [user1_ratings_dict[movie_id] for movie_id in common_movies]
    user2_ratings_list = [user2_ratings_dict[movie_id] for movie_id in common_movies]
    
    # Tüm puanlar aynıysa veya varyans yoksa benzerlik 0
    if len(set(user1_ratings_list)) == 1 or len(set(user2_ratings_list)) == 1:
        return 0.0
    
    try:
        # Normalize ratings
        user1_mean = np.mean(user1_ratings_list)
        user2_mean = np.mean(user2_ratings_list)
        user1_std = np.std(user1_ratings_list)
        user2_std = np.std(user2_ratings_list)
        
        if user1_std == 0 or user2_std == 0:
            return 0.0
            
        user1_normalized = [(x - user1_mean) / user1_std for x in user1_ratings_list]
        user2_normalized = [(x - user2_mean) / user2_std for x in user2_ratings_list]
        
        # Calculate correlation
        correlation = np.corrcoef(user1_normalized, user2_normalized)[0, 1]
        
        # Handle NaN values
        if np.isnan(correlation):
            return 0.0
            
        return correlation
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

def get_recommendations_for_user(db: Session, user_id: int, n_recommendations: int = 5):
    # Get user's watched movies
    watched_movies = get_user_watched_movies(db, user_id)
    watched_movie_ids = {wm.movie_id for wm in watched_movies}
    print(f"User {user_id} has watched {len(watched_movie_ids)} movies")
    
    # Get user's ratings
    user_ratings = get_user_ratings(db, user_id)
    print(f"User {user_id} has {len(user_ratings)} ratings")
    
    if not user_ratings:
        print(f"User {user_id} has no ratings, returning popular movies")
        return get_recommendations_for_new_user(db, n_recommendations)
    
    # Get all other users
    all_users = db.query(User).filter(User.id != user_id).all()
    print(f"Found {len(all_users)} other users")
    
    # Calculate similarity with other users
    user_similarities = []
    for other_user in all_users:
        other_user_ratings = get_user_ratings(db, other_user.id)
        if other_user_ratings:  # Only consider users with ratings
            similarity = calculate_similarity(user_ratings, other_user_ratings)
            if similarity > 0:  # Only consider positive correlations
                user_similarities.append((other_user.id, similarity))
    
    print(f"Found {len(user_similarities)} similar users")
    
    if not user_similarities:
        print("No similar users found, returning popular movies")
        return get_recommendations_for_new_user(db, n_recommendations)
    
    # Sort by similarity
    user_similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get top similar users
    top_users = user_similarities[:10]  # Consider top 10 similar users
    print(f"Top similar users: {top_users}")
    
    # Get movies rated by similar users
    recommended_movies = {}
    for user_id, similarity in top_users:
        user_ratings = get_user_ratings(db, user_id)
        for rating in user_ratings:
            if rating.movie_id not in watched_movie_ids:  # Only recommend unwatched movies
                if rating.movie_id not in recommended_movies:
                    recommended_movies[rating.movie_id] = []
                recommended_movies[rating.movie_id].append(rating.rating * similarity)
    
    print(f"Found {len(recommended_movies)} potential recommendations")
    
    if not recommended_movies:
        print("No recommendations found, returning popular movies")
        return get_recommendations_for_new_user(db, n_recommendations)
    
    # Calculate weighted average ratings
    movie_scores = []
    for movie_id, weighted_ratings in recommended_movies.items():
        avg_rating = sum(weighted_ratings) / len(weighted_ratings)
        movie_scores.append((movie_id, avg_rating))
    
    # Sort by score
    movie_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top recommendations
    top_movie_ids = [movie_id for movie_id, _ in movie_scores[:n_recommendations]]
    recommendations = []
    for movie_id in top_movie_ids:
        movie = get_movie(db, movie_id)
        if movie:
            recommendations.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre
            })
    
    print(f"Returning {len(recommendations)} recommendations")
    return recommendations

def get_recommendations_for_new_user(db: Session, n_recommendations: int = 5):
    # Get all movies
    all_movies = get_all_movies(db)
    
    # Get average ratings for each movie
    movie_scores = []
    for movie in all_movies:
        ratings = get_movie_ratings(db, movie.id)
        if ratings:
            avg_rating = sum(r.rating for r in ratings) / len(ratings)
            movie_scores.append((movie.id, avg_rating))
    
    # Sort by average rating
    movie_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top recommendations
    top_movie_ids = [movie_id for movie_id, _ in movie_scores[:n_recommendations]]
    recommendations = []
    for movie_id in top_movie_ids:
        movie = get_movie(db, movie_id)
        if movie:
            recommendations.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre
            })
    
    return recommendations

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, n_recommendations: int = 5, db: Session = Depends(get_db)):
    if user_id == "new-user":
        return get_recommendations_for_new_user(db, n_recommendations)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return get_recommendations_for_user(db, user_id, n_recommendations)

@app.get("/recommendations/new-user/")
def get_new_user_recommendations(n_recommendations: int = 5, db: Session = Depends(get_db)):
    return get_recommendations_for_new_user(db, n_recommendations)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 