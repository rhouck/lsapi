from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import copy
import datetime
import socket
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

from api.views import gen_search_display
from api.utils import current_time_aware, conv_to_js_date, gen_alphanum_key, check_creds, run_authnet_trans, test_trans
from sales.models import *
from forms import *

from analysis.models import Cash_reserve, Additional_capacity
from pricing.models import Searches
from api.views import gen_search_display

from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
from django.views.generic import DetailView, ListView




def get_cust_list(request):

    items = Customer.objects.all()

    paginator = Paginator(items, 25)
    page = request.GET.get('page')
    try:
        short_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        short_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        short_list = paginator.page(paginator.num_pages)

    return render_to_response('sales/list.html', {'items': short_list, 'category': "Customers"}, context_instance=RequestContext(request))

def get_plat_list(request):
    items = Platform.objects.all()

    paginator = Paginator(items, 25)
    page = request.GET.get('page')
    try:
        short_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        short_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        short_list = paginator.page(paginator.num_pages)

    return render_to_response('sales/list.html', {'items': short_list, 'category': "Platforms"}, context_instance=RequestContext(request))

def get_staging_list(request):

    contracts = Staging.objects.all().order_by('id')

    paginator = Paginator(contracts, 25)
    page = request.GET.get('page')
    try:
        short_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        short_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        short_list = paginator.page(paginator.num_pages)

    return render_to_response('sales/staging_list.html', {'items': short_list}, context_instance=RequestContext(request))



def get_cust_detail(request, slug):

    cust = get_object_or_404(Customer, key__iexact=slug)
    contracts = Contract.objects.filter(customer__key=slug).order_by('-purch_date')

    paginator = Paginator(contracts, 25)
    page = request.GET.get('page')
    try:
        short_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        short_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        short_list = paginator.page(paginator.num_pages)

    return render_to_response('sales/detail.html', {'items': short_list, 'name': cust}, context_instance=RequestContext(request))

def get_plat_detail(request, slug):

    plat = get_object_or_404(Platform, key__iexact=slug)
    contracts = Contract.objects.filter(customer__platform__key=slug).order_by('-purch_date')

    paginator = Paginator(contracts, 25)
    page = request.GET.get('page')
    try:
        short_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        short_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        short_list = paginator.page(paginator.num_pages)


    return render_to_response('sales/detail.html', {'items': short_list, 'name': plat}, context_instance=RequestContext(request))






