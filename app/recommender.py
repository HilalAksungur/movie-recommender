import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from app.models.models import User, Movie, Rating
import pandas as pd
from typing import List, Dict, Optional

class MovieRecommender:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.kmeans = None
        self.user_clusters = None
        self.movie_clusters = None
        self.user_ids = None
        self.movie_ids = None
        
    def prepare_data(self):
        # Get all ratings
        ratings = self.db_session.query(Rating).all()
        print(f"Found {len(ratings)} ratings in total")
        
        if not ratings:
            print("No ratings found in database")
            return None
        
        # Create user-movie matrix
        users = self.db_session.query(User).all()
        movies = self.db_session.query(Movie).all()
        print(f"Found {len(users)} users and {len(movies)} movies")
        
        if not users or not movies:
            print("No users or movies found in database")
            return None
        
        self.user_ids = [user.id for user in users]
        self.movie_ids = [movie.id for movie in movies]
        
        # Create empty matrix
        matrix = np.zeros((len(self.user_ids), len(self.movie_ids)))
        
        # Fill matrix with ratings
        rating_count = 0
        for rating in ratings:
            try:
                user_idx = self.user_ids.index(rating.user_id)
                movie_idx = self.movie_ids.index(rating.movie_id)
                matrix[user_idx, movie_idx] = rating.rating
                rating_count += 1
            except ValueError as e:
                print(f"Error processing rating: {e}")
                continue
        
        print(f"Successfully processed {rating_count} ratings")
        
        # Remove users with no ratings
        non_zero_rows = np.any(matrix != 0, axis=1)
        matrix = matrix[non_zero_rows]
        self.user_ids = [self.user_ids[i] for i in range(len(self.user_ids)) if non_zero_rows[i]]
        print(f"Users after removing zero rows: {len(self.user_ids)}")
        
        # Remove movies with no ratings
        non_zero_cols = np.any(matrix != 0, axis=0)
        matrix = matrix[:, non_zero_cols]
        self.movie_ids = [self.movie_ids[i] for i in range(len(self.movie_ids)) if non_zero_cols[i]]
        print(f"Movies after removing zero columns: {len(self.movie_ids)}")
        
        print(f"Matrix shape after cleaning: {matrix.shape}")
        print(f"Non-zero elements: {np.count_nonzero(matrix)}")
        
        if matrix.shape[0] < 2 or matrix.shape[1] < 2:
            print("Not enough data for clustering")
            return None
            
        return matrix
        
    def train(self, n_clusters=3):
        matrix = self.prepare_data()
        
        if matrix is None:
            print("Could not prepare data for training")
            return
            
        # Normalize the matrix
        matrix = (matrix - np.mean(matrix)) / (np.std(matrix) + 1e-10)
        
        # Train KMeans on user preferences
        try:
            n_clusters = min(n_clusters, matrix.shape[0]-1)
            print(f"Training with {n_clusters} clusters")
            
            self.kmeans = KMeans(n_clusters=n_clusters, 
                               random_state=42, 
                               n_init=10)
            self.user_clusters = self.kmeans.fit_predict(matrix)
            print(f"User clusters: {self.user_clusters}")
            
            # Train KMeans on movie features
            self.movie_clusters = self.kmeans.fit_predict(matrix.T)
            print(f"Movie clusters: {self.movie_clusters}")
            
            # Print cluster sizes
            user_cluster_sizes = np.bincount(self.user_clusters)
            movie_cluster_sizes = np.bincount(self.movie_clusters)
            print(f"User cluster sizes: {user_cluster_sizes}")
            print(f"Movie cluster sizes: {movie_cluster_sizes}")
            
        except Exception as e:
            print(f"Error during training: {e}")
            self.kmeans = None
            self.user_clusters = None
            self.movie_clusters = None
            
    def get_recommendations(self, user_id: int, n_recommendations: int = 5):
        if self.kmeans is None:
            print("Training recommender...")
            self.train()
            
        print(f"Getting recommendations for user {user_id}")
        
        try:
            # Get user's watched movies
            user_ratings = self.db_session.query(Rating).filter(Rating.user_id == user_id).all()
            rated_movie_ids = [rating.movie_id for rating in user_ratings]
            print(f"User has rated {len(rated_movie_ids)} movies")
            
            if not rated_movie_ids:
                print("User has no ratings, returning popular movies")
                return self.get_recommendations_for_new_user(n_recommendations)
            
            # Get user's cluster
            try:
                user_idx = self.user_ids.index(user_id)
                user_cluster = self.user_clusters[user_idx]
                print(f"User is in cluster {user_cluster}")
            except ValueError:
                print("User not found in clusters, returning popular movies")
                return self.get_recommendations_for_new_user(n_recommendations)
            
            # Get movies from the same cluster
            cluster_movies = np.where(self.movie_clusters == user_cluster)[0]
            print(f"Found {len(cluster_movies)} movies in the same cluster")
            
            # Filter out rated movies
            recommended_movie_ids = [self.movie_ids[i] for i in cluster_movies 
                                   if self.movie_ids[i] not in rated_movie_ids]
            print(f"Found {len(recommended_movie_ids)} unrated movies in the cluster")
            
            # If we don't have enough recommendations, add some from other clusters
            if len(recommended_movie_ids) < n_recommendations:
                print("Not enough movies in the same cluster, adding from other clusters")
                all_movies = set(self.movie_ids) - set(rated_movie_ids)
                additional_movies = list(all_movies - set(recommended_movie_ids))
                recommended_movie_ids.extend(additional_movies)
            
            # Get movie details
            recommended_movies = self.db_session.query(Movie).filter(
                Movie.id.in_(recommended_movie_ids[:n_recommendations])
            ).all()
            
            print(f"Returning {len(recommended_movies)} recommendations")
            return recommended_movies
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return self.get_recommendations_for_new_user(n_recommendations)
    
    def get_recommendations_for_new_user(self, n_recommendations: int = 5):
        if self.kmeans is None:
            self.train()
            
        print("Getting recommendations for new user")
        
        try:
            # Get the largest cluster
            cluster_sizes = np.bincount(self.movie_clusters)
            largest_cluster = np.argmax(cluster_sizes)
            print(f"Largest cluster is {largest_cluster} with {cluster_sizes[largest_cluster]} movies")
            
            # Get movies from the largest cluster
            cluster_movies = np.where(self.movie_clusters == largest_cluster)[0]
            recommended_movie_ids = [self.movie_ids[i] for i in cluster_movies[:n_recommendations]]
            print(f"Found {len(recommended_movie_ids)} movies in the largest cluster")
            
            # Get movie details
            recommended_movies = self.db_session.query(Movie).filter(
                Movie.id.in_(recommended_movie_ids)
            ).all()
            
            print(f"Returning {len(recommended_movies)} recommendations")
            return recommended_movies
            
        except Exception as e:
            print(f"Error getting recommendations for new user: {e}")
            return []