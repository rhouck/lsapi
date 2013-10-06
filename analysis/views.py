from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
import datetime
import time
from django.utils import simplejson
import copy
from forms import *

from pricing.views import format_pref_input
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from analysis.models import *
from sales.models import *
from api.views import current_time_aware, conv_to_js_date

from projection import *



def hello(request):
    return HttpResponse("Hello")


@login_required()
def replicated_db_status(request):

    def build_status_bank(db_name):
        db_status = db(cursorclass=MySQLdb.cursors.DictCursor, db=db_name)
        bank = []
        tables = db_status.show_tables()
        for i in tables:
            table_name = i['Tables_in_%s' % (db_name)]
            stats = db_status.show_table_stats(table_name)
            bank.append({'table_name': table_name, 'update_time': stats[0]['Update_time'], 'num_rows': stats[0]['Rows']})
        db_status.db_disconnect()
        return bank

    model = build_status_bank("steadyfa_sf_model")
    proj_prep = build_status_bank("steadyfa_projection_prep")

    return render_to_response('analysis/data_status.html', {'model': model, 'proj_prep': proj_prep})



@login_required()
def exposure(request):

    # enables user to block/prevent future sales and change amount of cash in risk pool account
    inputs = request.POST if request.POST else None
    form = Dashboard_current(inputs)
    capacity = Additional_capacity.objects.get(pk=1)
    sales_gate = Open.objects.get(pk=1)

    now = current_time_aware()

    display_time_frame_wks = 5


    if (inputs):

        #if cd['change_status']:
        if 'change_status' in inputs:

            if sales_gate.status == True:
                sales_gate.status = False

            else:
                #return HttpResponse('dont change')
                if capacity.quantity != 0:
                    sales_gate.status = True
            sales_gate.save()

        if form.is_valid():
            cd = form.cleaned_data

            if cd['cash_change']:
                try:
                    latest_change = Cash_reserve.objects.latest('action_date')
                    new_balance = latest_change.cash_balance + cd['cash_change']
                except:
                    new_balance = cd['cash_change']
                add_cash = Cash_reserve(action_date=now, transaction=None, cash_change=cd['cash_change'], cash_balance=new_balance)
                add_cash.save()

                capacity.recalc_capacity(new_balance)
                capacity.save()

        return HttpResponseRedirect('')

    # amount of cash available in option pool
    try:
        current_cash_reserve = Cash_reserve.objects.latest('action_date')
        #date = conv_to_js_date(current_cash_reserve.action_date)
        date = current_cash_reserve.action_date.strftime("%Y-%m-%d")
        cash_balance = {'last_change': date, 'cash_balance': int(current_cash_reserve.cash_balance)}
    except:
        cash_balance = {}

    # builds data for graph of cash changes over time
    try:
        cash_reserve_movement = Cash_reserve.objects.all()
        cash_movement = []
        for i in cash_reserve_movement:
            date = conv_to_js_date(i.action_date)
            cash_movement.append({'x': date, 'y': i.cash_balance, 'cash_change': i.cash_change})
        cash_movement_series = [{'name': 'cash_balance', 'data': cash_movement, 'tooltip': {'valueDecimals': 0}}]
    except:
        cash_movement_series = []

    # show current expected exposure
    expected_exposure = []
    max_exposure = []
    i = 0
    valid = True
    while valid is True:
        date = now + datetime.timedelta(days = (i * 7))
        #exposure = calc_exposure_by_date(date=date)
        exposure = capacity.calc_exposure_by_date(date=date)
        expected_exposure.append({'x': exposure['js_date'], 'y': exposure['expected_exposure'], 'count': exposure['num_outstanding']})
        max_exposure.append({'x': exposure['js_date'], 'y': exposure['max_current_exposure']})
        if i == 0:
            current_exposure = {'num_options_out': exposure['num_outstanding'], 'current_exp_exposure': int(exposure['expected_exposure']), 'next_expiration': exposure['next_expiration']}

        i += 1
        if exposure['num_outstanding'] == 0:
            valid = False

    exposure_outlook_series = [{'name': 'max_exposure', 'data': max_exposure, 'tooltip': {'valueDecimals': 0}},
                               {'name': 'expected_exposure', 'data': expected_exposure, 'tooltip': {'valueDecimals': 0}}]

    # search conversion graph
    conversion_series = []
    conversion_series.append({'name': 'total_search', 'data': []})
    conversion_series.append({'name': 'total_open_search', 'data': []})
    conversion_series.append({'name': 'valid_search', 'data': []})
    conversion_series.append({'name': 'total_purchased', 'data': []})
    conversion_series.append({'name': 'total_exercised', 'data': []})
    try:
        for i in reversed(xrange(display_time_frame_wks)):
            late = now + datetime.timedelta(days = (i * -7))
            early = late + datetime.timedelta(days = -7)

            total_search =  Search_history.objects.filter(search_date__gte = early, search_date__lte = late).count()
            total_open_search =  Search_history.objects.filter(search_date__gte = early, search_date__lte = late, open_status = True).count()
            valid_search =  Search_history.objects.filter(search_date__gte = early, search_date__lte = late, open_status = True, error = None).count()
            total_purchased =  Contract.objects.filter(purch_date__gte = early, purch_date__lte = late).count()
            total_exercised =  Contract.objects.filter(purch_date__gte = early, purch_date__lte = late, ex_fare__gte = 0).count()
            date = conv_to_js_date(late)

            conversion_series[0]['data'].append([date, total_search])
            conversion_series[1]['data'].append([date, total_open_search])
            conversion_series[2]['data'].append([date, valid_search])
            conversion_series[3]['data'].append([date, total_purchased])
            conversion_series[4]['data'].append([date, total_exercised])
    except:
        pass

    # average profit/loss per option
    average_cash_effects = []
    average_cash_effects.append({'name': 'with_margin', 'data': []})
    average_cash_effects.append({'name': 'exp_risk', 'data': []})
    try:
        for i in reversed(xrange(display_time_frame_wks)):
            late = now + datetime.timedelta(days = (i * -7))
            early = late + datetime.timedelta(days = -7)

            expired =  Contract.objects.filter(search__exp_date__gte = early, search__exp_date__lte = late, ex_fare = None)
            exercised =  Contract.objects.filter(ex_date__gte = early, ex_date__lte = late)
            total_count = expired.count() + exercised.count()

            # holding price includes margin
            expired_holding_price_sum = expired.aggregate(Sum('search__holding_price'))
            if expired_holding_price_sum['search__holding_price__sum'] is None:
                expired_holding_price_sum = 0
            else:
                expired_holding_price_sum = expired_holding_price_sum['search__holding_price__sum']
            exercised_holding_price_sum = exercised.aggregate(Sum('search__holding_price'))
            if exercised_holding_price_sum['search__holding_price__sum'] is None:
                exercised_holding_price_sum = 0
            else:
                exercised_holding_price_sum = exercised_holding_price_sum['search__holding_price__sum']

            # expected risk removes built in profit margin
            expired_exp_risk_sum = expired.aggregate(Sum('search__expected_risk'))
            if expired_exp_risk_sum['search__expected_risk__sum'] is None:
                expired_exp_risk_sum = 0
            else:
                expired_exp_risk_sum = expired_exp_risk_sum['search__expected_risk__sum']
            exercised_exp_risk_sum = exercised.aggregate(Sum('search__expected_risk'))
            if exercised_exp_risk_sum['search__expected_risk__sum'] is None:
                exercised_exp_risk_sum = 0
            else:
                exercised_exp_risk_sum = exercised_exp_risk_sum['search__expected_risk__sum']


            sum_exercised_effect = 0
            for i in exercised:
                if i.ex_fare > i.search.locked_fare:
                    sum_exercised_effect += i.ex_fare - i.search.locked_fare
            try:
                average_effect_holding_price = round(((expired_holding_price_sum + exercised_holding_price_sum - sum_exercised_effect) / total_count) * 1.0,1)
                average_effect_exp_risk = round(((expired_exp_risk_sum + exercised_exp_risk_sum - sum_exercised_effect) / total_count) * 1.0,1)
            except:
                average_effect_holding_price = average_effect_exp_risk = 0

            date = conv_to_js_date(late)
            average_cash_effects[0]['data'].append([date, average_effect_holding_price])
            average_cash_effects[1]['data'].append([date, average_effect_exp_risk])
    except:
        pass

    # show recent transactions
    recent_purchases = Contract.objects.all().order_by('-search__id')[:10]
    recent_exercises = Contract.objects.filter(ex_fare__gte = 0).order_by('-search__id')[:10]

    # build pie graphs showing characteristics of customer searches and purchases
    try:
        weeks_back = display_time_frame_wks
        # search flexibility
        cut_off_date = now + datetime.timedelta(weeks = -weeks_back)
        low_flex =  Search_history.objects.filter(search_date__gte = cut_off_date, total_flexibility__gte = 0, total_flexibility__lte = 2, error = None).count()
        mid_flex =  Search_history.objects.filter(search_date__gte = cut_off_date, total_flexibility__gte = 3, total_flexibility__lte = 6, error = None).count()
        high_flex =  Search_history.objects.filter(search_date__gte = cut_off_date, total_flexibility__gte = 7, error = None).count()
        total = (low_flex + mid_flex + high_flex) * 1.0
        search_flex_chart = [["Low Flex (0-2)", round((low_flex/total),2)], ["Mid Flex (3-6)", round((mid_flex/total),2)], ["High Flex (>6)", round((high_flex/total),2)]]
        # search hold_period
        low_hold =  Search_history.objects.filter(search_date__gte = cut_off_date, holding_per__gte = 1, holding_per__lte = 3, error = None).count()
        mid_hold =  Search_history.objects.filter(search_date__gte = cut_off_date, holding_per__gte = 4, holding_per__lte = 6, error = None).count()
        high_hold =  Search_history.objects.filter(search_date__gte = cut_off_date, holding_per__gte = 7, error = None).count()
        total = (low_hold + mid_hold + high_hold) * 1.0
        search_hold_chart = [["Short Hold Per (1-3)", round((low_hold/total),2)], ["Med Hold Per (4-6)", round((mid_hold/total),2)], ["Long Hold Per (6>)", round((high_hold/total),2)]]
        # search departure distance
        short_length =  Search_history.objects.filter(search_date__gte = cut_off_date, time_to_departure__gte = 2, time_to_departure__lte = 5, error = None).count()
        med_length =  Search_history.objects.filter(search_date__gte = cut_off_date, time_to_departure__gte = 6, time_to_departure__lte = 10, error = None).count()
        long_length =  Search_history.objects.filter(search_date__gte = cut_off_date, time_to_departure__gte = 11, error = None).count()
        total = (short_length + med_length + long_length) * 1.0
        search_dep_len_chart = [["Short dep time (2-5)", round((short_length/total),2)], ["Med dep time (6-10)", round((med_length/total),2)], ["Long dep time (10>)", round((long_length/total),2)]]
    except:
        search_flex_chart = search_hold_chart = search_dep_len_chart = []
    try:
        # purch flexibility
        cut_off_date = now + datetime.timedelta(weeks = -weeks_back)
        low_flex =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__total_flexibility__gte = 0, search__total_flexibility__lte = 2).count()
        mid_flex =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__total_flexibility__gte = 3, search__total_flexibility__lte = 6).count()
        high_flex =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__total_flexibility__gte = 7).count()
        total = (low_flex + mid_flex + high_flex) * 1.0
        purch_flex_chart = [["Low Flex (0-2)", round((low_flex/total),2)], ["Mid Flex (3-6)", round((mid_flex/total),2)], ["High Flex (>6)", round((high_flex/total),2)]]
        # purch hold_period
        low_hold =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__holding_per__gte = 1, search__holding_per__lte = 3).count()
        mid_hold =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__holding_per__gte = 4, search__holding_per__lte = 6).count()
        high_hold =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__holding_per__gte = 7).count()
        total = (low_hold + mid_hold + high_hold) * 1.0
        purch_hold_chart = [["Short Hold Per (1-3)", round((low_hold/total),2)], ["Med Hold Per (4-6)", round((mid_hold/total),2)], ["Long Hold Per (6>)", round((high_hold/total),2)]]
        # purch departure distance
        short_length =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__time_to_departure__gte = 2, search__time_to_departure__lte = 5).count()
        med_length =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__time_to_departure__gte = 6, search__time_to_departure__lte = 10).count()
        long_length =  Contract.objects.filter(search__search_date__gte = cut_off_date, search__time_to_departure__gte = 11).count()
        total = (short_length + med_length + long_length) * 1.0
        purch_dep_len_chart = [["Short dep time (2-5)", round((short_length/total),2)], ["Med dep time (6-10)", round((med_length/total),2)], ["Long dep time (10>)", round((long_length/total),2)]]
    except:
        purch_flex_chart = purch_hold_chart = purch_dep_len_chart = []

    return render_to_response('analysis/dashboard.html',
                              {'form': form, 'search_dep_len_chart': search_dep_len_chart, 'search_hold_chart': search_hold_chart, 'search_flex_chart': search_flex_chart,
                              'purch_dep_len_chart': purch_dep_len_chart, 'purch_hold_chart': purch_hold_chart, 'purch_flex_chart': purch_flex_chart,
                              'recent_purchases': recent_purchases, 'recent_exercises': recent_exercises, 'conversion': conversion_series, 'sales_gate': sales_gate.status,
                              'cash_balance': cash_balance, 'additional_capacity': {'quantity': capacity.quantity}, 'current_exposure': current_exposure, 'cash_movement': cash_movement_series,
                              'exposure_outlook': exposure_outlook_series, 'average_cash_effects': average_cash_effects},
                              context_instance=RequestContext(request))


