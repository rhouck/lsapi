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
from pricing.models import Search_history
from sales.models import Open, Platform
from api.views import current_time_aware, gen_search_display, gen_alphanum_key


from functions import *
from gen_price import *
from mult_search import *
from search_summary import *



from api.views import conv_to_js_date

# start date used to calculate price and lock in period both need to be changed to follow current date, not fixed date

def refund_format_conversion(pricing_results):
    pricing_results['refund_value'] = pricing_results['locked_fare']
    if pricing_results['holding_price'] and pricing_results['locked_fare']:
        pricing_results['deposit_value'] = pricing_results['holding_price'] + pricing_results['locked_fare']
    else:
        pricing_results['deposit_value'] = ''
    del pricing_results['holding_price']
    del pricing_results['locked_fare']
    return pricing_results


def search_info(request, slug, all=False):

    if not request.user.is_authenticated():
        platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])

    search = get_object_or_404(Search_history, key__iexact=slug)

    purch_date_time = current_time_aware()
    search_date_date = search.search_date

    if not all:
        expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 10) else False
        if expired:
            return HttpResponse(json.dumps({'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}), mimetype="application/json")

    search_dict = search.__dict__

    for k, v in search_dict.iteritems():
        if isinstance(v,datetime.date):
            search_dict[k] = conv_to_js_date(v)

    del search_dict['_state']
    del search_dict['open_status']
    del search_dict['id']
    del search_dict['search_type']
    del search_dict['holding_per']
    del search_dict['error']

    # convert to refund system
    search_dict = refund_format_conversion(search_dict)

    search_dict['success'] = True

    # temporary fix to terms in contract object
    search_dict['depart_times'] = 'morning'
    search_dict['return_times'] = 'evening'
    search_dict['airlines'] = 'major'
    search_dict['convenience'] = 'best options'
    del search_dict['nonstop']



    return HttpResponse(json.dumps(search_dict), mimetype="application/json")





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


def price_edu_combo(view, clean=False):
    def gen_price_edu_combo(request, clean):

        if not clean and not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('login'))
        else:
            if (request.GET):
                if clean:
                    platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])

                form = full_option_info(request.GET)
                if form.is_valid():
                    cd = form.cleaned_data

                    search_params = Search_history(origin_code=cd['origin_code'], destination_code=cd['destination_code'], holding_per=cd['holding_per'], depart_date1=cd['depart_date1'], depart_date2=cd['depart_date2'], return_date1=cd['return_date1'], return_date2=cd['return_date2'], search_type=cd['search_type'], depart_times=cd['depart_times'], return_times=cd['return_times'], nonstop=cd['nonstop'],
                                                   holding_price=25, locked_fare=500, exp_date=(datetime.datetime.now().date()+datetime.timedelta(weeks=3)),
                                                   search_date = current_time_aware(), open_status = True, key=gen_alphanum_key())
                    search_params.save()
                    search_key = search_params.key
                    inputs = {"depart_date2": "2013-06-12","return_date1": "2013-06-20","destination_code": "MAD","return_date2": "2013-06-22","origin_code": "SFO","depart_date1": "2013-06-12","depart_times": 'morning',"search_type": "rt","decision_time": 2,"return_times": 'evening',"convenience": 'best options', "airlines": "major"}
                    combined_results = {'pricing_results': {'dates': "2013612, 2013612, 2013620, 2013622",'deposit_value': 1900,'error': {0: "No error"},'refund_value': 1862}, 'context': 'this flight gets expensive fast', 'inputs': inputs, 'key': search_key}
                    build = {'form': form, 'results': combined_results}
                    return view(request, build, clean)
                else:
                    return HttpResponse('not valid form')
            else:
                form = full_option_info()
                combined_results = None
                build = {'form': form, 'results': combined_results}
                return view(request, build, clean)


            """
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
                                search_params = Search_history(origin_code=cd['origin_code'], destination_code=cd['destination_code'], holding_per=cd['holding_per'], depart_date1=inputs['depart_date1'], depart_date2=inputs['depart_date2'], return_date1=inputs['return_date1'], return_date2=inputs['return_date2'], search_type=inputs['search_type'], depart_times=inputs['depart_times'], return_times=inputs['return_times'], nonstop=inputs['nonstop'], search_date=search_date,
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
    return gen_price_edu_combo



def format_pref_input(i):
    # alters the preferences inputs from website to match format in simulation model
    if int(i) == 0:
        return []
    else:
        return [int(i)]


def conv_holding_to_lockin(inputs):
    """
    @summary: convert holidng_period to lockin_per using today's date.
                This assumes that all pricing done through API will be done in real time at current date.
    @todo: find a better way to handle the 'depart_date1' input, it currently is not ensuring proper date format
    """

    start = current_time_aware().date()

    """
    if inputs['holding_per']:
        holding_per = int(inputs['holding_per'])
    else:
        holding_per = int(inputs['lockin_per'])
    """
    holding_per = int(inputs['holding_per'])
    expiry = start + datetime.timedelta(days = holding_per*7)
    #departure = datetime.datetime.strptime(inputs['depart_date1'])
    departure = inputs['depart_date1']
    lockin_per = int(floor((departure - expiry).days / 7.0))
    #lockin_per = ((departure - expiry).days / 7.0)

    return lockin_per
