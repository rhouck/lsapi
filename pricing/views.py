from django.core.mail import send_mail
import time
import datetime
import sys
from random import randint
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.core.context_processors import csrf
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404

from forms import *
from pricing.models import Searches, ExpiredSearchPriceCheck
from sales.models import Platform, Contract, Demo
from analysis.models import Open
from api.views import current_time_aware, gen_search_display, gen_alphanum_key, conv_to_js_date
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


from functions import *
from gen_price import *
from mult_search import *
from search_summary import *
from simp_price import *

from api.utils import *
from api.settings import MODE
from pricing.utils import *

from dateutil.parser import parse

from temp import return_search_res

import random

from sales.utils import send_template_email


def test_google(request):

    data = {
              "request": {
                "passengers": {
                  "adultCount": 1
                },
                "slice": [
                  {
                    "origin": "BOS",
                    "destination": "LAX",
                    "date": "2014-04-05"
                  },
                  {
                    "origin": "LAX",
                    "destination": "BOS",
                    "date": "2014-04-10"
                  }
                ]
              }
            }

    res = call_google(data)
    return HttpResponse(json.encode(res), content_type="application/json")

def test_wan(request):
    url = 'searches'
    data = {
              "trips": [
                {
                  "departure_code": "SIN",
                  "arrival_code": "HKG",
                  "outbound_date": "2013-11-13",
                  "inbound_date": "2013-11-20"
                }
              ],
              "adults_count": 1
            }
    res = call_wan(url, data, method='post')
    return HttpResponse(json.encode(res), content_type="application/json")

def test_skyscan(request):
    """
    # grid search
    url = 'browsegrid/v1.0/GB/GBP/en-GB/LHR/FRA/2013-12/2014-01'
    res = call_sky(url, data={}, method='get')
    return HttpResponse(json.encode(res), content_type="application/json")
    """

    """
    # price caching api - seems to pull cached fare on specific flight
    url = 'pricing/v1.0/GB/GBP/en-GB/LHR/FRA/2013-12/2014-01'
    res = call_sky(url, method='get')
    return HttpResponse(json.encode(res), content_type="application/json")
    """



    # create session
    url = 'pricing/v1.0'

    data = {
            'country': 'US',
            'currency': 'USD',
            'locale': 'en-US',
            'originplace': 'SFO',
            'destinationplace': 'JFK',
            'outbounddate': '2013-12-13',
            'inbounddate': '2013-12-20',
            'adults': "1",
            }

    res = call_sky(url, data, method='post')
    return HttpResponse(json.encode(res), content_type="application/json")