@login_required()
def simulation_sales(request):

    inputs = request.GET if request.GET else None
    form = Simulation(inputs)

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        source_sim = 'temp_options%s' % (cd['source'])
        source_accuracy = 'temp_accuracy_testing%s' % (cd['source'])
        if cd['route']:
            where = {'route': '%s' % (cd['route'])}
        else:
            where = {}

        try:
            db_sim = db(cursorclass=MySQLdb.cursors.DictCursor)
            sim_set = db_sim.sel_crit('all', source_sim, ['purchase_date','cash_effect','holding_price','exercised_fare','lockin_per','hold_per','locked_fare','proj_week','amt_in_money'], where)
            sim_accuracy = db_sim.sel_crit('all', source_accuracy, ['*'], where)


            # builds the graph showing projection accuracy, split by projection week
            try:
                proj_weeks_bank = db_sim.sel_distinct('proj_week', source_accuracy, db_dict=True)
                depart_date_bank = []
                for k in sim_accuracy[0].iterkeys():
                    try:
                        k = int(k)
                        depart_date_bank.append(k)
                    except:
                        pass

                series_set = []

                # this calculates the aggreagete projection accuracy, ignoring the time to departure the projection was made
                results = {}
                for i in sim_accuracy:
                    for k, v in i.iteritems():
                        try:
                            k = int(k)
                            proj_week = int(i['proj_week'])
                            if v:
                                if (proj_week - k) not in results:
                                    results[proj_week - k] = []
                                results[proj_week - k].append(v)
                        except:
                            pass

                def find_max(alist):
                    return max(alist)
                def find_min(alist):
                    return min(alist)

                results_bank = []
                for k, v in results.iteritems():
                    try:
                        average = sum(v)/len(v)
                        try:
                            st_dev = standard_deviation(v)
                        except:
                            st_dev = 0
                        maximum = find_max(v)
                        minimum = find_min(v)
                        results_bank.append([k, average-st_dev, maximum, minimum, average+st_dev])
                    except:
                        pass
                series = {'name': 'Aggregate', 'data': results_bank, 'tooltip': {'valueDecimals': 0}, 'index': 1}
                series_set.append(series)

                # this calculates accuracy of projections, separating by length of time to departure of projection
                for i in proj_weeks_bank:

                    results = []
                    proj_week_where = {'proj_week': '%s' % (i)}
                    name = 'Projection Week %s' % (i)
                    index = 2

                    for j in depart_date_bank:
                        if i >= j:
                            try:
                                average = db_sim.find_simple_sum_stat(source_accuracy, 'Avg', '%s' % (j),  where = proj_week_where, db_dict=True)
                                st_dev = db_sim.find_simple_sum_stat(source_accuracy, 'StdDev', '%s' % (j),  where = proj_week_where, db_dict=True)
                                maximum = db_sim.find_simple_sum_stat(source_accuracy, 'Max', '%s' % (j),  where = proj_week_where, db_dict=True)
                                minimum = db_sim.find_simple_sum_stat(source_accuracy, 'Min', '%s' % (j),  where = proj_week_where, db_dict=True)
                                results.append([(i-j), average-st_dev, maximum, minimum, average+st_dev])
                            except:
                                pass

                    series = {'name': name, 'data': results, 'tooltip': {'valueDecimals': 0}, 'index': index}
                    series_set.append(series)

                accuracy_series = {'title': 'Accuracy of projections by distance from departure date', 'series': series_set}

            except:
                accuracy_series = {}


            # overall summary averages and st_devs
            try:
                count, exercised = 0, 0
                for i in sim_set:
                    count += 1
                    if float(i['amt_in_money']) > 0:
                        exercised += 1

                num_options = count
                percent_exericsed = round((exercised*100.0)/count,1)
                cash_effect_avg = round(db_sim.find_simple_sum_stat(source_sim, 'Avg', 'cash_effect', where = where, db_dict=True),1)
                holding_price_avg = round(db_sim.find_simple_sum_stat(source_sim, 'Avg', 'holding_price', where = where, db_dict=True),1)
                locked_fare_avg = round(db_sim.find_simple_sum_stat(source_sim, 'Avg', 'locked_fare',  where = where, db_dict=True),1)
                exercised_fare_avg = round(db_sim.find_simple_sum_stat(source_sim, 'Avg', 'exercised_fare',  where = where, db_dict=True),1)
                markup_avg = round(db_sim.find_simple_sum_stat(source_sim, 'Avg', 'markup',  where = where, db_dict=True),1)
                cash_effect_stdev = round(db_sim.find_simple_sum_stat(source_sim, 'StdDev', 'cash_effect',  where = where, db_dict=True),1)
                holding_price_stdev = round(db_sim.find_simple_sum_stat(source_sim, 'StdDev', 'holding_price',  where = where, db_dict=True),1)
                locked_fare_stdev = round(db_sim.find_simple_sum_stat(source_sim, 'StdDev', 'locked_fare',  where = where, db_dict=True),1)
                exercised_fare_stdev = round(db_sim.find_simple_sum_stat(source_sim, 'StdDev', 'exercised_fare',  where = where, db_dict=True),1)
                markup_stdev = round(db_sim.find_simple_sum_stat(source_sim, 'StdDev', 'markup',  where = where, db_dict=True),1)

                aggregate_stats = {'cash_effect_avg': cash_effect_avg, 'holding_price_avg': holding_price_avg, 'locked_fare_avg': locked_fare_avg, 'exercised_fare_avg': exercised_fare_avg, 'markup_avg': markup_avg,
                                   'cash_effect_stdev': cash_effect_stdev, 'holding_price_stdev': holding_price_stdev, 'locked_fare_stdev': locked_fare_stdev, 'exercised_fare_stdev': exercised_fare_stdev, 'markup_stdev': markup_stdev,
                                   'num_options': num_options, 'percent_exericsed': percent_exericsed}
            except:
                aggregate_stats = {}

            # builds the graph showing the cash effect of each option over time by exercise date
            try:
                series_set = []
                results = []
                for index, i in enumerate(sim_set):
                    locked_fare = i['locked_fare']
                    cash_effect = i['cash_effect']

                    open = 0
                    low = min(0, cash_effect)
                    high = max(0, cash_effect)
                    close = cash_effect
                    date = conv_to_js_date(i['purchase_date'])
                    results.append([date, open, high, low, close])

                temp_series_bank = dict()
                results = sorted(results)
                marker = 0
                counter = 0
                for index, i in enumerate(results):
                    if i[0] == marker:
                        counter += 1
                        i[0] += counter
                    else:
                        counter = 0
                        marker = i[0]
                    if counter not in temp_series_bank:
                        temp_series_bank[counter] = []
                    temp_series_bank[counter].append(results[index])
                for i in temp_series_bank.iterkeys():
                    series = {'name': 'Aggregate', 'data': temp_series_bank[i], 'tooltip': {'valueDecimals': 0}, 'depart_date': 1, 'type': 'candlestick'}
                    series_set.append(series)
                date_series = {'title': 'Cash effects of sales by purchase date', 'series': series_set, 'index': index}
            except:
                date_series = {}

            # builds the graph showing the cash effect of each option over time by exercise date
            try:
                pivot_results = {}
                proj_week_results = {}
                hold_per_results = {}

                for index, i in enumerate(sim_set):
                    cash_effect = float(i['cash_effect'])
                    holding_price = float(i['holding_price'])
                    hold_per = int(i['hold_per'])
                    proj_week = int(i['proj_week'])
                    amt_in_money = float(i['amt_in_money'])

                    # for pivot table
                    if proj_week not in pivot_results:
                        pivot_results[proj_week] = dict()
                    if hold_per not in pivot_results[proj_week]:
                        pivot_results[proj_week][hold_per] = dict()
                        pivot_results[proj_week][hold_per]['cash_effect'] = []
                        pivot_results[proj_week][hold_per]['holding_price'] = []
                    pivot_results[proj_week][hold_per]['cash_effect'].append(cash_effect)
                    pivot_results[proj_week][hold_per]['holding_price'].append(holding_price)


                    # for proj week only table
                    if proj_week not in proj_week_results:
                        proj_week_results[proj_week] = dict()
                        proj_week_results[proj_week]['cash_effect'] = []
                        proj_week_results[proj_week]['holding_price'] = []
                        proj_week_results[proj_week]['exercise'] = 0
                    proj_week_results[proj_week]['cash_effect'].append(cash_effect)
                    proj_week_results[proj_week]['holding_price'].append(holding_price)
                    if amt_in_money > 0:
                        proj_week_results[proj_week]['exercise'] += 1


                    # for hold per only table
                    if hold_per not in hold_per_results:
                        hold_per_results[hold_per] = dict()
                        hold_per_results[hold_per]['cash_effect'] = []
                        hold_per_results[hold_per]['holding_price'] = []
                        hold_per_results[hold_per]['exercise'] = 0
                    hold_per_results[hold_per]['cash_effect'].append(cash_effect)
                    hold_per_results[hold_per]['holding_price'].append(holding_price)
                    if amt_in_money > 0:
                        hold_per_results[hold_per]['exercise'] += 1


                results_format = []
                series_set = []
                for i, j in pivot_results.iteritems():
                    for k, v in j.iteritems():
                        results_format.append({'x': i, 'y': k, 'count': len(v['cash_effect']), 'cash_effect': int(sum(v['cash_effect'])/len(v['cash_effect'])), 'holding_price': int(sum(v['holding_price'])/len(v['holding_price']))})
                series = {'name': 'Aggregate', 'data': results_format, 'tooltip': {'valueDecimals': 0}}
                series_set.append(series)
                pivot_series = {'title': 'Average holding price & cash effect by weeks to departure and holding length', 'series': series_set}


                results_format = []
                exercised_format = []
                series_set = []
                for i, j in proj_week_results.iteritems():
                    results_format.append({'x': i, 'y': int(sum(j['cash_effect'])/len(j['cash_effect'])), 'count': len(j['cash_effect']), 'holding_price': int(sum(j['holding_price'])/len(j['holding_price']))})
                    exercised_format.append({'x': i, 'y': float(j['exercise'])/float(len(j['cash_effect']))})
                series = {'name': 'Cash Effect', 'data': results_format, 'tooltip': {'valueDecimals': 0}, 'yAxis': 1, 'type': 'column'}
                series_set.append(series)
                series = {'name': 'Exercised', 'data': exercised_format, 'tooltip': {'valueDecimals': 0}, 'type': 'line'}
                series_set.append(series)
                proj_week_series = {'title': 'Gain/loss by weeks to departure', 'series': series_set}


                exercised_format = []
                results_format = []
                series_set = []
                for i, j in hold_per_results.iteritems():
                    results_format.append({'x': i, 'y': int(sum(j['cash_effect'])/len(j['cash_effect'])), 'count': len(j['cash_effect']), 'holding_price': int(sum(j['holding_price'])/len(j['holding_price']))})
                    exercised_format.append({'x': i, 'y': float(j['exercise'])/float(len(j['cash_effect']))})
                series = {'name': 'Cash Effect', 'data': results_format, 'tooltip': {'valueDecimals': 0}, 'yAxis': 1, 'type': 'column'}
                series_set.append(series)
                series = {'name': 'Exercised', 'data': exercised_format, 'tooltip': {'valueDecimals': 0}, 'type': 'line'}
                series_set.append(series)
                hold_per_series = {'title': 'Gain/loss by weeks held before exercise', 'series': series_set}


            except:
                pivot_series = {}
                proj_week_series = {}
                hold_per_series = {}

            return render_to_response('analysis/sim_charts.html', {'form': form, 'date': date_series, 'pivot': pivot_series, 'proj_week': proj_week_series, 'hold_per': hold_per_series, 'aggregate_stats': aggregate_stats, 'accuracy': accuracy_series})

        except:
            return render_to_response('analysis/sim_charts.html', {'form': form, 'error_message': 'The table selected did not return any results.',}, context_instance=RequestContext(request))
    else:
        return render_to_response('analysis/sim_charts.html', {'form': form})


