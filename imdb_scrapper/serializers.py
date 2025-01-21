from rest_framework import serializers

from .models import Movie, Person


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name"]


class MovieSerializer(serializers.ModelSerializer):
    directors = PersonSerializer(many=True, read_only=True)
    writers = PersonSerializer(many=True, read_only=True)
    stars = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "release_year",
            "rating",
            "plot",
            "directors",
            "writers",
            "stars",
            "created_at",
            "updated_at",
        ]
