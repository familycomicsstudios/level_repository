from django.contrib import admin
from .models import Level
from .models import Profile, Comment, LevelRating, LevelCompletion

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'difficulty_rating', 'quality_rating', 'creator')
    search_fields = ('name', 'level_code')  # Add search functionality
    list_filter = ('difficulty', 'difficulty_rating', 'quality_rating')


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


@admin.register(LevelRating)
class LevelRatingAdmin(admin.ModelAdmin):
    list_display = ('level', 'user', 'difficulty_rating', 'quality_rating', 'updated_at')
    list_filter = ('difficulty_rating', 'quality_rating', 'updated_at')
    search_fields = ('level__name', 'user__username')


@admin.register(LevelCompletion)
class LevelCompletionAdmin(admin.ModelAdmin):
    list_display = ('level', 'user', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('level__name', 'user__username', 'proof')
    readonly_fields = ('submitted_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    actions = ('approve_completions', 'reject_completions')

    @admin.action(description='Approve selected completions')
    def approve_completions(self, request, queryset):
        for completion in queryset:
            completion.approve(reviewer=request.user)

    @admin.action(description='Reject selected completions')
    def reject_completions(self, request, queryset):
        for completion in queryset:
            completion.reject(reviewer=request.user)

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == LevelCompletion.STATUS_APPROVED:
                obj.approve(reviewer=request.user)
                return
            if obj.status == LevelCompletion.STATUS_REJECTED:
                obj.reject(reviewer=request.user)
                return
        super().save_model(request, obj, form, change)