def test_flight_search(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if (request.POST):
        if clean:
            cred = check_creds(request.POST, Platform)
            if not cred['success']:
                return HttpResponse(json.encode(cred), content_type="application/json")


        form = flight_search_form(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            res = run_flight_search(cd['origin_code'], cd['destination_code'], cd['depart_date1'], cd['return_date1'], cd['depart_times'], cd['return_times'], cd['convenience'], airlines=cd['airlines'], cached=False)
            #return HttpResponse(json.encode(res), mimetype="application/json")
            build = {'form': form, 'results': res}

        else:
            build = {'results': {'success': False, 'error': "Invalid inputs."}}

    else:
        form = flight_search_form()
        combined_results = None
        build = {'form': form, 'results': combined_results}

    return gen_search_display(request, build, clean, method='post')



def display_current_flights(request, slug, convert=False):
    """
    @summary: use this to find flights associated with a particular search_key
                if convert - must supply two travel dates and one flight search will be provided
                if not convert - this will automatically return all flights in the date ranges searched, trying cached searches first
    """
    
    inputs = request.GET if request.GET else None

    if not request.user.is_authenticated():
        cred = check_creds(inputs, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), content_type="application/json")

    try:

        search = Searches.objects.get(key=slug)

        if convert:

            form = flights_display(inputs)

            if not form.is_valid():
                raise Exception("Valid travel dates not provided: depart_date & return_date")

            # raise error if contract is not outstanding or has already been marked for staging process
            contract = Contract.objects.get(search__key=slug)
            if not contract.outstanding() or contract.staged():
                raise Exception("This contract is no longer valid or has already been converted.")

            cd = form.cleaned_data
            if (search.depart_date1 > cd['depart_date']) or (cd['depart_date'] > search.depart_date2) or (search.return_date1 > cd['return_date']) or (cd['return_date'] > search.return_date2):
                raise Exception('Selected travel dates not within locked fare range.')



            # run search and format results
            res = run_flight_search(search.origin_code, search.destination_code, cd['depart_date'], cd['return_date'], search.depart_times, search.return_times, search.convenience, search.airlines, slug, cached=False)
            if not res['success']:
                raise Exception("Could not return list of current available flights: %s" % (res['error']))
            
            if res['min_fare'] > search.locked_fare:
                res['payout'] = res['min_fare'] - search.locked_fare
            else:
                res['payout'] = 0
            """
            # converts prices to rebate values and caps the price level of flights available to choose from
            
            bank = []
            cap = None
            
            for index, i in enumerate(res['flights']):

                add = False

                if not cap:
                    add = True
                    if index == 0:
                        if i['fare'] < search.locked_fare:
                            cap = search.locked_fare
                    else:
                        if i['fare'] > search.locked_fare:
                            cap = i['fare']
                else:
                    if i['fare'] <= cap + 5:
                        add = True

                if add:

                    if i['fare'] < search.locked_fare:
                        #res['flights'][index]['rebate'] = search.locked_fare - i['fare']
                        res['flights'][index]['rebate'] = None
                    else:
                        res['flights'][index]['rebate'] = None
                    del res['flights'][index]['fare']

                    bank.append(res['flights'][index])
            
            res['flights'] = bank
            """

        else:

            # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
            # or the purchase occured after too much time had passed, and the quoted price is deemed expired
            purch_date_time = current_time_aware()
            search_date_date = search.search_date
            expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 60) else False

            if search.error or not search.get_status() or expired:
                raise Exception("The search is expired, had an error, or was made while sales were shut off")

            # run search and format data
            res = {'success': True}
            error = ""

            dep_range = (search.depart_date2 - search.depart_date1).days
            ret_range = (search.return_date2 - search.return_date1).days

            # build empty list of fares for each flight date combination
            for i in range(dep_range + 1):
              depart_date = search.depart_date1 + datetime.timedelta(days=i)
              for k in range(ret_range + 1):

                return_date = search.return_date1 + datetime.timedelta(days=k)
                one_res = run_flight_search(search.origin_code, search.destination_code, depart_date, return_date, search.depart_times, search.return_times, search.convenience, search.airlines, slug, cached=True)
                
                res['%s-%s' % (depart_date, return_date)] = one_res

                if not one_res['success']:
                    res['success'] = False
                    error += '%s-%s: %s ' % (depart_date, return_date, one_res['error'])
            if not res['success']:
                res['error'] = error

        
    except (Contract.DoesNotExist):
        res = {'success': False, 'error': 'The contract key entered is not valid.'}
    except (Searches.DoesNotExist):
        res = {'success': False, 'error': 'The search key entered is not valid.'}
    except Exception as err:
        res = {'success': False, 'error': str(err)}
    
    return HttpResponse(json.encode(res), content_type="application/json")


def search_info(request, slug, all=False):

    if not request.user.is_authenticated():
        cred = check_creds(request.GET, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), content_type="application/json")

    search = get_object_or_404(Searches, key=slug)

    purch_date_time = current_time_aware()
    search_date_date = search.search_date
    """
    if not all:
        expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 60) else False
        if expired:
            return HttpResponse(json.encode({'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}), content_type="application/json")
    """
    search_dict = search.__dict__

    for k, v in search_dict.iteritems():
        if isinstance(v,datetime.date):
            search_dict[k] = conv_to_js_date(v)

    del search_dict['_state']
    del search_dict['open_status']
    del search_dict['id']
    #del search_dict['search_type']
    del search_dict['holding_per']
    del search_dict['error']

    # convert to refund system
    #search_dict = refund_format_conversion(search_dict)

    search_dict['success'] = True
    return HttpResponse(json.encode(search_dict), content_type="application/json")