@login_required()
def overlay(request, departure_trend):

    inputs = request.GET if request.GET else None
    form = Overlay(inputs)

    if (inputs) and form.is_valid():
        cd = form.cleaned_data

        try:
            inputs = search_inputs(purpose='projection', start_date=cd['proj_date'], origin=cd['origin'], destination=cd['destination'], num_high_days=cd['num_high_days'], dep_time_pref=format_pref_input(cd['depart_times']), ret_time_pref=format_pref_input(cd['return_times']), stop_pref=format_pref_input(cd['nonstop']),
                                   num_per_look_back = cd['num_per_look_back'], weight_on_imp = cd['weight_on_imp'], ensure_suf_data = cd['ensure_suf_data'], seasonality_adjust = cd['seasonality_adjust'], regressed = cd['regressed'], black_list_error=cd['black_list_error'], depart_length_width = cd['depart_length_width'], width_of_avg = cd['width_of_avg'],
                                   num_wks_proj_out=cd['num_wks_proj_out'], final_proj_week = cd['final_proj_week'], first_proj_week = cd['first_proj_week'])
            projections = projection(inputs)

            db_date = db(cursorclass=MySQLdb.cursors.DictCursor, db='steadyfa_projection_prep')
            latest_add_date = db_date.find_simple_sum_stat("%s%s" % (inputs.origin, inputs.destination), 'Max', 'date_collected', db_dict=True)
            db_date.db_disconnect()

            db_min = db(cursorclass=MySQLdb.cursors.DictCursor, db='steadyfa_temp_tables')
            db_min.pull_mins(inputs.origin, inputs.destination, datetime.date(1900,1,1), latest_add_date, inputs.flight_type, inputs.max_trip_length, inputs.prefs.id, num_high_days=inputs.num_high_days, adj_name='graph_build_')

            series_set = []

            """
            if inputs.black_list_error:
                black_list_bank = []
                for i in projections.previous.black_list.itervalues():
                    black_list_bank.append(i['beg_period'])
            """

            for i, j in projections.adjusted_fares[projections.type].projected.iteritems():
                results = []
                for k, v in j.iteritems():
                    if isinstance(k, int) and v:
                        try:
                            st_dev = projections.adjusted_fares[projections.type].standard_deviations[i][k]
                            actual = db_min.find_simple_sum_stat('graph_build_minimums', 'Avg', 'min_fare', where = {'depart_length': k*7}, greater = {'depart_date': j['beg_period']}, less = {'depart_date': (j['beg_period'] + datetime.timedelta(days = 7))}, db_dict=True)
                            actual = float(actual)

                            if departure_trend == 'relative':
                                if st_dev:
                                    vals = ((float(v)-st_dev)/actual - 1, (float(v)+st_dev)/actual - 1)
                                else:
                                    vals = (float(v)/actual - 1, float(v)/actual - 1)
                            else:
                                if st_dev:
                                    vals = (float(v)-st_dev-actual, float(v)+st_dev-actual)
                                else:
                                    vals = (float(v)-actual, float(v)-actual)
                            date = conv_to_js_date((j['beg_period'] - datetime.timedelta(days = int(k)*7)))
                            results.append([date, vals[0], vals[1]])

                        except:
                            pass
                results = sorted(results)

                series = {'name': 'dep week - %s' % (j['beg_period']), 'data': results, 'tooltip': {'valueDecimals': 0}, 'depart_date': int(i)}

                series_set.append(series)
                """
                if inputs.black_list_error:
                    if j['beg_period'] in black_list_bank:
                        del series_set[-1]
                """
            return render_to_response('analysis/highstock.html', {'form': form, 'title': 'Projected vs Actual fares from %s to %s as of %s' % (inputs.origin, inputs.destination, inputs.start_date), 'series': series_set, 'visible': 10, 'type': 'areasplinerange', 'plot_line': 0.001})
        except:
            return render_to_response('analysis/highstock.html', {'form': form, 'error_message': 'The route selected did not return any results.',}, context_instance=RequestContext(request))
    else:
        return render_to_response('analysis/highstock.html', {'form': form})