def customer_info(request, slug):


    if request.POST:
        method = 'post'
        inputs = request.POST
        request.POST = None
    else:
        method = 'get'
        inputs = request.GET if request.GET else None
        request.GET = None
    inputs = copy.deepcopy(inputs)

    if not request.user.is_authenticated():
        cred = check_creds(inputs, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")

    if inputs:
        if 'platform_key' in inputs:
            del inputs['platform_key']


    if inputs and method == 'post':
        cust = get_object_or_404(Customer, key__iexact=slug)
        for key, value in inputs.items():
            setattr(cust, key, value)
        cust.save()
        cust = get_object_or_404(Customer, key__iexact=slug)
        cust_dict = cust.__dict__
        cust_dict['update'] = True
    else:
        cust = get_object_or_404(Customer, key__iexact=slug)
        cust_dict = cust.__dict__
        cust_dict['update'] = False


    del cust_dict['_state']
    del cust_dict['platform_id']
    del cust_dict['reg_date']
    del cust_dict['key']
    del cust_dict['id']


    if 'csrfmiddlewaretoken' in cust_dict:
        del cust_dict['csrfmiddlewaretoken']
    if 'Search' in cust_dict:
        del cust_dict['Search']

    cust_dict['success'] = True

    build = {'results': cust_dict}

    if request.user.is_authenticated():
        clean = False
        del build['results']['update']
    else:
        clean = True


    return gen_search_display(request, build, clean)
    #return HttpResponse(json.encode(cust_dict), mimetype="application/json")




def find_open_contracts(request, slug):

    if not request.user.is_authenticated():
        cred = check_creds(request.GET, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")



    cust = get_object_or_404(Customer, key__iexact=slug)
    contracts = Contract.objects.filter(customer__id__iexact=cust.id).order_by('search__exp_date')

    bank = []
    for index, i in enumerate(contracts):
        if i.outstanding() and not i.staged():
            temp = {}
            temp['redeem'] = "link to purchase"
            temp['refund'] = "link to refund"
            temp['desc'] =  {
                                    'key': i.search.key,
                                    #'platform': i.platform.org_name,
                                    'origin_code': i.search.origin_code,
                                    'destination_code': i.search.destination_code,
                                    'exp_date': conv_to_js_date(i.search.exp_date),
                                    'purch_date': conv_to_js_date(i.purch_date),
                                    'depart_times': i.search.depart_times,
                                    'return_times': i.search.return_times,
                                    'convenience': i.search.convenience,
                                    'deposit': i.search.locked_fare + i.search.holding_price,
                                    'refund_value': i.search.locked_fare,
                                    'depart_date_1': conv_to_js_date(i.search.depart_date1),
                                    'return_date_1': conv_to_js_date(i.search.return_date1),
                                    'depart_date_2': conv_to_js_date(i.search.depart_date2),
                                    'return_date_2': conv_to_js_date(i.search.return_date2),
                                    }
            bank.append(temp)
    build = {}
    build['results'] = {'success': True, 'results': bank,}

    return gen_search_display(request, build, True)



def find_cust_id(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.GET if request.GET else None
    form = Customer_login(inputs)
    build = {'form': form, 'cust_title': "Find ID"}
    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:
            find_org = Platform.objects.get(key=cd['platform_key'])
            find_cust = Customer.objects.get(email=cd['email'], platform=find_org)
            build['results'] = {'success': True, 'key': find_cust.key}
            here = "worked"
        except:
            build['error_message'] = 'The customer is not registered in the system.'
            build['results'] = {'success': False, 'message': 'The customer is not registered in the system.'}
            here = "didnt work"

    #check = {'inputs': inputs, 'form_val': form.is_valid()}
    #return HttpResponse(json.encode(check), mimetype="application/json")
    return gen_search_display(request, build, clean)



def customer_signup(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.POST if request.POST else None
    if clean:
        cred = check_creds(request.POST, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")

    form = Customer_signup(inputs)
    build = {'form': form, 'cust_title': "Customer Signup"}
    if (inputs) and form.is_valid():
        cd = form.cleaned_data

        try:
            find_org = Platform.objects.get(key=cd['platform_key'])
        except (Platform.DoesNotExist):
            build['error_message'] = 'The platform name is not valid.'
            build['results'] = {'success': False, 'error': 'The platform name is not valid.'}
        else:
            try:
                find_cust = Customer.objects.get(email=cd['email'], platform=find_org)
                message = 'The email address is already registered in the system with this platform.'
                build['error_message'] = message
                build['results'] = {'success': False, 'error': message} # , 'key': find_cust.key
            except:
                cust_key = gen_alphanum_key()
                field_inps = cd
                field_inps['reg_date'] = current_time_aware().date()
                field_inps['key'] = cust_key
                field_inps['platform'] = find_org
                del field_inps['platform_key']
                new_cust = Customer(**field_inps)
                #new_cust = Customer(first_name=cd['first_name'], last_name=cd['last_name'], email=cd['email'], password=cd['password'], platform=find_org, phone=cd['phone'], address=cd['address'], city=cd['city'], state_prov=cd['state_prov'], zip_code=cd['zip_code'], country=cd['country'], reg_date=current_time_aware().date(), key=cust_key)
                new_cust.save()

                build['results'] = dict({'success': True}.items() + new_cust.__dict__.items())
                del build['results']['_platform_cache']
                del build['results']['platform_id']
                del build['results']['reg_date']
                del build['results']['_state']
                del build['results']['id']

    return gen_search_display(request, build, clean, method='post')


def purchase_option(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.POST if request.POST else None
    if clean:
        cred = check_creds(request.POST, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")



    form = Purchase_option(inputs)
    build = {'form': form, 'cust_title': "Purchase option"}

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:

            #find_org = Platform.objects.get(key=cd['platform_key'])
            find_search = Searches.objects.get(key=cd['search_key'])
            find_cust = Customer.objects.get(key__iexact=cd['cust_key']) # , platform__iexact=cd['platform']

            # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
            # or the purchase occured after too much time had passed, and the quoted price is deemed expired
            purch_date_time = current_time_aware()
            search_date_date = find_search.search_date
            expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 10) else False

            try:
                existing = Contract.objects.get(search__key=cd['search_key'])
            except:
                pass
            else:
                raise Exception

            if find_search.error or not find_search.get_status() or expired:
                raise Exception

        #except (Platform.DoesNotExist):
        #    build['error_message'] = 'The platform name is not valid.'
        #    build['results'] = {'success': False, 'error': 'The platform name is not valid.'}
        except (Searches.DoesNotExist):
            build['error_message'] = 'The option id entered is not valid.'
            build['results'] = {'success': False, 'error': 'The option id entered is not valid.'}
        except (Exception):
            build['error_message'] = 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'
            build['results'] = {'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}
        else:

            # run credit card
            amount = find_search.locked_fare + find_search.holding_price
            card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': cd['number'], 'month': cd['month'], 'year': cd['year'], 'code': cd['code']}
            cust_info = {'email': find_cust.email, 'cust_id': find_cust.key}
            address = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'phone': find_cust.phone, 'address1': find_cust.billing_address1, 'city': find_cust.billing_city, 'state_province': find_cust.billing_state_province, 'country': find_cust.billing_country, 'postal_code': find_cust.billing_postal_code}
            try:
                for i in (card_info, cust_info, address):
                    for v in i.itervalues():
                        if v == "" or v is None:
                            raise Exception
            except (Exception):
                build['error_message'] = 'Not all of the required customer information is available.'
                build['results'] = {'success': False, 'error': 'Not all of the required customer information is available.'}

            else:

                response = run_authnet_trans(amount, card_info, address=address, cust_info=cust_info)

                if response['success']:

                    new_contract = Contract(customer=find_cust, purch_date=purch_date_time, search=find_search, gateway_id=response['trans_id'])
                    # save non-sensitive cc data
                    new_contract.cc_last_four = cd['number'][-4:]
                    new_contract.cc_exp_month = cd['month']
                    new_contract.cc_exp_year = cd['year']
                    new_contract.save()
                    confirmation_url = "https://www.google.com/" # '%s/platform/%s/customer/%s' % (socket.gethostname(), find_org.key, find_cust.key)
                    build['results'] = {'success': True, 'search_key': cd['search_key'], 'cust_key': cd['cust_key'], 'purchase_date': purch_date_time.strftime('%Y-%m-%d'), 'confirmation': confirmation_url, 'gateway_status': response['status']}

                    # augment cash reserve with option price and update option inventory capacity
                    try:
                        latest_change = Cash_reserve.objects.latest('action_date')
                        new_balance = latest_change.cash_balance + new_contract.search.holding_price
                        add_cash = Cash_reserve(action_date=current_time_aware(), transaction=new_contract, cash_change=new_contract.search.holding_price, cash_balance=new_balance)
                        add_cash.save()

                        capacity = Additional_capacity.objects.get(pk=1)
                        capacity.recalc_capacity(new_balance)
                        capacity.save()
                    except:
                        pass

                else:
                    form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([response['status']])
                    #build['error_message'] = response['status']
                    build['results'] = {'success': False, 'error': response['status']}

    return gen_search_display(request, build, clean, method='post')



def exercise_option(cust_key, search_key, exercise, fare=None, dep_date=None, ret_date=None, flight_choice=None, use_gateway=True):

    build = {}

    try:

        find_cust = Customer.objects.get(key__iexact=cust_key)
        find_contract = Contract.objects.get(customer=find_cust, search__key=search_key)

    except (KeyError, Customer.DoesNotExist, Contract.DoesNotExist):
        build['error_message'] = 'The user id and/or transaction id is not valid.'
        build['results'] = {'success': False, 'error': 'The user id and/or transaction id is not valid.'}

    else:
        if not find_contract.outstanding():
            build['error_message'] = 'The contract selected is either expired or already exercised.'
            build['results'] = {'success': False, 'error': 'The contract selected is either expired or already exercised.'}

        else:
            if exercise:
                # if option is converted into airline ticket
                find_contract.ex_fare = fare
                find_contract.dep_date = dep_date
                find_contract.ret_date = ret_date
                find_contract.flight_choice = flight_choice

                # refund partial value if exercised fare below refund value
                if find_contract.search.locked_fare > fare and use_gateway:
                    card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': str(find_contract.cc_last_four).zfill(4), 'month': find_contract.cc_exp_month, 'year': find_contract.cc_exp_year}
                    response = run_authnet_trans(find_contract.search.locked_fare - fare, card_info, trans_id=find_contract.gateway_id)
                    if not response['success']:
                        build['results'] = {'success': False, 'error': response['status']}
                        return build

            else:
                # if option is refunded
                if use_gateway:
                    card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': str(find_contract.cc_last_four).zfill(4), 'month': find_contract.cc_exp_month, 'year': find_contract.cc_exp_year}
                    response = run_authnet_trans(find_contract.search.locked_fare, card_info, trans_id=find_contract.gateway_id)
                else:
                    response = {'success': True}
                if not response['success']:
                    build['results'] = {'success': False, 'error': response['status']}
                    return build


                find_contract.ex_fare = None
                find_contract.dep_date = None
                find_contract.ret_date = None
                find_contract.flight_choice = flight_choice


            exercise_date_time = current_time_aware()
            find_contract.ex_date = exercise_date_time
            find_contract.save()
            build['results'] = {'success': True, 'search_key': search_key, 'cust_key': cust_key, 'exercise_fare': find_contract.ex_fare, 'exercise_date': exercise_date_time.strftime('%Y-%m-%d')}

            # augment cash reserve with option price
            try:
                if find_contract.ex_fare > find_contract.search.locked_fare:
                    effect = find_contract.search.locked_fare - find_contract.ex_fare
                    latest_change = Cash_reserve.objects.latest('action_date')
                    new_balance = latest_change.cash_balance + effect
                    add_cash = Cash_reserve(action_date=current_time_aware(), transaction=find_contract, cash_change=effect, cash_balance=new_balance)
                    add_cash.save()

                    capacity = Additional_capacity.objects.get(pk=1)
                    capacity.recalc_capacity(new_balance)
                    capacity.save()
            except:
                pass


    return build
    #return gen_search_display(request, build, clean)



# staging views
def add_to_staging(request, action, slug):


    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if clean:
        cred = check_creds(request.POST, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")



    find_contract = get_object_or_404(Contract, search__key__iexact=slug)


    try:
        find_stage = Staging.objects.get(contract=find_contract)
        return HttpResponse(json.encode({'success': False, 'error': 'Already staged'}), mimetype="application/json")
    except (Staging.DoesNotExist):

        exercise = True if action == 'exercise' else False
        staged_cont = Staging(contract=find_contract, exercise=exercise)

        inputs = request.POST if request.POST else None
        form = AddToStagingForm(inputs)

        if form.is_valid():
            cd = form.cleaned_data
            if (find_contract.search.depart_date1 > cd['dep_date']) or (cd['dep_date'] > find_contract.search.depart_date2) or (find_contract.search.return_date1 > cd['ret_date']) or (cd['ret_date'] > find_contract.search.return_date2):
                return HttpResponse(json.encode({'success': False, 'error': 'Selected travel dates not within locked fare range'}), mimetype="application/json")

            if 'dep_date' in cd:
                staged_cont.dep_date = cd['dep_date']
            if 'ret_date' in cd:
                staged_cont.ret_date = cd['ret_date']
            if 'notes' in cd:
                staged_cont.notes = cd['notes']
            if 'flight_choice' in cd:
                staged_cont.flight_choice = cd['flight_choice']

        staged_cont.save()

        if clean:
            return HttpResponse(json.encode({'success': True}), mimetype="application/json")
        else:
            return HttpResponseRedirect(reverse('staged_item', kwargs={'slug': slug}))

    except Exception as err:
        return HttpResponse(json.encode({'success': False, 'error': '%s' % (err)}), mimetype="application/json")




def staged_item(request, slug):

    find_contract = get_object_or_404(Contract, search__key__iexact=slug)
    find_stage = get_object_or_404(Staging, contract=find_contract)

    inputs = request.POST if request.POST else None

    build = {}
    build['detail'] = find_stage

    if find_stage.exercise:

        if inputs:
            form = ExerStagingForm(inputs)
        else:
            data = {'dep_date': find_stage.dep_date, 'ret_date': find_stage.ret_date}
            form = ExerStagingForm(initial=data)

    else:
        form = RefundStagingForm(inputs)
        if form.is_valid():
            cd = form.cleaned_data

    build['form'] = form


    if inputs:

        """
        if 'remove' in inputs or 'force_close' in inputs:
            find_stage.delete()
            if 'force_close' in inputs:
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, flight_choice=cd['notes'], use_gateway=False)
            return HttpResponseRedirect(reverse('staging_view'))
        """

        # remove contract
        if 'remove' in inputs:
            find_stage.delete()
            return HttpResponseRedirect(reverse('staging_view'))

        # exercise the contract
        elif find_stage.exercise:
            if form.is_valid():
                cd = form.cleaned_data
                if (find_contract.search.depart_date1 > cd['dep_date']) or (cd['dep_date'] > find_contract.search.depart_date2) or (find_contract.search.return_date1 > cd['ret_date']) or (cd['ret_date'] > find_contract.search.return_date2):
                    build['error_message'] = 'Selected travel dates not within locked fare range'
                else:
                    if 'force_close' in inputs:
                        find_stage.delete()
                        response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=cd['fare'], dep_date=cd['dep_date'], ret_date=cd['ret_date'], flight_choice=cd['flight_choice'], use_gateway=False)
                        return HttpResponseRedirect(reverse('staging_view'))
                    else:
                        response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=cd['fare'], dep_date=cd['dep_date'], ret_date=cd['ret_date'], flight_choice=cd['flight_choice'])
                        if not response['results']['success']:
                            build['error_message'] = response['results']['error']
                        else:
                            find_stage.delete()
                            return HttpResponseRedirect(reverse('staging_view'))
            else:
                build['error_message'] = "Form not valid"

        # refund the contract
        else:
            if 'force_close' in inputs:
                find_stage.delete()
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, flight_choice=cd['notes'], use_gateway=False)
                return HttpResponseRedirect(reverse('staging_view'))
            else:
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, flight_choice=cd['notes'])
                if not response['results']['success']:
                        build['error_message'] = response['results']['error']
                else:
                    find_stage.delete()
                    return HttpResponseRedirect(reverse('staging_view'))


    return render_to_response('sales/staging.html', build, context_instance=RequestContext(request))


def staging_sweep(request):
    cont_list = []
    full_set = Contract.objects.filter(ex_date=None)

    for i in full_set:
        if not i.outstanding() and not i.staged():
            staged_cont = Staging(contract=i, exercise=False, notes="Forced staging upon expiration")
            staged_cont.save()
            cont_list.append(i)

    if not cont_list:
        message = "No contracts to stage"
    else:
        message = "Staged %s contracts" % (len(cont_list))

    return render_to_response('sales/sweep.html', {'items': cont_list, 'message': message}, context_instance=RequestContext(request))
