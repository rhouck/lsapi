from api.utils import *
from images import get_airline_image

def select_geography(hub):
    """
    @attention: this function determines what geography to set for gen_price function based on the hub. once more than one hub per geography is availalble, another method should be used.
                it may be best to use the sites model to determine geography, or have the client send the geography in the api pricing call
    """
    if hub == "SFO":
        geography = "us"
    elif hub == "LHR":
        geography = "eu"
    else:
        geography = ""
    return geography


# start date used to calculate price and lock in period b': th need to be change'd to follow ': urrent date, not fix'ed date':
def refund_format_conversion(pricing_results):
    pricing_results['refund_value'] = pricing_results['locked_fare']
    if pricing_results['holding_price'] and pricing_results['locked_fare']:
        pricing_results['deposit_value'] = pricing_results['holding_price'] + pricing_results['locked_fare']
    else:
        pricing_results['deposit_value'] = ''
    del pricing_results['holding_price']
    del pricing_results['locked_fare']
    return pricing_results


def call_sky(url, data={}, method='get'):

  url = 'http://partners.api.skyscanner.net/apiservices/%s' % (url)
  data.update({'apikey': 'lvls0948650201236592310165489310', 'locationschema': 'Iata',})
  #data.update({'apikey': 'prtl6749387986743898559646983194'})

  #return {'data': data, 'url': url}
  """
  if method == 'post':
    pass
  elif method == 'get':
    pass
  """

  headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
  response = send_request(url, data, headers, method)
  response['source'] = 'skyscanner'
  return response




def pull_fares_range(origin, destination, depart_dates, return_dates, depart_times, return_times, num_stops, airlines):
    """
    @summary:
      1. *** to do *** run live search on one likely expensive pair of dates
      2. run api-based cached search on full date range
      2. run local cached search on full date range
      3. run live search on non display dates that are empty or have cached fare higher than all live search prices
    """


    # to do: then run live search on empty dates and dates that are higher than display date live search
    # make sure it only compares display date search with max fare if the display dates are within the option range
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

    """
    # run search for display flights
    if display_dates:
      results['flights'] = None
      if len(display_dates) == 2:
        if display_dates[1] > display_dates[0]:
          display_flights = run_flight_search(origin, destination, display_dates[0], display_dates[1], depart_times, return_times, num_stops, airlines)

          #return display_flights
          if display_flights['success']:
            results['flights'] = display_flights['flights']
            max_live_fare = display_flights['min_fare']
    """


    dep_range = (depart_dates[1] - depart_dates[0]).days
    ret_range = (return_dates[1] - return_dates[0]).days



    # build empty list of fares for each flight date combination
    fares = []
    for i in range(dep_range + 1):
      depart_date = depart_dates[0] + datetime.timedelta(days=i)
      for k in range(ret_range + 1):
        return_date = return_dates[0] + datetime.timedelta(days=k)
        fares.append({'depart_date': depart_date, 'return_date': return_date, 'fare': None, 'method': None})

    """
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
    """

    """
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
    """

    #raw = []
    # run live flight searches where no fare exists data exists or api_cached fare is higher than max_live_fare
    for i in range(dep_range + 1):
      depart_date = depart_dates[0] + datetime.timedelta(days=i)
      for k in range(ret_range + 1):
        return_date = return_dates[0] + datetime.timedelta(days=k)

        ind = find_sub_index_dict(fares, {'depart_date': depart_date, 'return_date': return_date}, loop=False)
        if ind:
          if not fares[ind[0]]['fare'] or (fares[ind[0]]['fare'] > max_live_fare and fares[ind[0]]['method'] == 'api_cached'):
            res = run_flight_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines, cache_only=False)
            #raw.append(res)
            if res['success']:
              fares[ind[0]]['fare'] = res['min_fare']
              fares[ind[0]]['method'] = res['method']
              if res['min_fare'] > max_live_fare:
                max_live_fare = res['min_fare']

    #results['raw'] = raw

    results['fares'] = string_dates(fares)
    #results = {'fares': None, 'flights': None}

    error = ""
    if results['fares']:
      results['success'] = True
    else:
      results['success'] = False
      error += "Couldn't find minimum fares for date combinations."
      results['error'] = error
    """
    if display_dates:
      if not results['flights']:
        results['success'] = False
        if error:
          error += " "
        error += "Couldn't build list of current flights for display dates."
        results['error'] = error
    """
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

    data = None
    """
    # check if search has already been cached
    res = mongo.flight_search.live.find({'date_created': current_date, 'inputs.origin': inputs['origin'], 'inputs.destination': inputs['destination'], 'inputs.depart_date': inputs['depart_date'], 'inputs.return_date': inputs['return_date'], 'inputs.depart_times': inputs['depart_times'], 'inputs.return_times': inputs['return_times'], 'inputs.num_stops': inputs['num_stops'], 'inputs.airlines': inputs['airlines']}, {'_id': 0 }).sort('date_created',-1).limit(1)
    if res.count():
        # return search results if already cached
        data = res[0]
        method = "cached"
    """
    if 3<2:
      pass
    else:
        # run search if not already cached
        if not cache_only:
          response = live_search(inputs['origin'], inputs['destination'], inputs['depart_date'].date(), inputs['return_date'].date(), inputs['depart_times'], inputs['return_times'], inputs['num_stops'], inputs['airlines'])

          if response['success']:
            if response['flights_count']:
                search_res = mongo.flight_search.live.insert({'date_created': current_date, 'source': response['source'], 'inputs': inputs, 'response': response['response'],})
                method = "live"
                data = response

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


