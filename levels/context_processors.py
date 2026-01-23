from django.conf import settings


def dark_mode_context(request):
    """Add dark_mode preference to template context for all views."""
    dark_mode = False
    if request.user.is_authenticated:
        dark_mode = request.user.profile.dark_mode
    return {'dark_mode': dark_mode}
