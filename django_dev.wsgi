#!/usr/bin/env python
import os
import sys

path = '/home/projects/api.dev.levelskies.com'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'api.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