@login_required()
def projections(request, format):

    inputs = request.GET if request.GET else None
    form = Projection(inputs)

    if (inputs) and form.is_valid():
        cd = form.cleaned_data

        inputs = search_inputs(purpose='projection', origin=cd['origin'], destination=cd['destination'], num_high_days=cd['num_high_days'], dep_time_pref=format_pref_input(cd['depart_times']), ret_time_pref=format_pref_input(cd['return_times']), stop_pref=format_pref_input(cd['nonstop']))
        try:
            db_proj = db(cursorclass=MySQLdb.cursors.DictCursor)
            projections = db_proj.sel_crit('all', 'projections', ['*'], {'route': "%s_%s" % (inputs.origin, inputs.destination), 'num_high_days': inputs.num_high_days, 'prefs': inputs.prefs.id, 'flight_type': inputs.flight_type})

            series_set = []
            """
            black_list_bank = []
            try:
                black_list_source = db_proj.sel_crit('all', 'black_list', ['beg_period'], {'route': "%s_%s" % (inputs.origin, inputs.destination), 'num_high_days': inputs.num_high_days, 'prefs': inputs.prefs.id, 'flight_type': inputs.flight_type})
                for i in black_list_source:
                    black_list_bank.append(i['beg_period'])
            except:
                pass
            """

            if format == "date":
                for i in projections:
                    results = []
                    for k, v in i.iteritems():
                        if k.isdigit() and v:
                            date = conv_to_js_date((i['beg_period'] - datetime.timedelta(days = int(k)*7)))
                            results.append([date, float(v)])
                    results = sorted(results)
                    series = {'name': 'dep week - %s' % (i['beg_period']), 'data': results, 'tooltip': {'valueDecimals': 0}, 'depart_date': int(i['proj_week'])}
                    series_set.append(series)
                    """
                    if i['beg_period'] in black_list_bank:
                        del series_set[-1]
                    """
                return render_to_response('analysis/highstock.html', {'form': form, 'title': 'Projected fares from %s to %s by departure date' % (inputs.origin, inputs.destination), 'series': series_set, 'visible': 20, 'type': 'spline'})

            else:
                results = dict()
                for i in projections:
                    for k, v in i.iteritems():
                        if k.isdigit() and v:
                            if k not in results:
                                results[k] = []
                            date = conv_to_js_date(i['beg_period'])
                            """
                            if i['beg_period'] in black_list_bank:
                                v = 0
                            """
                            results[k].append([date, float(v)])

                for k in results.iterkeys():
                    results[k] = sorted(results[k])
                    series = {'name': 'dep length - %s' % (int(k)*7), 'data': results[k], 'tooltip': {'valueDecimals': 0}, 'depart_date': int(k)}
                    series_set.append(series)
                series_set_2 = sorted(series_set, key=lambda k: k['depart_date'])
                return render_to_response('analysis/highstock.html', {'form': form, 'title': 'Projected fares from %s to %s by time to departure' % (inputs.origin, inputs.destination), 'series': series_set_2, 'visible': 20, 'type': 'spline'})

        except:
            return render_to_response('analysis/highstock.html', {'form': form, 'error_message': 'The route selected did not return any results.',}, context_instance=RequestContext(request))

    else:
        return render_to_response('analysis/highstock.html', {'form': form})


