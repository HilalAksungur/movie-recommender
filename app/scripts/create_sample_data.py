from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import random
from datetime import datetime, timedelta

from app.models.models import User, Movie, Rating, WatchedMovie
from app.database.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sample data
genres = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance", "Thriller", "Fantasy", "Animation", "Adventure", "Crime", "Mystery", "Documentary"]
movies = [
    # Sci-Fi
    ("The Matrix", "Sci-Fi"),
    ("Inception", "Sci-Fi"),
    ("Interstellar", "Sci-Fi"),
    ("Star Wars: A New Hope", "Sci-Fi"),
    ("Blade Runner", "Sci-Fi"),
    ("The Terminator", "Sci-Fi"),
    ("Avatar", "Sci-Fi"),
    ("Dune", "Sci-Fi"),
    ("The Fifth Element", "Sci-Fi"),
    ("District 9", "Sci-Fi"),
    
    # Action
    ("The Dark Knight", "Action"),
    ("Die Hard", "Action"),
    ("Mad Max: Fury Road", "Action"),
    ("John Wick", "Action"),
    ("The Avengers", "Action"),
    ("Mission: Impossible", "Action"),
    ("The Bourne Identity", "Action"),
    ("Gladiator", "Action"),
    ("Kill Bill", "Action"),
    ("The Raid", "Action"),
    
    # Drama
    ("The Shawshank Redemption", "Drama"),
    ("The Godfather", "Drama"),
    ("Forrest Gump", "Drama"),
    ("Pulp Fiction", "Drama"),
    ("Schindler's List", "Drama"),
    ("Fight Club", "Drama"),
    ("Goodfellas", "Drama"),
    ("The Green Mile", "Drama"),
    ("The Departed", "Drama"),
    ("American Beauty", "Drama"),
    
    # Horror
    ("The Shining", "Horror"),
    ("The Exorcist", "Horror"),
    ("Get Out", "Horror"),
    ("Hereditary", "Horror"),
    ("A Quiet Place", "Horror"),
    ("The Conjuring", "Horror"),
    ("It", "Horror"),
    ("The Babadook", "Horror"),
    ("Sinister", "Horror"),
    ("Insidious", "Horror"),
    
    # Comedy
    ("The Hangover", "Comedy"),
    ("Superbad", "Comedy"),
    ("Bridesmaids", "Comedy"),
    ("Anchorman", "Comedy"),
    ("Step Brothers", "Comedy"),
    ("The Grand Budapest Hotel", "Comedy"),
    ("Airplane!", "Comedy"),
    ("Monty Python and the Holy Grail", "Comedy"),
    ("The Big Lebowski", "Comedy"),
    ("Groundhog Day", "Comedy"),
    
    # Romance
    ("Titanic", "Romance"),
    ("The Notebook", "Romance"),
    ("Pride and Prejudice", "Romance"),
    ("La La Land", "Romance"),
    ("Before Sunrise", "Romance"),
    ("Eternal Sunshine of the Spotless Mind", "Romance"),
    ("500 Days of Summer", "Romance"),
    ("The Fault in Our Stars", "Romance"),
    ("Crazy, Stupid, Love", "Romance"),
    ("About Time", "Romance"),
    
    # Fantasy
    ("The Lord of the Rings: The Fellowship of the Ring", "Fantasy"),
    ("Harry Potter and the Sorcerer's Stone", "Fantasy"),
    ("Pan's Labyrinth", "Fantasy"),
    ("The Princess Bride", "Fantasy"),
    ("Stardust", "Fantasy"),
    ("The NeverEnding Story", "Fantasy"),
    ("Willow", "Fantasy"),
    ("The Dark Crystal", "Fantasy"),
    ("Labyrinth", "Fantasy"),
    ("The Chronicles of Narnia", "Fantasy"),
    
    # Animation
    ("Toy Story", "Animation"),
    ("Finding Nemo", "Animation"),
    ("The Lion King", "Animation"),
    ("Spirited Away", "Animation"),
    ("Up", "Animation"),
    ("Wall-E", "Animation"),
    ("Inside Out", "Animation"),
    ("Coco", "Animation"),
    ("Zootopia", "Animation"),
    ("How to Train Your Dragon", "Animation"),
    
    # Adventure
    ("Indiana Jones: Raiders of the Lost Ark", "Adventure"),
    ("Jurassic Park", "Adventure"),
    ("Pirates of the Caribbean", "Adventure"),
    ("The Goonies", "Adventure"),
    ("Jumanji", "Adventure"),
    ("The Mummy", "Adventure"),
    ("National Treasure", "Adventure"),
    ("The Jungle Book", "Adventure"),
    ("Hook", "Adventure"),
    ("The Princess Bride", "Adventure"),
    
    # Thriller
    ("Se7en", "Thriller"),
    ("The Silence of the Lambs", "Thriller"),
    ("Gone Girl", "Thriller"),
    ("Shutter Island", "Thriller"),
    ("The Sixth Sense", "Thriller"),
    ("Memento", "Thriller"),
    ("Zodiac", "Thriller"),
    ("The Girl with the Dragon Tattoo", "Thriller"),
    ("Prisoners", "Thriller"),
    ("The Prestige", "Thriller"),
]

def create_sample_data():
    db = SessionLocal()
    
    try:
        # Clean up existing data
        db.query(WatchedMovie).delete()
        db.query(Rating).delete()
        db.query(Movie).delete()
        db.query(User).delete()
        db.commit()
        
        # Reset sequence for users table
        db.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
        db.commit()
        
        # Create users
        users = []
        for i in range(50):  # Create 50 users
            user = User(username=f"user{i+1}")
            db.add(user)
            users.append(user)
        db.commit()
        
        # Create movies
        movie_objects = []
        for title, genre in movies:
            movie = Movie(title=title, genre=genre)
            db.add(movie)
            movie_objects.append(movie)
        db.commit()
        
        # Create ratings and watch history
        for user in users:
            # Each user rates 5-10 random movies
            num_ratings = random.randint(5, 10)
            rated_movies = random.sample(movie_objects, num_ratings)
            
            for movie in rated_movies:
                rating = Rating(
                    user_id=user.id,
                    movie_id=movie.id,
                    rating=random.uniform(1.0, 5.0)
                )
                db.add(rating)
                
                # Add to watch history
                watched = WatchedMovie(
                    user_id=user.id,
                    movie_id=movie.id,
                    watched_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                )
                db.add(watched)
        
        # Add more watched movies for user 1 (7-8 movies)
        user1 = users[0]  # First user (ID: 1)
        additional_movies = random.sample([m for m in movie_objects if m not in rated_movies], 8)
        for movie in additional_movies:
            if not any(wm.movie_id == movie.id for wm in user1.watched_movies):
                watched = WatchedMovie(
                    user_id=user1.id,
                    movie_id=movie.id,
                    watched_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                )
                db.add(watched)
        
        db.commit()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data() 