from settings import mongo_host, mongo_port, MODE

try:
    import czjson as json
    json.encode = json.dumps
    json.decode = json.loads
except ImportError:
    try:
        import cjson as json
    except ImportError:
        import json
        json.encode = json.dumps
        json.decode = json.loads
from pymongo import MongoClient
mongo = MongoClient(mongo_host, mongo_port)

from random import randint, choice
import string
import copy
import time
import datetime
from dateutil.parser import parse
from django.utils.timezone import utc
import urllib2
import urllib
from django.http import HttpResponse
from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site

from quix.pay.gateway.authorizenet import AimGateway
from quix.pay.transaction import CreditCard, Address, Customer as AuthCustomer

from functions import find_sub_index_dict


def format_pref_input(i):
    # alters the preferences inputs from website to match format in simulation model
    if int(i) == 0:
        return []
    else:
        return [int(i)]


def check_creds(inps,model):
    #return HttpResponse(json.encode({'success': False, 'error': 'platform_key not sent'}), mimetype="application/json")
    #platform = get_object_or_404(Platform, key=request.POST['platform_key'])
    if not inps:
      return {'success': False, 'error': 'platform_key not sent'}
    elif 'platform_key' not in inps:
        return {'success': False, 'error': 'platform_key not sent'}
    else:
        try:
            platform = model.objects.get(key=inps['platform_key'])
            return {'success': True}
        except:
            return {'success': False, 'error': 'platform_key not valid'}

def gen_alphanum_key():
    key = ''
    for i in range(6):
        key += choice(string.lowercase + string.uppercase + string.digits)
    return key

def conv_to_js_date(date):
    return 1000 * time.mktime(date.timetuple())

def current_time_aware():
    return datetime.datetime.utcnow().replace(tzinfo=utc)

def conv_date_to_datetime(inp):
    return datetime.datetime(inp.year, inp.month, inp.day,0,0)


def send_request(url, data={}, headers=None, method='get'):

  try:

    url_values = urllib.urlencode(data)

    if method == 'get':
      url = url + '?' + url_values
      data = urllib2.urlopen(url)

    elif method == 'post':

      if headers:
        if headers['Content-Type'] == 'application/json':
          if 'query_params' in data:
            url_values = urllib.urlencode(data['query_params'])
            url = url + '?' + url_values
            del data['query_params']
          url_values = json.encode(data)
        req = urllib2.Request(url, url_values, headers)
      else:
        req = urllib2.Request(url, url_values)

      data = urllib2.urlopen(req)

    else:
      raise Exception("Impropper method: '%s'" % method)

    return {'success': True, 'response': json.decode(data.read())}

  except urllib2.HTTPError as e:
    return {'success': False, 'error': "The server couldn't fulfill the request: %s - %s" % (e.code, e.reason)}
  except urllib2.URLError as e:
    return {'success': False, 'error': "We failed to reach a server: %s" % (e.reason)}
  except Exception as err:
    return {'success': False, 'error': str(err)}


def run_authnet_trans(amt, card_info, cust_info=None, address=None, trans_id=None):

    gateway = AimGateway('3r34zx5KELcc', '29wm596EuWHG72PB')

    # use gateway.authorize() for an "authorize only" transaction
    # gateway.use_test_url = True

    # ensures all transactions done on local servers or the dev server are in test mode
    gateway.use_test_mode = False if MODE == 'live' else True

    # number, month, year, first_name, last_name, code
    card = CreditCard(**card_info)
    if not trans_id:
        if cust_info:
            address = Address(**address)
            customer = AuthCustomer(**cust_info)
            customer.billing_address = address
            customer.shipping_address = address
            response = gateway.sale(str(amt), card, customer=customer)
        else:
            response = gateway.sale(str(amt), card)
    else:
        response = gateway.credit(str(trans_id), str(amt), card)

    if response.status == response.APPROVED:
        # this is where you store data from the response object into
        # your models. The response.trans_id would be used to capture,
        # void, or credit the sale later.

        success = True
        status = "Authorize Request: %s</br>Transaction %s = %s: %s" % (gateway.get_last_request().url,response.trans_id,
                                           response.status_strings[response.status],
                                           response.message)
    else:
        success = False
        status = "%s - %s" % (response.status_strings[response.status],
            response.message)
        #form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([status])
    return {'success': success, 'status': status, 'trans_id': response.trans_id}


def test_trans(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if request.GET:
        form = PaymentForm(request.GET)
        if form.is_valid():
            cd = form.cleaned_data
            #return HttpResponse(cd)
            card = {}
            for i in ('first_name', 'last_name', 'number','month','year','code'):
                card[i] = cd[i]

            address = {}
            for i in ('first_name', 'last_name', 'phone', 'address1', 'city', 'state_province', 'country', 'postal_code'):
                address[i] = cd[i]

            cust_info = {}
            for i in ('email',):
                cust_info[i] = cd[i]

            response = run_authnet_trans(123, card, address=address, cust_info=cust_info)

            if response['success']:
                return HttpResponse(response['status'])
            else:

                form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([response['status']])
                return gen_search_display(request, {'form': form}, clean)
    else:
        form = PaymentForm()
        build = {'form': form}
    return gen_search_display(request, build, clean)
