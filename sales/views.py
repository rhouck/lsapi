from django.core.mail import send_mail
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

from api.views import gen_search_display, current_time_aware
from api.utils import conv_to_js_date, gen_alphanum_key, check_creds, run_authnet_trans, test_trans
from sales.models import *
from forms import *

from analysis.models import Cash_reserve, Additional_capacity
from pricing.models import Searches
from api.views import gen_search_display

from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
from django.views.generic import DetailView, ListView

from sales.utils import exercise_option, send_template_email

from api.settings import MODE, HIGHRISE_CONFIG

import ast

from pricing.utils import pull_fares_range

import pickle

from dateutil.parser import parse

import numpy as np

from promos.models import Promo

from django.template.defaultfilters import striptags

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

    cust = get_object_or_404(Customer, key=slug)
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

    plat = get_object_or_404(Platform, key=slug)
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

    try:
        if inputs and method == 'post':
            cust = Customer.objects.get(key=slug)
            for key, value in inputs.items():
                #cust.first_name = key
                if key in ("email", "phone", "first_name", "last_name"):
                    setattr(cust, key, value)
                    
                    try:
                        setattr(cust, key, value)
                    except:
                        pass
                    
            cust.save()
            cust.update_highrise(inputs)

            cust = Customer.objects.get(key=slug)
            cust_dict = cust.__dict__
            cust_dict['update'] = True
        else:
            cust = Customer.objects.get(key=slug)
            cust_dict = cust.__dict__
            cust_dict['update'] = False


        del cust_dict['_state']
        del cust_dict['platform_id']
        del cust_dict['reg_date']
        del cust_dict['key']
        del cust_dict['id']
        del cust_dict['billdotcom_id']
        del cust_dict['highrise_id']


        if 'csrfmiddlewaretoken' in cust_dict:
            del cust_dict['csrfmiddlewaretoken']
        if 'Search' in cust_dict:
            del cust_dict['Search']

        cust_dict['success'] = True

        build = {'results': cust_dict}
    except (Searches.DoesNotExist):
        build = {'results': {'success': False, 'error': 'Slug provided does not correspond to existing customer.'}}
    except Exception as err:
        build = {'results': {'success': False, 'error': '%s' % (err)}}


    if request.user.is_authenticated():
        clean = False
        #if 'update' in build['results']:
        #    del build['results']['update']
    else:
        clean = True


    return gen_search_display(request, build, clean)
    #return HttpResponse(json.encode(cust_dict), mimetype="application/json")

