from django.db import models
from django.contrib.auth.models import User

class Level(models.Model):

    MOD_CHOICES = [
        ('appel', 'Appel'),
        ('appelp', 'Appel+'),
        ('appelm', 'Appel Multiplayer'),
        ('sheepel', 'Sheepel'),
        ('appel-playground', "Appel Playground")
    ]

    name = models.CharField(max_length=100)
    level_code = models.TextField(max_length=10000)
    description = models.TextField(null=True, blank=True, default="", max_length=2000)
    original_uploader = models.CharField(null=True, blank=True, default="", max_length=100, help_text="The original creator of the level. Leave blank if this was you.")
    difficulty = models.FloatField(default=0, help_text="The difficulty (in the Punter scale, more info <a href='https://appel.miraheze.org/wiki/Difficulty'>here</a>)")
    rated_difficulty = models.FloatField(null=True, blank=True)
    level_ratings = models.JSONField(default=list, blank=True)
    mod_category = models.CharField(max_length=50, choices=MOD_CHOICES, default='appel')

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="levels")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.creator.username}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    stats = models.JSONField(default={
        "levelpoints": 0,
        "levels_completed": [],
    })  # A JSON field for storing stats, like {"score": 0, "level": 1}

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Comment(models.Model):
    level = models.ForeignKey('Level', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.level.name}"

