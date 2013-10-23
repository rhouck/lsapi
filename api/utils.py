import pymongo
from random import randint, choice
import string
import copy
import time
import datetime
from django.utils.timezone import utc
import json
import urllib2
import urllib
from django.http import HttpResponse
from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site

from settings import host,live

from functions import find_sub_index_dict

"""
from django.core.mail import send_mail
def practice_mail(request):

    send_mail('Auto message from Level Skies', 'Here is an auto generated message sent just to annoy you while testing.', 'levelskiestest@gmail.com',
        ['ryanchouck@gmail.com', 'bcollins.audio@gmail.com'], fail_silently=False)
    return HttpResponse("success i think")
"""

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



def call_wan(url, data, method='post'):

  if method == 'post':
    url = 'http://api.wego.com/flights/api/%s' % (url)
  elif method == 'get':
    url = 'http://www.wego.com/flights/api/%s' % (url)

  data.update({'api_key': 'da9792caf6eae5490aef', 'ts_code': '9edfc'})
  headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

  response = send_request(url, data, headers, method)
  response['source'] = 'wego'
  return response


def pull_fares_range(origin, destination, depart_dates, return_dates, depart_times, return_times, num_stops, airlines, display_dates):
    """
    @summary:
      1. run live search on display dates
      2. run cached search on full date range
      3. run live search on non display dates that are empty or have cached fare higher than all live search prices
    """

    # to do: then run live search on empty dates and dates that are higher than display date live search

    def string_dates(inp):
      if isinstance(inp, list):
        for ind, i in enumerate(inp):
          for k, v in i.iteritems():
            inp[ind][k] = str(v)
      else:
        for k, v in inp.iteritems():
          inp[k] = str(v)
      return inp


    results = {}
    max_live_fare = None


    # run search for display flights
    if display_dates:
      if len(display_dates) == 2:
        if display_dates[1] > display_dates[0]:
          display_flights = run_flight_search(origin, destination, display_dates[0], display_dates[1], depart_times, return_times, num_stops, airlines)
          if display_flights['success']:
            results['flights'] = display_flights['flights']
            max_live_fare = display_flights['min_fare']



    dep_range = (depart_dates[1] - depart_dates[0]).days
    ret_range = (return_dates[1] - return_dates[0]).days



    # build empty list of fares for each flight date combination
    fares = []
    for i in range(dep_range + 1):
      depart_date = depart_dates[0] + datetime.timedelta(days=i)
      for k in range(ret_range + 1):
        return_date = return_dates[0] + datetime.timedelta(days=k)
        fares.append({'depart_date': depart_date, 'return_date': return_date, 'fare': None, 'method': None})




    # cached fare
    res = cached_search(origin, destination, depart_dates, return_dates)
    if res['fares']:
      for i in res['fares']:
        where = copy.deepcopy(i)
        del where['fare']
        ind = find_sub_index_dict(fares, where, loop=False)
        if ind:
          fares[ind[0]]['fare'] = i['fare']
          fares[ind[0]]['method'] = 'api_cached'




    # check mongo for existing flight searches
    for i in range(dep_range + 1):
      depart_date = depart_dates[0] + datetime.timedelta(days=i)
      for k in range(ret_range + 1):
        return_date = return_dates[0] + datetime.timedelta(days=k)

        # check if cached fare exists in level skies db, if so, overide api_cached fare
        ind = find_sub_index_dict(fares, {'depart_date': depart_date, 'return_date': return_date}, loop=False)
        if ind:
          #if not fares[ind[0]]['fare'] or fares[ind[0]]['fare'] > max_live_fare:
          res = run_flight_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines, cache_only=True)

          if res['success']:
            fares[ind[0]]['fare'] = res['min_fare']
            fares[ind[0]]['method'] = res['method']
            if res['min_fare'] > max_live_fare:
              max_live_fare = res['min_fare']




    # run live flight searches where no fare exists data exists or api_cached fare is higher than max_live_fare
    for i in range(dep_range + 1):
      depart_date = depart_dates[0] + datetime.timedelta(days=i)
      for k in range(ret_range + 1):
        return_date = return_dates[0] + datetime.timedelta(days=k)

        ind = find_sub_index_dict(fares, {'depart_date': depart_date, 'return_date': return_date}, loop=False)
        if ind:
          if not fares[ind[0]]['fare'] or (fares[ind[0]]['fare'] > max_live_fare and fares[ind[0]]['fare'] == 'api_cached'):
            res = run_flight_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines, cache_only=False)

            if res['success']:
              fares[ind[0]]['fare'] = res['min_fare']
              fares[ind[0]]['method'] = res['method']
              if res['min_fare'] > max_live_fare:
                max_live_fare = res['min_fare']

    results['fares'] = string_dates(fares)


    error = ""
    if results['fares']:
      results['success'] = True
    else:
      results['success'] = False
      error += "Couldn't find minimum fares for date combinations."
      results['error'] = error

    if display_dates:
      if not results['flights']:
        results['success'] = False
        error += "Couldn't build list of current flights for display dates."
        results['error'] = error

    return results