def live_search(origin, destination, depart_date, return_date, depart_times, return_times, num_stops, airlines=None):

    # format inputs
    def pick_time_window(time_list):

        if time_list == 'morning':
          return (0, 720) # 12:00am to 12:00pm
        elif time_list == 'morning-no-red-eye':
          return (360, 720) # 6:00am to 12:00pm
        elif time_list == 'evening':
          return (720, 1440) # 12:00pm to 12:00am
        elif time_list == 'evening-no-red-eye':
          return (720, 1320) # 12:00pm to 10:00pm
        elif time_list == 'no-red-eye':
          return (360, 1320) # 6:00am to 10:00pm
        elif time_list == 'any':
          return (0, 1440) # 12:00am to 12:00am
        else:
          return (0, 1440) # 12:00am to 12:00am

    depart_times = pick_time_window(depart_times)
    return_times = pick_time_window(return_times)


    if num_stops == "none-one":
        num_stops = ["none", "one",]
    elif num_stops == "any":
        num_stops = ["none", "one", "two_plus"]
    else:
      num_stops = ["none", "one", "two_plus"]


    # create search
    url = 'searches'
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

        return {'success': False, 'error': "Could not complete 'Searches' call: %s" % (response['error'])}

    else:

        # pull fares
        url = 'fares'
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

        time.sleep(5)
        response = call_wan(url, data)

        # if no results, try two more times since it occasionally returns zero routes
        counter = 1
        while counter <= 4:
            if (response['success'] and response['response']['filtered_routes_count'] == 0) or not response['success']:
                time.sleep(1.5)
                response = call_wan(url, data)
                counter += 1
            else:
                break

        # check if more results are coming in, stop once results count is stable
        if response['success']:
          found_routes = response['response']['filtered_routes_count']

          time.sleep(1.5)
          response = call_wan(url, data)

          counter = 1
          while counter <= 4:
              if (response['success'] and response['response']['filtered_routes_count'] > found_routes) or not response['success']:
                  found_routes = response['response']['filtered_routes_count']
                  time.sleep(1.5)
                  response = call_wan(url, data)
                  counter += 1
              else:
                  break

        try:
          response['flights_count'] = response['response']['filtered_routes_count']
        except:
          pass

        return response





def call_wan(url, data, method='post'):

  creds = {'api_key': 'da9792caf6eae5490aef', 'ts_code': '9edfc'}

  if method == 'post':
    url = 'http://api.wego.com/flights/api/k/2/%s' % (url)
    data.update({'query_params': creds})
  elif method == 'get':
    url = 'http://www.wego.com/flights/api/%s' % (url)
    data.update(creds)

  headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

  response = send_request(url, data, headers, method)
  response['source'] = 'wego'
  return response


