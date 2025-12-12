# levels/management/commands/create_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from levels.models import Profile

class Command(BaseCommand):
    help = 'Creates Profile objects for users without profiles'

    def handle(self, *args, **kwargs):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        for user in users_without_profiles:
            Profile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f"Profile created for user: {user.username}"))

        self.stdout.write(self.style.SUCCESS("All profiles created!"))
