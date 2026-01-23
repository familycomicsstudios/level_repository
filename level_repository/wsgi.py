"""
WSGI config for level_repository project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'level_repository.settings')

# Ensure staticfiles directory exists for Vercel deployment
BASE_DIR = Path(__file__).resolve().parent.parent
staticfiles_dir = BASE_DIR / 'staticfiles'
if not staticfiles_dir.exists():
    staticfiles_dir.mkdir(exist_ok=True)

application = get_wsgi_application()

# Vercel serverless handler
app = application