def run_flight_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines, cache_only=False):
    """
    @summary: first searches mongo db for valid cached fare meeting search parameters
              calls external api if no cached search available
              runs selects appropriate parsing function based on api source
    """
    inputs = {
            'origin':origin,
            'destination': destination,
            'depart_date': conv_date_to_datetime(depart_date),
            'return_date': conv_date_to_datetime(return_date),
            'depart_times': depart_times,
            'return_times': return_times,
            'num_stops': num_stops,
            'airlines': airlines,
            }

    current_time = current_time_aware()
    current_date = datetime.datetime(current_time.year, current_time.month, current_time.day,0,0)

    mongo = pymongo.MongoClient()

    data = None
    for i in range(2):
        # check if search has already been cached
        res = mongo.flight_search.live.find({'date_created': current_date, 'inputs.origin': inputs['origin'], 'inputs.destination': inputs['destination'], 'inputs.depart_date': inputs['depart_date'], 'inputs.return_date': inputs['return_date'], 'inputs.depart_times': inputs['depart_times'], 'inputs.return_times': inputs['return_times'], 'inputs.num_stops': inputs['num_stops'], 'inputs.airlines': inputs['airlines']}, {'_id': 0 }).sort('date_created',-1).limit(1)

        if res.count():
            # return search results if already cached
            data = res[0]
            if i == 0:
              method = "cached"

        else:
            # run search if not already cached
            if not cache_only:
              response = live_search(inputs['origin'], inputs['destination'], inputs['depart_date'].date(), inputs['return_date'].date(), inputs['depart_times'], inputs['return_times'], inputs['num_stops'], inputs['airlines'])
              if response['success']:
                if response['flights_count']:
                    search_res = mongo.flight_search.live.insert({'date_created': current_date, 'source': response['source'], 'inputs': inputs, 'response': response['response'],})
                    method = "live"

    mongo.disconnect()

    # parse data if available
    if not data:
        data = {'success': False, 'error': 'No data returned'}
    else:
        if data['source'] == 'wego':
            data = parse_wan_live(data)
            data['method'] = method
        else:
            data = {'success': False, 'error': 'Data was not parsed'}

    return data


def parse_wan_live(data):
    """
    @summary: parsing function for WeGo api flight search response
    """
    bank = []
    for i in data['response']['routes']:
        flight = {}
        flight['fare'] = i['best_fare']['price']
        flight['link'] = i['best_fare']['deeplink']
        flight['cabin'] = i['best_fare']['description']
        flight.update({'inbound_segments': i['inbound_segments'], 'outbound_segments': i['outbound_segments'],})
        bank.append(flight)

    fare_bank = [i['fare'] for i in bank]
    if fare_bank:
      min_fare = min(fare_bank)
    else:
      min_fare = None

    return {'success': True, 'flights': bank, 'min_fare': min_fare}



