from django.urls import path
from .views import MovieScrapAPI, MovieListAPI, MovieSearchAPI

urlpatterns = [
    path("movies/scrap/", MovieScrapAPI.as_view(), name="movie-scrap"),
    path("movies/", MovieListAPI.as_view(), name="movie-list"),
    path("movies/search/", MovieSearchAPI.as_view(), name="movie-search"),
]