def parse_wan_live(data):

    """
    @summary: parsing function for WeGo api flight search response
    """

    airline_bank = data['response']['airline_filters']

    def get_airline_name(code, airline_bank):
      airline_name = None
      for i in airline_bank:
        if code == i['code']:
          airline_name = i['name']
          break
      return airline_name

    bank = []
    for i in data['response']['routes']:
        flight = {}
        flight['fare'] = i['best_fare']['price']
        flight['deeplink'] = i['best_fare']['deeplink']
        flight['cabin'] = i['best_fare']['description']


        for j in (('departing','outbound'), ('returning','inbound')):
          # aggregate trip section
          flight[j[0]] = {}
          flight[j[0]]['take_off_airport_code'] = i['%s_segments' % (j[1])][0]['departure_code']
          flight[j[0]]['take_off_city'] = i['%s_segments' % (j[1])][0]['departure_name']
          flight[j[0]]['landing_airport_code'] = i['%s_segments' % (j[1])][-1]['arrival_code']
          flight[j[0]]['landing_city'] = i['%s_segments' % (j[1])][0]['arrival_name']
          beg_time = i['%s_segments' % (j[1])][0]['departure_time']
          flight[j[0]]['take_off_time'] = beg_time
          flight[j[0]]['take_off_weekday'] = parse(beg_time).strftime("%a")
          end_time = i['%s_segments' % (j[1])][-1]['arrival_time']
          flight[j[0]]['landing_time'] = end_time
          flight[j[0]]['landing_weekday'] = parse(end_time).strftime("%a")
          flight[j[0]]['trip_duration'] = (parse(end_time)-parse(beg_time)).seconds / 60
          flight[j[0]]['number_stops'] = len(i['%s_segments' % (j[1])])-1

          airlines = []
          airline_codes = []
          for k in i['%s_segments' % (j[1])]:
            if k['airline_code'] not in airline_codes:
              airline_name = get_airline_name(k['airline_code'], airline_bank)
              airlines.append(airline_name)
              airline_codes.append(k['airline_code'])
          if len(airlines) == 0:
            flight[j[0]]['airline'] = None
            flight[j[0]]['airline_image'] = None
          elif len(airlines) == 1:
            flight[j[0]]['airline'] = airlines[0]
            flight[j[0]]['airline_image'] = get_airline_image(flight[j[0]]['airline'])
          else:
            flight[j[0]]['airline'] = "Multiple"
            flight[j[0]]['airline_image'] = None

          # detail section
          flight[j[0]]['detail'] = []
          flight[j[0]]['layover_times'] = []
          for ind, k in enumerate(i['%s_segments' % (j[1])]):
            entry = {}
            entry['flight_number'] = k['designator_code']
            entry['take_off_airport_code'] = k['departure_code']
            entry['take_off_city'] = k['departure_name']
            entry['landing_airport_code'] = k['arrival_code']
            entry['landing_city'] = k['arrival_name']
            dep_time = k['departure_time']
            entry['take_off_time'] = dep_time
            entry['take_off_weekday'] = parse(dep_time).strftime("%a")

            # calc layover
            if ind > 0:
              minutes = (parse(dep_time)-parse(arr_time)).seconds / 60
              flight[j[0]]['layover_times'].append(minutes)

            arr_time = k['arrival_time']
            entry['landing_time'] = arr_time
            entry['duration'] = (parse(arr_time)-parse(dep_time)).seconds / 60
            entry['landing_weekday'] = parse(arr_time).strftime("%a")
            if 'operating_airline_name' in k:
              entry['airline'] = k['operating_airline_name']
            else:
              entry['airline'] = get_airline_name(k['airline_code'], airline_bank)
            entry['airline_image'] = get_airline_image(entry['airline'])
            entry['airline_code'] = k['airline_code']

            flight[j[0]]['detail'].append(entry)

        bank.append(flight)

    fare_bank = [i['fare'] for i in bank]
    if fare_bank:
      min_fare = min(fare_bank)
    else:
      min_fare = None

    return {'success': True, 'flights': bank, 'min_fare': min_fare, 'airlines': airline_bank}

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