def cached_search(origin, destination, depart_dates, return_dates):

    # this search does not actually find cached fares for the two dates listed
    # instead it supposedly finds best fares for dates departing within that range
    # saves cached data into mongo

    inputs = {
            'origin':origin,
            'destination': destination,
            'depart_dates': (conv_date_to_datetime(depart_dates[0]), conv_date_to_datetime(depart_dates[1])),
            'return_dates': (conv_date_to_datetime(return_dates[0]), conv_date_to_datetime(return_dates[1])),
            #'depart_times': depart_times,
            #'return_times': return_times,
            #'num_stops': num_stops,
            #'airlines': airlines,
            }

    current_time = current_time_aware()
    current_date = datetime.datetime(current_time.year, current_time.month, current_time.day,0,0)


    url = "rates/daily/from_city_to_city"
    data = {'from': origin, 'to': destination, 'trip_type': 'roundtrip'}
    data.update({'dt_start': depart_dates[0], 'dt_end': depart_dates[1]})

    response = call_wan(url, data, method="get")

    if response['success']:
      if response['response']['rates']:
        mongo = pymongo.MongoClient()
        cached_res = mongo.flight_search.cached.insert({'date_created': current_date, 'source': response['source'], 'inputs': inputs, 'response': response['response'],})
        mongo.disconnect()


    # parse data if available
    if not response['success']:
        data = {'success': False, 'error': response['success']['error']}
    else:
        if response['source'] == 'wego':
            data = parse_wan_cached(response['response'])
        else:
            data = {'success': False, 'error': 'Data was not parsed'}

    return data



def parse_wan_cached(data):
    """
    @summary: parsing function for WeGo api cached search response
    """

    bank = []

    for i in data['rates'].iterkeys():
      for k in data['rates'][i]:

        fare = {}
        fare['depart_date'] = k['outbound']
        fare['return_date'] = k['inbound']
        fare['fare'] = k['price_in_usd']
        bank.append(fare)

    fare_bank = [i['fare'] for i in bank]
    if fare_bank:
      max_fare = max(fare_bank)
    else:
      max_fare = None

    return {'success': True, 'fares': bank, 'max_fare': max_fare}



def live_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines=None):


    # format inputs
    def pick_time_window(time_list):
        morning = [360, 720] # 6:00am to 12:00pm
        evening = [720, 1080] # 12:00pm to 6:00pm
        any_time = [0, 1440] # 12:00am to 12:00am

        if 'any_time' in time_list:
            return (any_time[0], any_time[1])
        else:
            if 'morning' in time_list and 'evening' not in time_list:
                return (morning[0], morning[1])
            elif 'morning' in time_list and 'evening' in time_list:
                return (morning[0], evening[1])
            elif 'morning' not in time_list and 'evening' in time_list:
                return (evening[0], evening[1])
            else:
                return (any_time[0], any_time[1])

    depart_times = pick_time_window(depart_times)
    return_times = pick_time_window(return_times)

    if num_stops == "best-only":
        num_stops = ["none", "one",]
    else:
        num_stops = ["none", "one", "two_plus"]


    # create search
    url = 'k/2/searches'
    data = {
            "trips": [
              {
                "departure_code": str(origin),
                "arrival_code": str(destination),
                "outbound_date": "%s" % (depart_date),
                "inbound_date": "%s" % (return_date),
              }
            ],
            "adults_count": 1
          }
    response = call_wan(url, data)

    if not response['success']:

        return HttpResponse(json.dumps({'success': False, 'error': "Could not complete 'Searches' call: %s" % (response['error'])}), mimetype="application/json")

    else:

        # pull fares
        url = 'k/2/fares'
        data = {
                  # general
                  "id": "%s" % (gen_alphanum_key()),
                  "fares_query_type": "route",
                  "departure_day_time_filter_type": "separate",

                  # api response format
                  "sort": "price",
                  "order": "asc",
                  #"page": 1,
                  "per_page": 30,

                  # four hour max layover
                  "stopover_duration_min": 0,
                  "stopover_duration_max": 240,

                  # travel times
                  "outbound_departure_day_time_min": depart_times[0],
                  "outbound_departure_day_time_max": depart_times[1],
                  "inbound_departure_day_time_min": return_times[0],
                  "inbound_departure_day_time_max": return_times[1],

                  # num stops
                  "stop_types": num_stops,
                }

        data.update({'search_id': response['response']['id'], 'trip_id': response['response']['trips'][0]['id']})

        time.sleep(0.5)
        response = call_wan(url, data)

        # if no results, try two more times since it occasionally returns zero routes
        counter = 1
        while counter <= 2:
            if response['success'] and response['response']['filtered_routes_count'] == 0:
                time.sleep(0.5)
                response = call_wan(url, data)
                counter += 1
            else:
                break

    response['flights_count'] = response['response']['filtered_routes_count']
    return response
