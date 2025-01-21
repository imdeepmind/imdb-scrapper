from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Person(models.Model):
    """Base model for people involved in movies (directors, writers, stars)."""
    
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

class Movie(models.Model):
    """Main movie model with all details and relationships."""
    
    title = models.CharField(max_length=255)
    release_year = models.CharField(max_length=2, null=True)
    rating = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(10.0)
        ]
    )
    plot = models.TextField()
    
    # Many-to-many relationships
    directors = models.ManyToManyField(
        Person,
        related_name='directed_movies',
        through='MovieDirector'
    )
    writers = models.ManyToManyField(
        Person,
        related_name='written_movies',
        through='MovieWriter'
    )
    stars = models.ManyToManyField(
        Person,
        related_name='starred_movies',
        through='MovieStar'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_year', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_year']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.title} ({self.release_year or 'N/A'})"

class MovieDirector(models.Model):
    """Through model for movie-director relationship."""
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['movie', 'person']

class MovieWriter(models.Model):
    """Through model for movie-writer relationship."""
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['movie', 'person']

class MovieStar(models.Model):
    """Through model for movie-star relationship."""
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)  # For billing order
    character_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ['movie', 'person']