def find_open_contracts(request, slug):

    if not request.user.is_authenticated():
        cred = check_creds(request.GET, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")



    cust = get_object_or_404(Customer, key=slug)
    contracts = Contract.objects.filter(customer__id=cust.id).order_by('search__exp_date')

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
                new_cust.create_highrise_account()

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

            find_search = Searches.objects.get(key=cd['search_key'])
            find_platform = Platform.objects.get(key=cd['platform_key'])

            # either find the existing customer associated with the platform and email address or create it
            try:
                find_cust = Customer.objects.get(email=cd['email'], platform=find_platform)
                """
                find_cust.first_name =cd['billing_first_name']
                find_cust.last_name = cd['billing_last_name']
                find_cust.save()
                """
            except:
                inps = {}
                inps['key'] = gen_alphanum_key()
                inps['reg_date'] = current_time_aware().date()
                inps['platform'] = find_platform
                inps['email'] = cd['email']
                inps['first_name'] = cd['billing_first_name']
                inps['last_name'] = cd['billing_last_name']
                find_cust = Customer(**inps)
                find_cust.save()
                find_cust.create_highrise_account()


            # limit the number of simulataneously outstanding contracts to 10 per customer
            if find_cust.count_outstanding_contracts() >= 10:
               raise Exception("The customer has reached the limit of 10 outstanding contracts. This cusomer cannot currently make additional purchases.")  
            
            # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
            # or the purchase occured after too much time had passed, and the quoted price is deemed expired
            purch_date_time = current_time_aware()
            search_date_date = find_search.search_date
            expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 60) else False
            if expired:
               raise Exception("The quoted price is expired. Please run a new search.") 
            
            try:
                existing = Contract.objects.get(search__key=cd['search_key'])
            except:
                pass
            else:
                raise Exception("A contract realted to this search has already been purchased. Please run a new search.")


            if find_search.error or not find_search.get_status():
                raise Exception("Cannot purchase contract on invalid search. Please run a new search.")

            # check promo code if given
            if cd['promo']:
                promo = Promo.objects.get(customer=find_cust, code=cd['promo'])
                if promo.contract:
                   raise Exception("Promotional code already used.")
            else:
                promo = None

        except (Searches.DoesNotExist):
            build['error_message'] = 'The search id entered is not valid.'
            build['results'] = {'success': False, 'error': 'The search id entered is not valid.'}
        except (Promo.DoesNotExist):
            build['error_message'] = 'Not a valid promotional code.'
            build['results'] = {'success': False, 'error': 'Not a valid promotional code.'}
        except (Exception) as err:
            build['error_message'] = '%s' % err
            build['results'] = {'success': False, 'error': '%s' % err}
        
        else:

            # update customer data
            setattr(find_cust, 'phone', cd['billing_phone'])
            find_cust.save()

            # run credit card
            amount = find_search.holding_price
            if promo:
                amount = amount - abs(promo.value) if amount > abs(promo.value) else 1

            # can we include middle name here?
            card_info = {'first_name': cd['billing_first_name'], 'last_name': cd['billing_last_name'], 'number': cd['card_number'], 'month': cd['card_month'], 'year': cd['card_year'], 'code': cd['card_code']}
            cust_info = {'email': find_cust.email, 'cust_id': find_cust.key}
            address = {'first_name': cd['billing_first_name'], 'last_name': cd['billing_last_name'], 'phone': cd['billing_phone'], 'address1': cd['billing_address1'], 'address2': cd['billing_address2'], 'city': cd['billing_city'], 'state_province': cd['billing_province'], 'country': cd['billing_country'], 'postal_code': cd['billing_postal_code'], 'country': cd['billing_country']}
            try:
                for i in (card_info, cust_info, address):
                    for k, v in i.iteritems():
                        if k is not 'address2':
                            if v == "" or v is None:
                                raise Exception("need '%s' - input '%s'" % (k,v))
            except (Exception) as err:
                build['error_message'] = 'Not all of the required customer information is available: %s' % (err)
                build['results'] = {'success': False, 'error': 'Not all of the required customer information is available: %s' % (err)}

            else:

                response = run_authnet_trans(amount, card_info, address=address, cust_info=cust_info)

                if response['success']:

                    find_cust.add_highrise_tag('customer')

                    new_contract = Contract(customer=find_cust, purch_date=purch_date_time, search=find_search, gateway_id=response['trans_id'])

                    # save non-sensitive cc data and billing info
                    new_contract.billing_first_name = cd['billing_first_name']
                    new_contract.billing_middle_name = cd['billing_middle_name']
                    new_contract.billing_last_name = cd['billing_last_name']
                    new_contract.billing_phone = cd['billing_phone']
                    new_contract.billing_address1 = cd['billing_address1']
                    new_contract.billing_address2 = cd['billing_address2']
                    new_contract.billing_city = cd['billing_city']
                    new_contract.billing_province = cd['billing_province']
                    new_contract.billing_postal_code = cd['billing_postal_code']
                    new_contract.billing_country = cd['billing_country']

                    new_contract.cc_last_four = cd['card_number'][-4:]
                    new_contract.cc_exp_month = cd['card_month']
                    new_contract.cc_exp_year = cd['card_year']
                    
                    new_contract.shipping_address1 = cd['shipping_address1']
                    new_contract.shipping_address2 = cd['shipping_address2']
                    new_contract.shipping_city = cd['shipping_city']
                    new_contract.shipping_province = cd['shipping_province']
                    new_contract.shipping_postal_code = cd['shipping_postal_code']
                    new_contract.shipping_country = cd['shipping_country']

                    new_contract.alerts = cd['alerts']

                    new_contract.save()

                    if promo:
                        promo.contract = new_contract
                        promo.save()

                    full_search_info = new_contract.search.__dict__
                    search_info = {}
                    for k, v in full_search_info.iteritems():
                        if v and k not in ('time_to_departure', '_state', 'id', 'open_status', 'key', 'expected_risk', 'search_type'):
                            try:
                                search_info[k] = conv_to_js_date(v)
                            except:
                                search_info[k] = v

                    #confirmation_url = "https://www.google.com/" # '%s/platform/%s/customer/%s' % (socket.gethostname(), find_org.key, find_cust.key)
                    build['results'] = {'success': True, 
                                        'search_key': cd['search_key'], 
                                        'cust_key': find_cust.key, 
                                        'purchase_date': purch_date_time.strftime('%Y-%m-%d'), 
                                        #'confirmation': confirmation_url, 
                                        'gateway_status': response['status'], 
                                        'search_info': search_info, 
                                        'receive_alerts': cd['alerts'],
                                        'amount_charged': amount,}

                    """
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
                    """
                    # send confirmation email on success
                    #if MODE == 'live':
                    if 3>1:
                        try:
                            subject = "You've successfully purchased your Level Skies Flex Fare"
                            title = "Congrats on locking in your airfare. That was a good move."
                            if (find_search.depart_date2 - find_search.depart_date1).days > 0:
                                dep = "between %s and %s" % (find_search.depart_date1.strftime("%B %d, %Y"), find_search.depart_date2.strftime("%B %d, %Y"))
                            else:
                                dep = "on %s" % (find_search.depart_date1.strftime("%B %d, %Y"))

                            if (find_search.return_date2 - find_search.return_date1).days > 0:
                                ret = "between %s and %s" % (find_search.return_date1.strftime("%B %d, %Y"), find_search.return_date2.strftime("%B %d, %Y"))
                            else:
                                ret = "on %s" % (find_search.return_date1.strftime("%B %d, %Y"))

                            body = """You have locked in today's low airfare of $%s. You now have until %s to use your Flex Fare when you book a flight from %s to %s, leaving %s and returning %s.\n\nWhen you book your flight just forward the itinerary or confirmation email to sales@levelskies.com and we'll send you your payout if prices on the lowest fares have increased.\n\nThe Level Skies Team""" % (int(find_search.locked_fare), find_search.exp_date.strftime("%B %d, %Y"), find_search.origin_code, find_search.destination_code, dep, ret)

                            send_template_email(new_contract.customer.email, subject, title, body)
                            
                        except:
                            pass

                else:
                    form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([response['status']])
                    #build['error_message'] = response['status']
                    build['results'] = {'success': False, 'error': response['status']}
    else:
        
        err_string = ""
        for error in form.errors.iteritems():
            err_string += "%s - %s " % (error[0], unicode(striptags(error[1]) if striptags else error[1]))

        build['results'] = {'success': False, 'error': err_string}


    return gen_search_display(request, build, clean, method='post')


