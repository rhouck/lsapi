import time
import datetime
import sys
from random import randint
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404

from forms import *
from pricing.models import Searches
from sales.models import Platform, Contract
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
from pricing.utils import *

from dateutil.parser import parse

from temp import return_search_res


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
    return HttpResponse(json.encode(res), mimetype="application/json")

def test_skyscan(request):
    """
    # grid search
    url = 'browsegrid/v1.0/GB/GBP/en-GB/LHR/FRA/2013-12/2014-01'
    res = call_sky(url, data={}, method='get')
    return HttpResponse(json.encode(res), mimetype="application/json")
    """

    """
    # price caching api - seems to pull cached fare on specific flight
    url = 'pricing/v1.0/GB/GBP/en-GB/LHR/FRA/2013-12/2014-01'
    res = call_sky(url, method='get')
    return HttpResponse(json.encode(res), mimetype="application/json")
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
    return HttpResponse(json.encode(res), mimetype="application/json")

def test_flight_search(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if (request.POST):
        if clean:
            cred = check_creds(request.POST, Platform)
            if not cred['success']:
                return HttpResponse(json.encode(cred), mimetype="application/json")


        form = flight_search_form(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            #res = pull_fares_range(cd['origin_code'], cd['destination_code'], (cd['depart_date1'], cd['depart_date1']), (cd['return_date1'], cd['return_date1']), cd['depart_times'], cd['return_times'], cd['convenience'], airlines=None)
            #return HttpResponse(json.dumps(res), mimetype="application/json")
            res = run_flight_search(cd['origin_code'], cd['destination_code'], cd['depart_date1'], cd['return_date1'], cd['depart_times'], cd['return_times'], cd['convenience'], airlines=None, cache_only=False)
            build = {'form': form, 'results': res}

        else:
            build = {'results': {'success': False, 'error': "Invalid inputs."}}

    else:
        form = flight_search_form()
        combined_results = None
        build = {'form': form, 'results': combined_results}

    return gen_search_display(request, build, clean, method='post')



def display_current_flights(request, slug, convert=False):

    inputs = request.GET if request.GET else None
    form = flights_display(inputs)


    if not request.user.is_authenticated():
        cred = check_creds(inputs, Platform)
        if not cred['success']:
            return HttpResponse(json.dumps(cred), mimetype="application/json")

    try:
        if not form.is_valid():
            raise Exception("Valid travel dates not provided: depart_date & return_date")

        cd = form.cleaned_data
        search = Searches.objects.get(key__iexact=slug)

        if convert:
            # raise error if contract is not outstanding or has already been marked for staging process
            contract = Contract.objects.get(search__key__iexact=slug)
            if not contract.outstanding() or contract.staged():
                raise Exception("This contract is no longer valid or has already been converted.")

            if (contract.search.depart_date1 > cd['depart_date']) or (cd['depart_date'] > contract.search.depart_date2) or (contract.search.return_date1 > cd['return_date']) or (cd['return_date'] > contract.search.return_date2):
                raise Exception('Selected travel dates not within locked fare range.')
        else:
            # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
            # or the purchase occured after too much time had passed, and the quoted price is deemed expired
            purch_date_time = current_time_aware()
            search_date_date = search.search_date
            expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 30) else False

            if search.error or not search.get_status() or expired:
                raise Exception("The search is expired, had an error, or was made while sales were shut off")


        airlines = 'any'
        if cd['dev_test']:
            res = run_flight_search('SFO', 'JFK', datetime.date(2014,4,1), datetime.date(2014,5,1), 'any', 'any', 'any', airlines=None)
        else:
            res = run_flight_search(search.origin_code, search.destination_code, cd['depart_date'], cd['return_date'], search.depart_times, search.return_times, search.convenience, airlines)

        if convert:
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
                        res['flights'][index]['rebate'] = search.locked_fare - i['fare']
                    else:
                        res['flights'][index]['rebate'] = None
                    del res['flights'][index]['fare']

                    bank.append(res['flights'][index])

            res['flights'] = bank


    except (Contract.DoesNotExist):
        res = {'success': False, 'error': 'The contract key entered is not valid.'}
    except (Searches.DoesNotExist):
        res = {'success': False, 'error': 'The search key entered is not valid.'}
    except Exception as err:
        res = {'success': False, 'error': str(err)}

    return HttpResponse(json.encode(res), mimetype="application/json")

def search_info(request, slug, all=False):

    if not request.user.is_authenticated():
        cred = check_creds(request.GET, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")

    search = get_object_or_404(Searches, key__iexact=slug)

    purch_date_time = current_time_aware()
    search_date_date = search.search_date

    if not all:
        expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 30) else False
        if expired:
            return HttpResponse(json.encode({'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}), mimetype="application/json")

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
    search_dict = refund_format_conversion(search_dict)

    search_dict['success'] = True
    return HttpResponse(json.encode(search_dict), mimetype="application/json")

def price_edu_combo(request):

        """
        if not clean and not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('login'))
        else:
        """
        if request.user.is_authenticated():
            clean = False
        else:
            clean = True

        if (request.POST):
            if clean:
                cred = check_creds(request.POST, Platform)
                if not cred['success']:
                    return HttpResponse(json.encode(cred), mimetype="application/json")


            form = full_option_info(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                #inp_errors = sim_errors(self.db, cd['origin_code'], cd['destination_code'],self.lockin_per,self.start_date,self.d_date1,self.d_date2,self.r_date1,self.r_date2,self.final_proj_week, self.max_trip_length, self.geography)
                #flights = pull_fares_range(, , (cd['depart_date1'], cd['depart_date2']), (cd['return_date1'], cd['return_date2']), cd['depart_times'], cd['return_times'], cd['convenience'], airlines=None, display_dates=(cd['disp_depart_date'], cd['disp_return_date']))
                #return HttpResponse(json.encode({'inputs': cd}), mimetype="application/json")


                open_status = Open.objects.get(pk=1)

                general = {'search_date': current_time_aware(), 'open_status': open_status.get_status(), 'key': gen_alphanum_key(),}

                model_in = {'origin_code': cd['origin_code'], 'destination_code': cd['destination_code'], 'holding_per': cd['holding_per'],
                            'depart_date1': str(cd['depart_date1']), 'depart_date2': str(cd['depart_date2']), 'return_date1': str(cd['return_date1']), 'return_date2': str(cd['return_date2']),
                            'search_type': 'rt', 'depart_times': cd['depart_times'], 'return_times': cd['return_times'], 'convenience': cd['convenience'],}

                combined = dict(general.items() + model_in.items())

                if open_status.get_status():
                    if (cd['depart_date2'] - cd['depart_date1']).days > 1 or (cd['return_date2'] - cd['return_date1']).days > 1:
                        model_out = {'error': 'Travel date ranges must not be more than one day in length'}
                    else:
                        if cd['dev_test']:
                            flights = pull_fares_range('SFO', 'JFK', (datetime.date(2014,4,1), datetime.date(2014,4,1)), (datetime.date(2014,5,1), datetime.date(2014,5,1)), 'any', 'any', 'any', airlines=None)
                        else:
                            flights = pull_fares_range(cd['origin_code'], cd['destination_code'], (cd['depart_date1'], cd['depart_date2']), (cd['return_date1'], cd['return_date2']), cd['depart_times'], cd['return_times'], cd['convenience'], airlines=None)


                        if flights['success']:
                            prices = calc_price(cd['origin_code'], cd['destination_code'], flights['fares'], cd['holding_per']*7, [cd['depart_date1'],cd['depart_date2']], [cd['return_date1'],cd['return_date2']])
                            model_out = {'holding_price': prices['holding_price'], 'locked_fare': prices['locked_fare'], 'expected_risk': prices['expected_risk'],
                                            'exp_date': prices['exp_date'], 'total_flexibility': prices['total_flexibility'], 'time_to_departure': prices['time_to_departure'], 'error': prices['error'] }
                        else:
                            model_out = {'error': flights['error']}
                else:
                    model_out = {'error': 'Sales currently disabled'}


                # save in model
                combined.update(model_out.items())
                search_params = Searches(**combined)
                search_params.save()
                search_key = search_params.key


                # add current flight list if no errors and 'show_flights' is true
                if not model_out['error']:
                    model_out = refund_format_conversion(model_out)
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
                    #return HttpResponse(json.encode(combined_results), mimetype="application/json")

                    #if cd['disp_depart_date'] and cd['disp_return_date']:
                    #    combined_results.update({'flights': flights['flights']})
                else:
                    combined_results.update({'success': False, 'error': model_out['error']})

                build = {'form': form, 'results': combined_results}
                return gen_search_display(request, build, clean, method='post')
            else:
                return HttpResponse('not valid form')
        else:
            form = full_option_info()
            combined_results = None
            build = {'form': form, 'results': combined_results}
            return gen_search_display(request, build, clean, method='post')


            """

            def conv_holding_to_lockin(inputs):

                #@summary: convert holidng_period to lockin_per using today's date.
                #            This assumes that all pricing done through API will be done in real time at current date.
                #@todo: find a better way to handle the 'depart_date1' input, it currently is not ensuring proper date format


                start = current_time_aware().date()


                #if inputs['holding_per']:
                #    holding_per = int(inputs['holding_per'])
                #else:
                #    holding_per = int(inputs['lockin_per'])

                holding_per = int(inputs['holding_per'])
                expiry = start + datetime.timedelta(days = holding_per*7)
                #departure = datetime.datetime.strptime(inputs['depart_date1'])
                departure = inputs['depart_date1']
                lockin_per = int(floor((departure - expiry).days / 7.0))
                #lockin_per = ((departure - expiry).days / 7.0)

                return lockin_per



            if (request.GET):
                form = full_option_info(request.GET)
                if form.is_valid():
                    cd = form.cleaned_data
                    open_status = Open.objects.get(pk=1)

                    if open_status.get_status():
                        # run gen_price
                        lockin_per = conv_holding_to_lockin(cd)
                        inputs = search_inputs(purpose='simulation', source = '', origin=cd['origin_code'], destination=cd['destination_code'], lockin_per=lockin_per, d_date1=cd['depart_date1'], d_date2=cd['depart_date2'], r_date1=cd['return_date1'], r_date2=cd['return_date2'], flight_type=cd['search_type'], dep_time_pref=format_pref_input(cd['depart_times']), ret_time_pref=format_pref_input(cd['return_times']), stop_pref=format_pref_input(cd['nonstop']), geography=select_geography(cd['origin_code']))
                        example = simulation(inputs)
                        pricing_results_full = example.return_simulation(expanded=True)

                        if 'output' in pricing_results_full:
                            pricing_results = pricing_results_full['output']
                            #pricing_results = {'combos': pricing_results_full['first_week_combos'], 'stats': pricing_results_full['first_week_stats']}
                        else:
                            pricing_results = pricing_results_full


                        # if prefs changed during the gen_price script, make sure new prefs are used in the search_summary script
                        if 'changed_prefs' in pricing_results:

                            depart_times = pricing_results['changed_prefs']['depart_times']
                            return_times = pricing_results['changed_prefs']['return_times']
                            nonstop = pricing_results['changed_prefs']['nonstop']

                            # reformat 'changed prefs' to match preferences inputs style


                            #del pricing_results['changed_prefs']['airline']
                            #for k, v in pricing_results['changed_prefs'].iteritems():
                            #    if not v:
                            #        pricing_results['changed_prefs'][k] = 0
                            #    else:
                            #        pricing_results['changed_prefs'][k] = v[0]


                            changed_prefs = pricing_results.pop('changed_prefs')
                            del changed_prefs['airline']
                            for k, v in changed_prefs.iteritems():
                                if not v:
                                    changed_prefs[k] = 0
                                else:
                                    changed_prefs[k] = v[0]

                        else:
                            changed_prefs = None
                            depart_times = format_pref_input(cd['depart_times'])
                            return_times = format_pref_input(cd['return_times'])
                            nonstop = format_pref_input(cd['nonstop'])


                        # run search_summary
                        inputs = search_inputs(purpose='projection', origin=cd['origin_code'], destination=cd['destination_code'], flight_type=cd['search_type'], dep_time_pref=depart_times, ret_time_pref=return_times, stop_pref=nonstop)
                        example_two = aggregate_search_summaries(inputs)
                        try:
                            cust_edu_results = example_two.display_single_search()

                            #randomly select one customer education element, if none available, use a review
                            bank = []
                            if cust_edu_results['price_swings']:
                                bank.append('price_swings')
                            if cust_edu_results['recent_peak_fare']:
                                bank.append('recent_peak_fare')
                            if cust_edu_results['popular_purchase']:
                                bank.append('popular_purchase')
                            if len(bank) > 0:
                                pick = bank[randint(0, (len(bank)-1))]
                            else:
                                pick = 'review'

                            #short_cust_ed = {'%s' % (pick): cust_edu_results['%s' % (pick)]}
                            #cust_edu_results = short_cust_ed
                            cust_edu_results = cust_edu_results['%s' % (pick)]
                        except:
                            cust_edu_results = example_two.pull_rand_review()
                    else:
                        pricing_results = {'holding_price': "", 'locked_fare': "", 'error': {}, 'dates': ""}
                        cust_edu_results = "Due to high demand, there are currently no Levelskies products available for sale. Please check again soon."
                        changed_prefs = None


                    inputs = dict()
                    for k, v in cd.iteritems():
                        if type(v) is datetime.date:
                            v = str(v)
                        inputs[k] = v
                    #inputs['lockin_per'] = lockin_per


                    # log search query unless done within api for testing purposes (i.e. not "clean" version)
                    search_date = current_time_aware()
                    time_to_departure =(cd['depart_date1'] - search_date.date()).days / 7
                    numdays_dep = (cd['depart_date2']-cd['depart_date1']).days
                    try:
                        numdays_ret = (cd['return_date2']-cd['return_date1']).days
                    except:
                        numdays_ret = 0
                    total_flexibility = numdays_dep + numdays_ret
                    if clean:
                        if open_status.get_status() and 0 in pricing_results['error']:
                            try:
                                max_avg = avearege_max_projected_stats(pricing_results_full['first_week_stats'], pricing_results_full['first_week_combos'])
                                first_week_max_fare = max_avg['max_fare']
                                first_week_max_st_dev = max_avg['max_st_dev']
                                first_week_avg_fare = max_avg['avg_fare']
                                first_week_avg_st_dev = max_avg['avg_st_dev']

                                if pricing_results_full['second_week_stats']:
                                    max_avg = avearege_max_projected_stats(pricing_results_full['second_week_stats'], pricing_results_full['second_week_combos'])
                                    second_week_max_fare = max_avg['max_fare']
                                    second_week_max_st_dev = max_avg['max_st_dev']
                                    second_week_avg_fare = max_avg['avg_fare']
                                    second_week_avg_st_dev = max_avg['avg_st_dev']
                                else:
                                    second_week_max_fare = second_week_max_st_dev = second_week_avg_fare = second_week_avg_st_dev = None

                                exp_date = search_date.date() + datetime.timedelta(weeks = cd['holding_per'])
                                search_params = Searches(origin_code=cd['origin_code'], destination_code=cd['destination_code'], holding_per=cd['holding_per'], depart_date1=inputs['depart_date1'], depart_date2=inputs['depart_date2'], return_date1=inputs['return_date1'], return_date2=inputs['return_date2'], search_type=inputs['search_type'], depart_times=inputs['depart_times'], return_times=inputs['return_times'], nonstop=inputs['nonstop'], search_date=search_date,
                                                               holding_price=pricing_results_full['output']['holding_price'], locked_fare=pricing_results_full['output']['locked_fare'], buffer=pricing_results_full['buffer'], correl_coef=pricing_results_full['correl_coef'], cycles=pricing_results_full['cycles'], expected_risk=pricing_results_full['expected_risk'], lockin_per=pricing_results_full['lockin_per'], markup=pricing_results_full['markup'], round_to=pricing_results_full['round_to'], wtp=pricing_results_full['wtp'], wtpx=pricing_results_full['wtpx'], max_trip_length=pricing_results_full['max_trip_length'], exp_date=exp_date,
                                                               first_week_avg_proj_fare = first_week_avg_fare, first_week_max_proj_fare = first_week_max_fare, second_week_avg_proj_fare = second_week_avg_fare, second_week_max_proj_fare = second_week_max_fare,
                                                               first_week_avg_proj_st_dev = first_week_avg_st_dev, first_week_max_proj_st_dev = first_week_max_st_dev, second_week_avg_proj_st_dev = second_week_avg_st_dev, second_week_max_proj_st_dev = second_week_max_st_dev,
                                                               open_status = open_status.get_status(), total_flexibility=total_flexibility, time_to_departure=time_to_departure, geography=pricing_results_full['geography'], key=gen_alphanum_key())
                                search_params.save()
                                search_key = search_params.key


                            except:
                                search_key = None

                        else:
                            geography = select_geography(cd['origin_code'])
                            try:
                                try:
                                    error = ', '.join(['%s: %s' % (key, value) for (key, value) in pricing_results['error'].items()])
                                except:
                                    error = None

                                search_params = Search_history(origin_code=cd['origin_code'], destination_code=cd['destination_code'], holding_per=cd['holding_per'], depart_date1=inputs['depart_date1'], depart_date2=inputs['depart_date2'], return_date1=inputs['return_date1'], return_date2=inputs['return_date2'], search_type=inputs['search_type'], depart_times=inputs['depart_times'], return_times=inputs['return_times'], nonstop=inputs['nonstop'], search_date=search_date,
                                                               open_status = open_status.get_status(), error = error, total_flexibility=total_flexibility, time_to_departure=time_to_departure, geography=geography)
                                search_params.save()
                            except:
                                pass
                            search_key = None
                    else:
                        search_key = None

                    # deposit format conversion
                    pricing_results = refund_format_conversion(pricing_results)

                    #pricing_results['refund_value'] = pricing_results['locked_fare']
                    #if pricing_results['holding_price'] and pricing_results['locked_fare']:
                    #    pricing_results['deposit_value'] = pricing_results['holding_price'] + pricing_results['locked_fare']
                    #else:
                    #    pricing_results['deposit_value'] = ''
                    #del pricing_results['holding_price']
                    #del pricing_results['locked_fare']


                    combined_results = [{'pricing_results': pricing_results, 'context': cust_edu_results, 'inputs': inputs, 'key': search_key}]
                    if changed_prefs:
                        combined_results[0]['changed_prefs'] = changed_prefs
                else:
                    combined_results = None
            else:
                form = full_option_info()
                combined_results = None
            build = {'form': form, 'results': combined_results}
            return view(request, build, clean)
            """
            #return gen_price_edu_combo



