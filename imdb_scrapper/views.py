from typing import List

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from django.db import transaction
from django.db.models import Q

from .models import Movie, Person, MovieDirector, MovieWriter, MovieStar
from .serializers import MovieSerializer


class MoviePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class MovieScrapAPI(APIView):
    def post(self, request):
        # Extract parameters from request
        query = request.GET.get("query")
        max_pages = request.GET.get("max_pages")

        # Validate required parameters
        if not all([query, max_pages]):
            return Response(
                {"error": "Missing required parameters: query, or max_pages"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            max_pages = int(max_pages)
        except ValueError:
            return Response(
                {
                    "error": "Invalid parameter type",
                    "details": "max_pages must be a number",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate max_pages range
        if not (max_pages > 0 and max_pages <= 10):
            return Response(
                {
                    "error": "Invalid parameter value",
                    "details": "max_pages must be between 1 and 10",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .scrapper import (
                IMDbScraper,
                MovieDetails,
            )  # Import here to avoid circular imports

            scrapper = IMDbScraper(max_workers=10)
            movies_data: List[MovieDetails] = scrapper.search_and_get_details(
                query, max_pages
            )

            duplicate_movies = []

            # Use transaction to ensure data consistency
            with transaction.atomic():
                movies_added = 0

                for movie_detail in movies_data:
                    # Create or get the movie
                    # TODO: Instead of using movie name to detect duplicate movies, I should collect some id from imdb and use that
                    movie, created = Movie.objects.get_or_create(
                        title=movie_detail.title,
                        defaults={
                            "release_year": movie_detail.release_year,
                            "rating": movie_detail.rating,
                            "plot": movie_detail.plot,
                        },
                    )

                    if created:
                        movies_added += 1

                    if not created:
                        duplicate_movies.append(movie_detail.title)

                    # Process directors
                    for idx, director_name in enumerate(movie_detail.director):
                        director, _ = Person.objects.get_or_create(name=director_name)
                        MovieDirector.objects.get_or_create(
                            movie=movie, person=director, defaults={"order": idx}
                        )

                    # Process writers
                    for idx, writer_name in enumerate(movie_detail.writer):
                        writer, _ = Person.objects.get_or_create(name=writer_name)
                        MovieWriter.objects.get_or_create(
                            movie=movie, person=writer, defaults={"order": idx}
                        )

                    # Process stars
                    for idx, star_name in enumerate(movie_detail.stars):
                        star, _ = Person.objects.get_or_create(name=star_name)
                        MovieStar.objects.get_or_create(
                            movie=movie, person=star, defaults={"order": idx}
                        )

            return Response(
                {
                    "message": f"Successfully stored {movies_added} new movies",
                    "total_scraped": len(movies_data),
                    "duplicate_movies": duplicate_movies,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred during import: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MovieListAPI(generics.ListAPIView):
    """API to fetch all movies with pagination."""

    serializer_class = MovieSerializer
    pagination_class = MoviePagination
    queryset = Movie.objects.all().order_by("-release_year", "title")


class MovieSearchAPI(generics.ListAPIView):
    """API to search movies by multiple criteria."""

    serializer_class = MovieSerializer
    pagination_class = MoviePagination

    def get_queryset(self):
        queryset = Movie.objects.all()

        # Get search parameters
        title = self.request.query_params.get("title", "")
        year = self.request.query_params.get("year")
        person = self.request.query_params.get("person", "")
        min_rating = self.request.query_params.get("min_rating")

        # Apply filters
        if title:
            queryset = queryset.filter(title__icontains=title)

        if year:
            queryset = queryset.filter(release_year=year)

        if person:
            queryset = queryset.filter(
                Q(directors__name__icontains=person)
                | Q(writers__name__icontains=person)
                | Q(stars__name__icontains=person)
            ).distinct()

        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass

        return queryset.order_by("-release_year", "title")