def demo_option(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.POST if request.POST else None
    if clean:
        cred = check_creds(request.POST, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")


    form = DemoOptionForm(inputs)
    build = {'form': form, 'cust_title': "Purchase option"}

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:

            find_search = Searches.objects.get(key=cd['search_key'])
            find_platform = Platform.objects.get(key=cd['platform_key'])

            
            # either find the existing customer associated with the platform and email addres or create it
            try:
                find_cust = Customer.objects.get(email=cd['email'], platform=find_platform)
                # update customer data
                for i in ('first_name', 'last_name'):
                    try:
                        setattr(find_cust, i, cd[i])
                    except:
                        pass
            except:
                inps = {}
                inps['key'] = gen_alphanum_key()
                inps['reg_date'] = current_time_aware().date()
                inps['platform'] = find_platform
                inps['email'] = cd['email']
                
                for i in ('first_name', 'last_name'):
                    if cd[i]:
                        inps[i] = cd[i]

                find_cust = Customer(**inps)
                find_cust.save()
                find_cust.create_highrise_account()
                if not find_cust.highrise_id:
                    raise Exception("didn't connect to highrise")
            
            # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
            # or the purchase occured after too much time had passed, and the quoted price is deemed expired
            #purch_date_time = current_time_aware()
            purch_date_time = current_time_aware()
            search_date_date = find_search.search_date
            expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 60) else False

            try:
                existing = Demo.objects.get(search__key=cd['search_key'])
            except:
                pass
            else:
                raise Exception('The related demo contract has already been assigned. Please run a new search.')

            if find_search.error or not find_search.get_status() or expired:
                raise Exception('The quoted price has expired or there was an error with the search. Please run a new search.')

        
        except (Searches.DoesNotExist):
            build['error_message'] = 'The option id entered is not valid.'
            build['results'] = {'success': False, 'error': 'The option id entered is not valid.'}
        except Exception as err:
            build['error_message'] = "%s" % (err)
            build['results'] = {'success': False, 'error': "%s" % (err)}
        else:

            find_cust.add_highrise_tag('demo')

            new_demo = Demo(customer=find_cust, purch_date=purch_date_time, search=find_search, alerts=cd['alerts'])
            new_demo.save()

            build['results'] = {'name': str(find_cust), 'success': True, 'search_key': cd['search_key'], 'cust_key': find_cust.key, 'purchase_date': purch_date_time.strftime('%Y-%m-%d'), 'receive_alerts': cd['alerts']}

            # send confirmation email on success                
            try:
                subject = "Thanks for trying out the Level Skies Flex Fare"
                title = "Here's what you need to know about how the Flex Fare works."
                if (find_search.depart_date2 - find_search.depart_date1).days > 0:
                    dep = "between %s and %s" % (find_search.depart_date1.strftime("%B %d, %Y"), find_search.depart_date2.strftime("%B %d, %Y"))
                else:
                    dep = "on %s" % (find_search.depart_date1.strftime("%B %d, %Y"))

                if (find_search.return_date2 - find_search.return_date1).days > 0:
                    ret = "between %s and %s" % (find_search.return_date1.strftime("%B %d, %Y"), find_search.return_date2.strftime("%B %d, %Y"))
                else:
                    ret = "on %s" % (find_search.return_date1.strftime("%B %d, %Y"))

                body = """Had this been a live Flex Fare, you would now have until %s to book a flight from %s to %s, leaving %s and returning %s.\n\nIn this case your protected fare would be $%s. If the lowest fares increase above this amount by the time you book your flight, we would pay you the difference. We will send you an email when this Flex Fare would have expired to let you know just how much you could have saved with us.\n\nThe Level Skies Team""" % (find_search.exp_date.strftime("%B %d, %Y"), find_search.origin_code, find_search.destination_code, dep, ret, int(find_search.locked_fare))

                send_template_email(new_demo.customer.email, subject, title, body)
                    
            except:
                pass

    else:
        err_string = ""
        for error in form.errors.iteritems():
            err_string += "%s - %s " % (error[0], unicode(striptags(error[1]) if striptags else error[1]))

        build['results'] = {'success': False, 'error': err_string}
        

    return gen_search_display(request, build, clean, method='post')






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

    try:
        
        find_contract = get_object_or_404(Contract, search__key=slug)

        staged_items = Staging.objects.filter(contract=find_contract)
        
        if staged_items.exists():
            raise Exception('This contract is currently staged')
        else:

            if action == 'exercise':
                exercise = True
            elif action == 'refund':
                exercise = False
            else:
                raise Http404

            if find_contract.ex_date or find_contract.close_staged_date:
                raise Exception('This contract has already been closed')
                #return HttpResponse(json.encode({'success': False, 'error': 'Contract expired or already closed.'}), mimetype="application/json")

            inputs = request.POST if request.POST else None
            form = AddToStagingForm(inputs)

            staged_cont = Staging(contract=find_contract, exercise=exercise)

            if clean and exercise:
                if not form.is_valid():
                    # dont add contract to staging if form is invalid unless done from api interface
                    err_string = ""
                    for error in form.errors.iteritems():
                        err_string += unicode(striptags(error[1]) if striptags else error[1])
                    raise Exception(err_string)
                    
                else:
                    cd = form.cleaned_data
                    if (find_contract.search.depart_date1 > cd['dep_date']) or (cd['dep_date'] > find_contract.search.depart_date2) or (find_contract.search.return_date1 > cd['ret_date']) or (cd['ret_date'] > find_contract.search.return_date2):
                        raise Exception('Selected travel dates not within locked fare range')

                    for key, value in cd.items():
                        try:
                            setattr(staged_cont, key, value)
                        except:
                            pass

            staged_cont.save()

            find_contract.ex_date = current_time_aware()
            find_contract.save()

            if clean:
                return HttpResponse(json.encode({'success': True}), mimetype="application/json")
            else:
                return HttpResponseRedirect(reverse('staged_item', kwargs={'slug': slug}))

    except (Contract.DoesNotExist):
        return HttpResponse(json.encode({'success': False, 'error': 'Contract key is invalid.'}), mimetype="application/json")
    except Exception as err:
        return HttpResponse(json.encode({'success': False, 'error': '%s' % (err)}), mimetype="application/json")

def staged_item(request, slug):

    find_contract = get_object_or_404(Contract, search__key=slug)
    find_stage = get_object_or_404(Staging, contract=find_contract)

    inputs = request.POST if request.POST else None

    build = {}
    build['detail'] = find_stage

    try:
        find_promo = Promo.objects.get(contract=find_contract)
        build['promo'] = find_promo.value
    except:
        build['promo'] = None

    try:
        formatted_flight_choice = ast.literal_eval(build['detail'].flight_choice)
        for index, i in enumerate(formatted_flight_choice):
            d = json.decode(i)
            formatted_flight_choice[index] = d
        build['detail'].flight_choice = formatted_flight_choice 
    except: 
        pass

        
    if find_stage.exercise:

        current_time = current_time_aware()
        current_date = datetime.datetime(current_time.year, current_time.month, current_time.day,0,0)

        
        build['fares'] = []
        # sets the search date to the expiration date or before
        if find_contract.expired():
            ref_date = find_contract.search.exp_date
        else:
            ref_date = current_date

        for i in ((ref_date-datetime.timedelta(days=1)), ref_date): 
            fares = pull_fares_range(find_contract.search.origin_code, find_contract.search.destination_code, (find_contract.search.depart_date1, find_contract.search.depart_date2), (find_contract.search.return_date1, find_contract.search.return_date2), find_contract.search.depart_times, find_contract.search.return_times, find_contract.search.convenience, find_contract.search.airlines, cached=True, search_date=i)
            if fares['success']:
                build['fares'].append({str(i): fares['fares']})

        #return HttpResponse(json.encode(build['fares']), mimetype="application/json")
        
        if inputs:
            form = ExerStagingForm(inputs)
        else:
            data = {'dep_date': find_stage.dep_date,
                    'ret_date': find_stage.ret_date,
                    'traveler_first_name': find_stage.traveler_first_name,
                    'traveler_middle_name': find_stage.traveler_middle_name,
                    'traveler_last_name': find_stage.traveler_last_name,
                    'traveler_infant': find_stage.traveler_infant,
                    'traveler_gender': find_stage.traveler_gender,
                    'traveler_birth_date': find_stage.traveler_birth_date,
                    'traveler_passport_country': find_stage.traveler_passport_country,
                    'traveler_seat_pref': find_stage.traveler_seat_pref,
                    'traveler_rewards_program': find_stage.traveler_rewards_program,
                    'traveler_contact_email': find_stage.traveler_contact_email,
                    }
            form = ExerStagingForm(initial=data)

    else:
        form = RefundStagingForm(inputs)
        if form.is_valid():
            cd = form.cleaned_data

    build['form'] = form


    if inputs:

        # remove contract
        if 'remove' in inputs:
            find_contract.ex_date = None
            find_contract.save()
            find_stage.delete()
            return HttpResponseRedirect(reverse('staging_view'))

        # exercise the contract
        elif find_stage.exercise:
            if form.is_valid():
                cd = form.cleaned_data
                if (find_contract.search.depart_date1 > cd['dep_date']) or (cd['dep_date'] > find_contract.search.depart_date2) or (find_contract.search.return_date1 > cd['ret_date']) or (cd['ret_date'] > find_contract.search.return_date2):
                    build['error_message'] = 'Selected travel dates not within locked fare range'
                else:
                    
                    inc = cd['fare'] - find_contract.search.locked_fare
                    payout =  inc if inc > 0 else None

                    if 'force_close' in inputs:
                        response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd, use_gateway=False)
                    else:       
                        response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd, payout=payout)

                    if not response['success']:
                        build['error_message'] = response['error']
                    else:
                        find_stage.delete()

                        # send customer email alerting them of payout or not
                        try:   
                            
                            if payout:
                                subject = "Here comes your payout!"
                                title = "Here comes your payout!"
                                body = "We've been tracking fares on flights from %s to %s for you and saw that since you locked in your fare with Level Skies the lowest airfare increased by $%s. That's exactly the amount we are sending you right now. Expect a check in the mail in roughly a week's time.\n\nThe Level Skies Team" % (find_contract.search.origin_code, find_contract.search.destination_code, int(payout))
                            else:

                                # create promotion for customer who received no payout
                                new_promo = Promo(customer=find_contract.customer, 
                                                created_date=current_time,
                                                value=5,
                                                code=gen_alphanum_key())
                                new_promo.save()

                                subject = 'We recieved your ticket confirmation'
                                title = "Thanks for using Level Skies!"
                                body = "We've been tracking fares on flights from %s to %s for you since you locked in your fare with us. As of today, the lowest airfare for the route and the dates you'll be traveling on hasn't increased beyond the fare you locked in. This time around there's no payout for us to send you but we don't want you to leave empty-handed. Here's a promo code you can use for $%s off your next Flex Fare:\n\n%s\n\nWe hope you enjoyed the peace of mind while you waited to book your ticket.\n\nThe Level Skies Team" % (find_contract.search.origin_code, find_contract.search.destination_code, new_promo.value, new_promo.code)  
                            send_template_email(find_contract.customer.email, subject, title, body)
                            
                        except:
                            pass


                        return HttpResponseRedirect(reverse('staging_view'))
            else:
                build['error_message'] = "Form not valid"

        # refund the contract
        else:
            
            if 'force_close' in inputs:
                #response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, notes=cd['notes'], use_gateway=False)
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd, use_gateway=False)
            else:
                # response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, notes=cd['notes'])
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd, promo=build['promo'])
            
            
            if not response['success']:
                build['error_message'] = response['error']
                #build['error_message'] = "Status: %s" % (response)
            else:
                
                #build['error_message'] = "Status: %s" % (response)
                
                
                find_stage.delete()
                find_contract.refunded = True
                find_contract.save()

                # send customer email of refund value
                try:

                    amount = find_contract.search.holding_price    
                    if build['promo']:
                        if amount > build['promo']:
                            amount = amount - build['promo']
                        else:
                            amount = 1
                     
                    subject = 'We processed your refund'
                    title = "Thanks for using Level Skies!"
                    body = "We just canceled your locked fare and refunded your purchase price of $%s. You should receive the refund within two or three business days. We hope to see you again.\n\nThe Level Skies Team" % (int(amount))
                    send_template_email(find_contract.customer.email, subject, title, body)
                    
                except:
                    pass

                return HttpResponseRedirect(reverse('staging_view'))
                

    return render_to_response('sales/staging.html', build, context_instance=RequestContext(request))


