from django.contrib import admin
from .models import Level
from .models import Profile, Comment

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'rated_difficulty', 'creator')  # Display these fields in the list view
    search_fields = ('name', 'level_code')  # Add search functionality
    list_filter = ('difficulty', 'rated_difficulty',)  # Add filtering options


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'stats']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('level', 'user', 'created_at', 'content')
    list_filter = ('created_at', 'user', 'level')
    search_fields = ('content', 'user__username', 'level__name')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
