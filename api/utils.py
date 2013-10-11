import json
import urllib2
import urllib
from django.http import HttpResponse
from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site

from settings import host,live



def call_wan(url, data, method='post'):

  if method == 'post':
    url = 'http://api.wego.com/flights/api/%s' % (url)
  elif method == 'get':
    url = 'http://www.wego.com/flights/api/%s' % (url)

  data.update({'api_key': 'da9792caf6eae5490aef', 'ts_code': '9edfc'})
  headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

  return send_request(url, data, headers, method)



def send_request(url, data, headers=None, method='get'):

  if not data:
    data = {}

  try:

    if method == 'get':
      url_values = urllib.urlencode(data)
      full_url = url + '?' + url_values
      data = urllib2.urlopen(full_url)

    elif method == 'post':
      url_values = json.dumps(data)
      req = urllib2.Request(url, url_values, headers)
      data = urllib2.urlopen(req)

    else:
      raise Exception("Impropper method: '%s'" % method)

    return {'success': True, 'response': json.loads(data.read())}

  except urllib2.HTTPError as e:
    return {'success': False, 'error': "The server couldn't fulfill the request: %s - %s" % (e.code, e.reason)}
  except urllib2.URLError as e:
    return {'success': False, 'error': "We failed to reach a server: %s" % (e.reason)}
  except Exception as err:
    return {'success': False, 'error': str(err)}
