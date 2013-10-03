import json
import urllib2
import urllib
from django.http import HttpResponse
from django.contrib.sites.models import Site
from settings import host,live


def call_api(data,url,method='get'):

  if not data:
    data = {}

  url_values = urllib.urlencode(data)

  current_site = Site.objects.get_current()
  url = '%s%s' % (current_site.domain, url)

  """
  if host == live:
    url = 'http://api.levelskies.net%s' % (url)
  else:
    url = 'http://127.0.0.1:8002%s' % (url)
  """
  try:

    if method == 'get':
      full_url = url + '?' + url_values
      data = urllib2.urlopen(full_url)

    elif method == 'post':
      req = urllib2.Request(url, url_values)
      data = urllib2.urlopen(req)

    else:
      pass

    return json.loads(data.read())

  except urllib2.HTTPError as e:
    return {'success': False, 'error': "%s - %s" % (e.code, e.reason)}
  except Exception as err:
    return {'success': False, 'error': err}