def price_edu_combo(request):

        if request.user.is_authenticated():
            clean = False
        else:
            clean = True

        if (request.POST):
            if clean:
                cred = check_creds(request.POST, Platform)
                if not cred['success']:
                    return HttpResponse(json.encode(cred), content_type="application/json")


            form = full_option_info(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                #inp_errors = sim_errors(self.db, cd['origin_code'], cd['destination_code'],self.lockin_per,self.start_date,self.d_date1,self.d_date2,self.r_date1,self.r_date2,self.final_proj_week, self.max_trip_length, self.geography)


                open_status = Open.objects.get(pk=1)

                current_time = current_time_aware()
                
                general = {'search_date': current_time, 'open_status': open_status.get_status(), 'key': gen_alphanum_key(),}

                model_in = {'origin_code': cd['origin_code'], 
                            'destination_code': cd['destination_code'], 
                            'holding_per': cd['holding_per'],
                            'depart_date1': str(cd['depart_date1']), 
                            'depart_date2': str(cd['depart_date2']), 
                            'return_date1': str(cd['return_date1']), 
                            'return_date2': str(cd['return_date2']),
                            'search_type': 'rt', 
                            'depart_times': cd['depart_times'], 
                            'return_times': cd['return_times'], 
                            'convenience': cd['convenience'], 
                            'airlines': cd['airlines']}

                combined = dict(general.items() + model_in.items())

                if open_status.get_status():
                    if (cd['depart_date2'] - cd['depart_date1']).days > 2 or (cd['return_date2'] - cd['return_date1']).days > 2:
                        model_out = {'error': 'Travel date ranges must not be more than two days in length'}
                    elif (cd['depart_date2'] < cd['depart_date1']) or (cd['return_date2'] < cd['return_date1']):
                        model_out = {'error': 'Travel date ranges are wrong'}
                    else:
                        
                        flights = pull_fares_range(cd['origin_code'], cd['destination_code'], (cd['depart_date1'], cd['depart_date2']), (cd['return_date1'], cd['return_date2']), cd['depart_times'], cd['return_times'], cd['convenience'], cd['airlines'], search_key=combined['key'])
                        #return HttpResponse(json.encode(flights), content_type="application/json")

                        if flights['success']:
                            #prices = calc_price(cd['origin_code'], cd['destination_code'], flights['fares'], cd['holding_per']*7, [cd['depart_date1'],cd['depart_date2']], [cd['return_date1'],cd['return_date2']], general['search_date'])
                            prices = calc_price(cd['origin_code'], cd['destination_code'], flights['fares'], cd['holding_per']*7, general['search_date'])
                            model_out = {'holding_price': prices['holding_price'], 'locked_fare': prices['locked_fare'], 'expected_risk': prices['expected_risk'],
                                            'exp_date': prices['exp_date'], 'total_flexibility': prices['total_flexibility'], 'time_to_departure': prices['time_to_departure'], 'error': prices['error'] }
                        else:
                            model_out = {'error': flights['error']}
                else:
                    model_out = {'error': 'Due to high demand, we are currently not making any additional sales. Please check again later.'}


                # save in model
                combined.update(model_out.items())
                search_params = Searches(**combined)
                search_params.save()
                search_key = search_params.key


                # add current flight list if no errors and 'show_flights' is true
                if not model_out['error']:
                    pass
                    #model_out = refund_format_conversion(model_out)
                combined_results = {'pricing_results': model_out, 'context': 'this flight gets expensive fast', 'inputs': model_in, 'key': search_key,}

                # convert all dates into js time-stamp
                date_bank = {}
                for i in ('inputs', 'pricing_results'):
                    date_bank[i] = {}
                    for k, v in combined_results[i].iteritems():
                        try:
                            date = parse(v)
                            combined_results[i][k] = conv_to_js_date(date)
                            date_bank[i]["%s_readable" % (k)] = v
                        except:
                            pass
                if date_bank:
                    for i in ('inputs', 'pricing_results'):
                        combined_results[i].update(date_bank[i])


                if not model_out['error']:
                    combined_results.update({'success': True})

                    #combined_results['raw'] = flights
                    #return HttpResponse(json.encode(combined_results), content_type="application/json")

                    #if cd['disp_depart_date'] and cd['disp_return_date']:
                    #    combined_results.update({'flights': flights['flights']})
                    
                else:
                    # checks for short error if generated in pull_fares_range function
                    try:
                        err = flights['short_error']
                    except: 
                        err = model_out['error']

                    combined_results.update({'success': False, 'error': err})

                build = {'form': form, 'results': combined_results}
                return gen_search_display(request, build, clean, method='post')
            else:
                return HttpResponse('Not valid form.')
        else:
            form = full_option_info()
            combined_results = None
            build = {'form': form, 'results': combined_results}
            return gen_search_display(request, build, clean, method='post')


def sweep_expired(request):
    """
    @summary:   run this daily to find prices on searches that expired within 24 hours
                this will help with analysis and model building
                cycle through recently expired options
    """
    
    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if (request.POST):
        if clean:
            cred = check_creds(request.POST, Platform)
            if not cred['success']:
                return HttpResponse(json.encode(cred), content_type="application/json")

    
    # ensure this query is not run more than once/24hrs
    current_time = current_time_aware()
    run_dates = ExpiredSearchPriceCheck.objects

    if not run_dates.exists() or (current_time - run_dates.latest('run_date').run_date) >= datetime.timedelta(hours=23):
        latest_price_check = ExpiredSearchPriceCheck(run_date=current_time)
        latest_price_check.save()

        # pull searches expiring in last 24 hours
        yesterday = current_time - datetime.timedelta(days=1)
        recent_expired = Searches.objects.filter(exp_date__range=[yesterday, current_time])
        
        # check expired demos
        exp_demo_query = Demo.objects.filter(search__exp_date__range=[yesterday, current_time])
        demo_keys = [str(i.search.key) for i in exp_demo_query]

        # run flight search query on each recently expired option     
        expired_searches = []
        expired_demos = []
        for i in recent_expired:

            flights = pull_fares_range(i.origin_code, i.destination_code, (i.depart_date1, i.depart_date2), (i.return_date1, i.return_date2), i.depart_times, i.return_times, i.convenience, i.airlines, cached=True)
            expired_searches.append({'search': i.key, 'success': flights['success']})
              
            # check if search relates to an expired demo contract, if so, check if customer would have saved money
            if i.key in demo_keys and flights['success']:
                savings_string = ""
                for j in flights['fares']:
                    savings = math.floor(float(j['fare']) - i.deposit_value())
                    # don't alert customer of savings unless greater than X dollars
                    if savings >= 10:
                        dep_flights = " | ".join(["%s %s" % (k['airline_short_name'], k['flight_number']) for k in j['flight']['departing']['detail']])
                        ret_flights = " | ".join(["%s %s" % (k['airline_short_name'], k['flight_number']) for k in j['flight']['returning']['detail']])
                        dep_datetime = parse(j['flight']['departing']['take_off_time']).strftime("%B %d, %Y at %I:%M%p")
                        ret_datetime = parse(j['flight']['returning']['take_off_time']).strftime("%B %d, %Y at %I:%M%p")
                   
                        savings_string += "$%s departing %s on %s \nand returning %s on %s\n\n" % (savings, dep_datetime, dep_flights, ret_datetime, ret_flights)
                # send customer email describing potential savings if savings were possible
                if savings_string:
                    try:
                        title = "Here's what you could have saved by buying a Flex Fare"
                        body = "Thanks for checking out Level Skies and for taking a closer look at the Flex Fare. You previously signed up for a trial run of the Flex Fare and now we're hear to show you what could have happened had you actually made the purchase. Prices on the flights you were looking at went up, as they tend to do! Here are the potential savings that would have been available to you:\n\n"
                        body += savings_string + "\n\nWe hope you check in with us again soon becasue we'd love to save you some real cash!\n\nThe Level Skies Team"
                        email_address = exp_demo_query.get(search__key=i.key).customer.email
                        send_template_email(email_address, 'Flex Fare Trial', title, body)
                    except:
                        pass

                expired_demos.append({'search': i.key, 'savings': True if savings_string else False})

        #  check fares on open contracts
        contracts_query = Contract.objects.filter(search__exp_date__gt=current_time, ex_date=None)
        
        open_contracts = []
        for i in contracts_query:

            flights = pull_fares_range(i.search.origin_code, i.search.destination_code, (i.search.depart_date1, i.search.depart_date2), (i.search.return_date1, i.search.return_date2), i.search.depart_times, i.search.return_times, i.search.convenience, i.search.airlines, cached=True)
            open_contracts.append({'search': i.search.key, 'success': flights['success']})
       

        duration = current_time_aware() - current_time
        
        results = {'success': True,  'time_run': str(current_time), 'expired_demos': expired_demos, 'expired_searches': expired_searches, 'open_contracts': open_contracts, 'duration': str(duration), 'count': recent_expired.count()}

        # send email to sysadmin summarizing expired searches
        #if MODE == 'live':    
        try:
            searches_email_string = ""
            for i in expired_searches:
                searches_email_string += "%s : %s\n" % (i['search'], i['success'])

            contracts_email_string = ""
            for i in open_contracts:
                contracts_email_string += "%s : %s\n" % (i['search'], i['success'])

            demos_email_string = ""
            for i in expired_demos:
                demos_email_string += "%s : %s\n" % (i['search'], i['savings'])

            email_body = 'Completed flight search for %s expired searches with duration of %s.\n\nSearch Key : Success status\n%s\n\n' % (results['count'], results['duration'], searches_email_string)
            email_body += 'Completed %s open contracts.\n\nSearch Key : Success status\n%s\n\n' % (len(open_contracts), contracts_email_string)
            email_body += 'Completed %s expired demos.\n\nSearch Key : Savings\n%s' % (len(expired_demos), demos_email_string)
            send_mail('Expired searches price check',
                email_body,
                'sysadmin@levelskies.com',
                ['sysadmin@levelskies.com'],
                fail_silently=False)
        except:
            pass

    else:
        results = {'success': False, 'error': 'Expired search price check ran within last 24 hours.'}
        
    return gen_search_display(request, {'results': results}, clean)

