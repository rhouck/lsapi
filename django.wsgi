#!/usr/bin/env python
import os
import sys

path = '/home/projects/beta.levelskies.com'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'api.settings_production'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