@login_required()
def historical(request, departure_trend):

    if departure_trend:
        template = 'analysis/highchart.html'
    else:
        template = 'analysis/highstock.html'

    inputs = request.GET if request.GET else None
    form = Historical(inputs)

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:
            num_high_days = cd['num_high_days']
        except:
            num_high_days = None


        inputs = search_inputs(purpose='projection', origin=cd['origin'], destination=cd['destination'], num_high_days=num_high_days, dep_time_pref=format_pref_input(cd['depart_times']), ret_time_pref=format_pref_input(cd['return_times']), stop_pref=format_pref_input(cd['nonstop']))
        try:
            db_min = db(cursorclass=MySQLdb.cursors.DictCursor, db='steadyfa_projection_prep')
            latest_add_date = db_min.find_simple_sum_stat("%s%s" % (inputs.origin, inputs.destination), 'Max', 'date_collected', db_dict=True)
            inputs.start_date = latest_add_date
            db_min.pull_mins(inputs.origin, inputs.destination, datetime.date(1900,1,1), inputs.start_date, inputs.flight_type, inputs.max_trip_length, inputs.prefs.id, num_high_days=inputs.num_high_days, adj_name='graph_build_')

            series_set = []
            for i in range(1, cd['depart_length_max']+1):
                try:
                    if departure_trend:
                        series = db_min.analysis_graph_search('Avg', depart_length = (i*7), trip_length = (cd['trip_length_min'],cd['trip_length_max']), start_date=inputs.start_date)
                        series = sorted(series, reverse=True)
                        results = []
                        for index, j in enumerate(series):
                            if departure_trend == 'relative':
                                if index == 0:
                                    beg = j['min_fare']
                                    results.append([int(j['depart_length']), 1])
                                else:
                                    results.append([int(j['depart_length']), j['min_fare'] / beg])
                            else:
                                results.append([int(j['depart_length']), j['min_fare']])
                        series = {'name': 'departed week of %s' % (inputs.start_date - datetime.timedelta(days = i*7)), 'data': results, 'tooltip': {'valueDecimals': 0}, 'depart_date': i}
                        series_set.append(series)

                    else:
                        series = db_min.analysis_graph_search('Avg', depart_length = (i*7), trip_length = (cd['trip_length_min'],cd['trip_length_max']))
                        results = []
                        for j in series:
                            date = conv_to_js_date(j['depart_date'])
                            results.append([date, j['min_fare']])
                        series = {'name': 'departs in %s weeks' % (i), 'data': results, 'tooltip': {'valueDecimals': 0}, 'depart_date': i}
                        series_set.append(series)
                except:
                    pass
            return render_to_response(template, {'form': form, 'title': 'Historical fares from %s to %s' % (inputs.origin, inputs.destination), 'series': series_set, 'visible': 5, 'type': 'spline'})
        except:
            return render_to_response(template, {'form': form, 'error_message': 'The route selected did not return any results.',}, context_instance=RequestContext(request))

    else:
        return render_to_response(template, {'form': form})