def staging_sweep(request):
    results = {'success': False, 'error': 'This method is no longer required.'}
    return gen_search_display(request, {'results': results}, True, method='post')
    """
    cont_list = []
    full_set = Contract.objects.filter(ex_date=None)

    for i in full_set:
        if not i.outstanding() and not i.staged():
            staged_cont = Staging(contract=i, exercise=False, notes="Forced staging upon expiration")
            staged_cont.save()
            i.ex_date = current_time_aware()
            i.save()
            cont_list.append(i)

    if not cont_list:
        message = "No contracts to stage"
    else:
        message = "Staged %s contracts" % (len(cont_list))

        if MODE == 'live':    
            try:
                send_mail('Staging sweep',
                    message,
                    'sysadmin@levelskies.com',
                    ['sales@levelskies.com'],
                    fail_silently=False)
            except:
                pass

    return render_to_response('sales/sweep.html', {'items': cont_list, 'message': message}, context_instance=RequestContext(request))
    """

def alerts(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if clean:
        cred = check_creds(request.POST, Platform)
        if not cred['success']:
            return HttpResponse(json.encode(cred), mimetype="application/json")


    current_time = current_time_aware()

    # ensure this query is not run more than once/24hrs
    run_dates = AlertsCheck.objects

    if not run_dates.exists() or (current_time - run_dates.latest('run_date').run_date) >= datetime.timedelta(hours=23):
        latest_price_check = AlertsCheck(run_date=current_time)
        latest_price_check.save()


        # delete old alerts
        Alerts.objects.filter(search__exp_date__lte=current_time).delete()

        contracts = Contract.objects.filter(alerts=True, search__exp_date__gt=(current_time + datetime.timedelta(hours=18)), search__search_date__lt=(current_time - datetime.timedelta(hours=18)), ex_date=None) 
        demos = Demo.objects.filter(alerts=True, search__exp_date__gt=(current_time + datetime.timedelta(hours=18)), search__search_date__lt=(current_time - datetime.timedelta(hours=18))) 
        

        alerted_searches = []
        for i in (contracts, demos):
            for k in i:
                
                obj, created = Alerts.objects.get_or_create(search=k.search)
                
                prev_fares = ast.literal_eval(obj.fares) if obj.fares else []
                prev_update = obj.update_date if obj.update_date else None

                # ensure not sent more than once daily
                if not prev_update or prev_update < current_time:
                    
                    temp = {'key': k.search.key}

                    # check updated flights
                    flights = pull_fares_range(k.search.origin_code, k.search.destination_code, (k.search.depart_date1, k.search.depart_date2), (k.search.return_date1, k.search.return_date2), k.search.depart_times, k.search.return_times, k.search.convenience, k.search.airlines, cached=True)

                    if flights['success']:
                        # delete unneccessary data
                        for f in flights['fares']:
                            del f['flight']
                        
                        fares = flights['fares']
                    else:
                        fares = None
                      
                    #obj.fares = str(pickle.dumps(fares)) if fares else None
                    obj.fares = str(fares) if fares else None
                    obj.update_date = current_time
                    obj.save()

                     
                    # line up previously checked fares with current
                    rows = []
                    any_changes = False
                    for fare in fares:
                        change = ""
                        if prev_fares:  
                            for p in prev_fares:
                                if p['depart_date'] == fare['depart_date'] and p['return_date'] == fare['return_date']:
                                    if fare['fare'] and p['fare']:
                                        # record change if greater than 10
                                        change = str(int(fare['fare']-p['fare'])) if abs(fare['fare']-p['fare']) > 10 else ""
                                        if change:
                                            any_changes = True
                                    prev_fares.remove(p)
                        
                        if fare['fare']:      
                            rows.append([fare['depart_date'], fare['return_date'], "$%s" % int(fare['fare']), change])


                    # send email 
                    subject = "Your Level Skies fare update"
                    title = "Here's what's new with the fare%s we're tracking" % ('s' if len(rows)>1 else '')
                    body = "We've been watching those fares for you, just like you asked. Below you'll see today's lowest fares for the dates you selected. We'll also let you know if anything has changed much since we last wrote you."
                    
                    if rows:
                        try:
                            if len(rows) > 1:
                                # sort by dates
                                rows = np.array(rows)
                                ind = np.lexsort((rows[:,0],rows[:,1]))
                                rows = rows[ind]
                                rows = rows.tolist()

                            if any_changes:
                                col = "Change since %s" % (prev_update.strftime("%b %d"))
                            else:
                                col = ""
                            table_dat = [["Depart Date","Return Date","Today's Low Fare",col],] + rows
                            
                            table = "<table>"
                            for r in table_dat:
                                table += "<tr>"
                                for d in r:
                                    table += "<td>%s</td>" % (d)
                                table += "</tr>"
                            table +="</table>"
                        
                            send_template_email(k.customer.email, subject, title, body, table)    
                            #return render_to_response('email_template/index.html', {'title': title, 'body': body, 'table': table}) 
                            temp['sent'] = True            
                        except:
                            temp['sent'] = False
                    else:
                        temp['sent'] = False

                    alerted_searches.append(temp)
        

        results = {'success': True, 'valid_alert_searches': alerted_searches}

    else:
        results = {'success': False, 'error': 'Alerts sent within last 24 hours.'}


    return gen_search_display(request, {'results': results}, clean)

