"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

application = get_wsgi_application()

from django.core.wsgi import get_wsgi_application

# Create superuser if not exists
from accounts.startup import create_superuser_if_not_exists
create_superuser_if_not_exists()

application = get_wsgi_application()