# Movie Recommender System

This project is a web application that provides personalized movie recommendations based on user ratings and watch history.

## Features

- User-based movie recommendations
- Popular movie recommendations for new users
- Movie rating system
- Watch history tracking
- Similar user-based recommendations

## Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Configure database settings:
```bash
cp .env.example .env
```
Edit the `.env` file with your database credentials.

3. Create database and load sample data:
```bash
python3 -m app.scripts.create_sample_data
```

4. Start the application:
```bash
python3 -m uvicorn app.main:app --reload
```

## API Endpoints

### User Operations
- `POST /users/`: Create a new user
- `POST /movies/`: Add a new movie
- `POST /ratings/`: Rate a movie

### Recommendation Systems
- `GET /recommendations/{user_id}`: Get recommendations for a specific user
- `GET /recommendations/new-user/`: Get popular movies for new users

## Example Usage

1. Create a new user:
```bash
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"username": "test_user"}'
```

2. Rate a movie:
```bash
curl -X POST "http://localhost:8000/ratings/?user_id=1&movie_id=1&rating=5"
```

3. Get recommendations:
```bash
curl "http://localhost:8000/recommendations/1?n_recommendations=5"
```

## Project Structure

```
movie-recommender/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main application and API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # Database models
│   ├── recommender.py       # Recommendation system
│   └── scripts/
│       ├── __init__.py
│       └── create_sample_data.py  # Sample data generation
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Technologies

- FastAPI: Web framework
- SQLAlchemy: ORM
- NumPy: Mathematical operations
- scikit-learn: K-means clustering
- PostgreSQL: Database

## Recommendation System Algorithm

1. User-based collaborative filtering:
   - Calculate similarity based on user ratings
   - Recommend movies watched by similar users

2. For new users:
   - Recommend highest rated movies
   - Recommend popular movies

## Contributing

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Contributors
     GYK-2
- HİLAL AKSUNGUR BÜYÜKYEKDELİ
- GÖZDE DİLAVER
- GAMZE KEVSER TEMÜR

