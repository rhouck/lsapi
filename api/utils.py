import pymongo
from random import randint, choice
import string

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

  return send_request(url, data, headers, method)




def run_flight_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines):
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
        res = mongo.flight_search.practice.find({'date_created': current_date, 'inputs.origin': inputs['origin'], 'inputs.destination': inputs['destination'], 'inputs.depart_date': inputs['depart_date'], 'inputs.return_date': inputs['return_date'], 'inputs.depart_times': inputs['depart_times'], 'inputs.return_times': inputs['return_times'], 'inputs.num_stops': inputs['num_stops'], 'inputs.airlines': inputs['airlines']}, {'_id': 0 }).sort('date_created',-1).limit(1)

        if res.count():
            # return search results if already cached
            data = res[0]
        else:
            # run search if not already cached
            response = live_search(inputs['origin'], inputs['destination'], inputs['depart_date'].date(), inputs['return_date'].date(), inputs['depart_times'], inputs['return_times'], inputs['num_stops'], inputs['airlines'])
            if response['flights_count']:
                search_res = mongo.flight_search.practice.insert({'date_created': current_date, 'source': response['source'], 'inputs': inputs, 'response': response['response'],})

    mongo.disconnect()

    # parse data if available
    if not data:
        data = {'success': False, 'error': 'No data returned'}
    else:
        if data['source'] == 'wego':
            data = parse_wan(data)
        else:
            data = {'success': False, 'error': 'Data was not parsed'}
    #return HttpResponse(json.dumps(data), mimetype="application/json")
    return data


def parse_wan(data):

    bank = []
    for i in data['response']['routes']:
        flight = {}
        flight['fare'] = i['best_fare']['price']
        flight['link'] = i['best_fare']['deeplink']
        flight['cabin'] = i['best_fare']['description']
        flight.update({'inbound_segments': i['inbound_segments'], 'outbound_segments': i['outbound_segments'],})
        bank.append(flight)
    return {'success': True, 'flights': bank}



def cached_search(origin, destination, depart_date, return_date):

    # this search does not actually find cached fares for the two dates listed
    # instead it supposedly finds best fares for dates departing within that range
    url = "rates/daily/from_city_to_city"
    data = {'from': origin, 'to': destination, 'trip_type': 'roundtrip'}
    data.update({'dt_start': depart_date, 'dt_end': return_date})

    response = call_wan(url, data, method="get")
    return response


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

    response['source'] = 'wego'
    response['flights_count'] = response['response']['filtered_routes_count']
    return response
