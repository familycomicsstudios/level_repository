"""
Run this script to apply migrations to your Supabase database.
Execute locally with your Supabase credentials in .env file.
"""
import os
import django
from pathlib import Path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'level_repository.settings')

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

django.setup()

# Run migrations
from django.core.management import call_command

print("Running migrations on Supabase database...")
call_command('migrate')
print("Migrations complete!")

# Optionally create a superuser
print("\nYou can now create a superuser by running:")
print("python manage.py createsuperuser")
