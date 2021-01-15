"""
WSGI config for WEB2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import sys
from os.path import dirname,abspath
from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# sys.path.append(dirname(dirname(abspath(__file__))))
application = get_wsgi_application()
