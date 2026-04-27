from django.urls import path
from . import views

app_name = 'levels'

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('api/docs/', views.api_docs, name='api_docs'),
    path('api/levels/', views.api_levels, name='api_levels'),
    path('api/levels/<int:level_id>/', views.api_level_detail, name='api_level_detail'),
    path('api/profiles/<str:username>/', views.api_profile_detail, name='api_profile_detail'),
    path('upload/', views.upload_level, name='upload'),
    path('list/', views.level_list, name='list'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Custom login URL
    path('logout/', views.logout, name='logout'),  # Custom logout URL
    path('level/<int:level_id>/', views.level_detail, name='level_detail'),  # Level detail URL
    path('level/<int:level_id>/reviews/', views.level_reviews, name='level_reviews'),
    path('level/<int:level_id>/submit-completion/', views.submit_level_completion, name='submit_level_completion'),
    path('completions/my-submissions/', views.my_completion_submissions, name='my_completion_submissions'),
    path('completions/admin-triage/', views.admin_completion_triage, name='admin_completion_triage'),
    path('level/<int:level_id>/edit/', views.edit_level, name='edit_level'),
    path('level/<int:level_id>/delete/', views.delete_level, name='delete_level'),
    path("profile/<str:username>/", views.user_profile, name="user_profile"),
    path("profile/<str:username>/edit/", views.edit_profile, name="edit_profile"),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('info/', views.info_page, name='info_page'),
    path('settings/', views.user_settings, name='user_settings'),

]
