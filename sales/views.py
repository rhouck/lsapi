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

from sales.utils import exercise_option, send_template_email

from api.settings import MODE

import ast


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
                if key not in ("key", "platform", "reg_date"):
                    try:
                        setattr(cust, key, value)
                    except:
                        pass
            cust.save()
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


        if 'csrfmiddlewaretoken' in cust_dict:
            del cust_dict['csrfmiddlewaretoken']
        if 'Search' in cust_dict:
            del cust_dict['Search']

        cust_dict['success'] = True

        build = {'results': cust_dict}

    except:
        build = {'results': {'success': False, 'error': 'Slug provided does not correspond to existing customer.'}}


    if request.user.is_authenticated():
        clean = False
        if 'update' in build['results']:
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

            find_search = Searches.objects.get(key=cd['search_key'])
            find_platform = Platform.objects.get(key=cd['platform_key'])

            # either find the existing customer associated with the platform and email addres or create it
            try:
                find_cust = Customer.objects.get(email=cd['email'], platform=find_platform)
            except:
                inps = {}
                inps['key'] = gen_alphanum_key()
                inps['reg_date'] = current_time_aware().date()
                inps['platform'] = find_platform
                inps['email'] = cd['email']
                find_cust = Customer(**inps)
                find_cust.save()

            # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
            # or the purchase occured after too much time had passed, and the quoted price is deemed expired
            purch_date_time = current_time_aware()
            search_date_date = find_search.search_date
            expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 60) else False

            try:
                existing = Contract.objects.get(search__key=cd['search_key'])
            except:
                pass
            else:
                raise Exception

            if find_search.error or not find_search.get_status() or expired:
                raise Exception

        #except (Customer.DoesNotExist):
        #    build['error_message'] = 'The customer key is not valid.'
        #    build['results'] = {'success': False, 'error': 'The customer key is not valid.'}
        except (Searches.DoesNotExist):
            build['error_message'] = 'The option id entered is not valid.'
            build['results'] = {'success': False, 'error': 'The option id entered is not valid.'}
        except (Exception):
            build['error_message'] = 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'
            build['results'] = {'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}
        else:

            # update customer data
            """
            for key, value in cd.items():
                if key not in ("key", "platform", "reg_date"):
                    try:
                        setattr(find_cust, key, value)
                    except:
                        pass
            """
            setattr(find_cust, 'phone', cd['billing_phone'])
            find_cust.save()


            # run credit card
            amount = find_search.locked_fare + find_search.holding_price
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
                    new_contract.save()


                    full_search_info = new_contract.search.__dict__
                    search_info = {}
                    for k, v in full_search_info.iteritems():
                        if v and k not in ('time_to_departure', '_state', 'id', 'open_status', 'key', 'expected_risk', 'search_type'):
                            try:
                                search_info[k] = conv_to_js_date(v)
                            except:
                                search_info[k] = v

                    confirmation_url = "https://www.google.com/" # '%s/platform/%s/customer/%s' % (socket.gethostname(), find_org.key, find_cust.key)
                    build['results'] = {'success': True, 'search_key': cd['search_key'], 'cust_key': find_cust.key, 'purchase_date': purch_date_time.strftime('%Y-%m-%d'), 'confirmation': confirmation_url, 'gateway_status': response['status'], 'search_info': search_info}

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

                    # send confirmation email on success
                    #if MODE == 'live':
                    if 3>1:
                        try:
                            subject = "You've successfully made your Level Skies Lock-in"
                            title = "Congrats on locking in your airfare. That was a good move."
                            if (find_search.depart_date2 - find_search.depart_date1).days > 0:
                                dep = "between %s and %s" % (find_search.depart_date1.strftime("%B %d, %Y"), find_search.depart_date2.strftime("%B %d, %Y"))
                            else:
                                dep = "on %s" % (find_search.depart_date1.strftime("%B %d, %Y"))

                            if (find_search.return_date2 - find_search.return_date1).days > 0:
                                ret = "between %s and %s" % (find_search.return_date1.strftime("%B %d, %Y"), find_search.return_date2.strftime("%B %d, %Y"))
                            else:
                                ret = "on %s" % (find_search.return_date1.strftime("%B %d, %Y"))

                            body = """You now have until %s to use your locked fare on a flight from %s to %s, leaving %s and returning %s.\n\nIf you choose not to use your Lock-in, you can request a refund of $%s any time from your profile on levelskies.com. Of course, this refund value will automatically be returned to you upon expiration of the Lock-in if you take no action.\n\nThe Level Skies Team""" % (find_search.exp_date.strftime("%B %d, %Y"), find_search.origin_code, find_search.destination_code, dep, ret, int(find_search.locked_fare))

                            send_template_email(new_contract.customer.email, subject, title, body)
                            """
                            send_mail(subject,
                                message,
                                'sales@levelskies.com',
                                ['%s' % (new_contract.customer.email)],
                                fail_silently=False,
                                auth_user='sales@levelskies.com',
                                auth_password='_second&mission_')
                            """
                        except:
                            pass

                else:
                    form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([response['status']])
                    #build['error_message'] = response['status']
                    build['results'] = {'success': False, 'error': response['status']}
    else:
        build['results'] = {'success': False, 'error': form.errors}

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

    find_contract = get_object_or_404(Contract, search__key=slug)

    try:
        find_stage = Staging.objects.get(contract=find_contract)
        return HttpResponse(json.encode({'success': False, 'error': 'Already staged'}), mimetype="application/json")

    except (Staging.DoesNotExist):

        if action == 'exercise':
            exercise = True
        elif action == 'refund':
            exercise = False
        else:
            raise Http404

        if exercise and not find_contract.outstanding():
            return HttpResponse(json.encode({'success': False, 'error': 'Contract expired or already closed.'}), mimetype="application/json")

        inputs = request.POST if request.POST else None
        form = AddToStagingForm(inputs)

        staged_cont = Staging(contract=find_contract, exercise=exercise)

        if clean and exercise:
            if not form.is_valid():
                # dont add contract to staging if form is invalid unless done from api interface
                return HttpResponse(json.encode({'success': False, 'error': form.errors}), mimetype="application/json")
            else:
                cd = form.cleaned_data
                if (find_contract.search.depart_date1 > cd['dep_date']) or (cd['dep_date'] > find_contract.search.depart_date2) or (find_contract.search.return_date1 > cd['ret_date']) or (cd['ret_date'] > find_contract.search.return_date2):
                    return HttpResponse(json.encode({'success': False, 'error': 'Selected travel dates not within locked fare range'}), mimetype="application/json")
                #staged_cont = Staging(contract=find_contract, exercise=exercise)
                #staged_cont(**cd)
                #staged_cont.save()

                for key, value in cd.items():
                    try:
                        setattr(staged_cont, key, value)
                    except:
                        pass

        staged_cont.save()

        find_contract.ex_date = current_time_aware()
        find_contract.save()



        # sends alert email to sales@levelskies
        if MODE == 'live':
            try:
                send_mail('Just added to staging - %s' % (action),
                    '%s (%s) just elected to %s contract with key: %s.' % (find_contract.customer, find_contract.customer.key, action, find_contract.search.key),
                    'sysadmin@levelskies.com',
                    ['sales@levelskies.com'],
                    fail_silently=False)
            except:
                pass
        # sends confirmation to customer

        #try:
        title = "Thanks again for using Level Skies!"
        if action == 'exercise':
            subject = 'We recieved your ticket request'

            if not (staged_cont.traveler_first_name and staged_cont.traveler_last_name):
                target = "your"
            else:
                target = "%s %s's" % (staged_cont.traveler_first_name, staged_cont.traveler_last_name)
            body = "We are now processing your request and will send you %s ticket from %s to %s within the next 48 hrs.\n\nThe Level Skies Team" % (target, find_contract.search.origin_code, find_contract.search.destination_code)

        else:
            subject = 'Your Level Skies Lock-in is being refunded'
            body = "We are processing your request. You should receive your refund of $%s within two to three business days.\n\nThe Level Skies Team" % (int(find_contract.search.locked_fare))

        send_template_email(find_contract.customer.email, subject, title, body)
        """
        send_mail(subject,
            message,
            'sales@levelskies.com',
            ['%s' % (find_contract.customer.email)],
            fail_silently=False,
            auth_user='sales@levelskies.com',
            auth_password='_second&mission_')
        """
        #except:
        #    pass

        if clean:
            return HttpResponse(json.encode({'success': True}), mimetype="application/json")
        else:
            return HttpResponseRedirect(reverse('staged_item', kwargs={'slug': slug}))

    except Exception as err:
        return HttpResponse(json.encode({'success': False, 'error': '%s' % (err)}), mimetype="application/json")

def staged_item(request, slug):

    find_contract = get_object_or_404(Contract, search__key=slug)
    find_stage = get_object_or_404(Staging, contract=find_contract)

    inputs = request.POST if request.POST else None

    build = {}
    build['detail'] = find_stage

    try:
        formatted_flight_choice = ast.literal_eval(build['detail'].flight_choice)
        for index, i in enumerate(formatted_flight_choice):
            d = json.decode(i)
            formatted_flight_choice[index] = d
        build['detail'].flight_choice = formatted_flight_choice 
    except: 
        pass

        
    if find_stage.exercise:

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

        """
        if 'remove' in inputs or 'force_close' in inputs:
            find_stage.delete()
            if 'force_close' in inputs:
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, flight_choice=cd['notes'], use_gateway=False)
            return HttpResponseRedirect(reverse('staging_view'))
        """

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
                    if 'force_close' in inputs:
                        #response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=cd['fare'], dep_date=cd['dep_date'], ret_date=cd['ret_date'], flight_purchased=cd['flight_purchased'], notes=cd['notes'], use_gateway=False)
                        response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd, use_gateway=False)
                    else:
                        # response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=cd['fare'], dep_date=cd['dep_date'], ret_date=cd['ret_date'], flight_purchased=cd['flight_purchased'], notes=cd['notes'])
                        response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd)

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
                #response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, notes=cd['notes'], use_gateway=False)
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd, use_gateway=False)
            else:
                # response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, fare=None, dep_date=None, ret_date=None, notes=cd['notes'])
                response = exercise_option(find_contract.customer.key, slug, find_stage.exercise, cd)

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
            i.ex_date = current_time_aware()
            i.save()
            cont_list.append(i)

    if not cont_list:
        message = "No contracts to stage"
    else:
        message = "Staged %s contracts" % (len(cont_list))

    return render_to_response('sales/sweep.html', {'items': cont_list, 'message': message}, context_instance=RequestContext(request))
