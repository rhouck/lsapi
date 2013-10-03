from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
import datetime
import socket
import json

from api.views import current_time_aware, conv_to_js_date, gen_alphanum_key, gen_search_display
from sales.models import *
from forms import *

from analysis.models import Cash_reserve, Additional_capacity
from pricing.models import Search_history
from api.views import gen_search_display

from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
from django.views.generic import DetailView, ListView

from quix.pay.gateway.authorizenet import AimGateway
from quix.pay.transaction import CreditCard, Address, Customer as AuthCustomer

from api.utils import *

def run_authnet_trans(amt, card_info, cust_info=None, address=None, trans_id=None):

    gateway = AimGateway('3r34zx5KELcc', '29wm596EuWHG72PB')
    gateway.use_test_mode = True
    # gateway.use_test_url = True
    # use gateway.authorize() for an "authorize only" transaction

    # number, month, year, first_name, last_name, code
    card = CreditCard(**card_info)
    if not trans_id:
        if cust_info:
            address = Address(**address)
            customer = AuthCustomer(**cust_info)
            customer.billing_address = address
            customer.shipping_address = address
            response = gateway.sale(str(amt), card, customer=customer)
        else:
            response = gateway.sale(str(amt), card)
    else:
        response = gateway.credit(str(trans_id), str(amt), card)

    if response.status == response.APPROVED:
        # this is where you store data from the response object into
        # your models. The response.trans_id would be used to capture,
        # void, or credit the sale later.

        success = True
        status = "Authorize Request: %s</br>Transaction %s = %s: %s" % (gateway.get_last_request().url,response.trans_id,
                                           response.status_strings[response.status],
                                           response.message)
    else:
        success = False
        status = "%s - %s" % (response.status_strings[response.status],
            response.message)
        #form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([status])
    return {'success': success, 'status': status, 'trans_id': response.trans_id}


def test_trans(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    if request.GET:
        form = PaymentForm(request.GET)
        if form.is_valid():
            cd = form.cleaned_data
            #return HttpResponse(cd)
            card = {}
            for i in ('first_name', 'last_name', 'number','month','year','code'):
                card[i] = cd[i]

            address = {}
            for i in ('first_name', 'last_name', 'phone', 'address1', 'city', 'state_province', 'country', 'postal_code'):
                address[i] = cd[i]

            cust_info = {}
            for i in ('email',):
                cust_info[i] = cd[i]

            response = run_authnet_trans(123, card, address=address, cust_info=cust_info)

            if response['success']:
                return HttpResponse(response['status'])
            else:

                form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([response['status']])
                return gen_search_display(request, {'form': form}, clean)
    else:
        form = PaymentForm()
        build = {'form': form}
    return gen_search_display(request, build, clean)





class CustomerList(ListView):
    model = Customer
    context_object_name = "items"
    template_name='sales/list.html'
    paginate_by = 100

class PlatformList(ListView):
    model = Platform
    context_object_name = "items"
    template_name='sales/list.html'
    paginate_by = 100

class CustomerDetail(DetailView):
    context_object_name = "detail"
    template_name='sales/detail.html'
    def get_object(self):
        return get_object_or_404(Customer, key__iexact=self.kwargs['slug'])

class PlatformDetail(DetailView):
    context_object_name = "detail"
    template_name='sales/detail.html'
    def get_object(self):
        return get_object_or_404(Platform, key__iexact=self.kwargs['slug'])

class PlatSpecCustDetail(DetailView):
    context_object_name = "detail"
    template_name='sales/detail.html'
    def get_object(self):
        return get_object_or_404(Customer, key__iexact=self.kwargs['slug'])



def customer_info(request, slug):

    inputs = request.GET if request.GET else None

    if not request.user.is_authenticated():
        platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])

    request.GET = None

    if inputs:
        try:
            del inputs['platform_key']
        except:
            pass

        #cust = get_object_or_404(Customer, key__iexact=slug, password__iexact=inputs['password'])
        cust = get_object_or_404(Customer, key__iexact=slug)
        for key, value in inputs.items():
            setattr(cust, key, value)
        cust.save()
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

    try:
        del cust_dict['csrfmiddlewaretoken']
        del cust_dict['Search']
    except:
        pass

    return HttpResponse(json.dumps(cust_dict), mimetype="application/json")




def find_open_contracts(request, slug):

    if not request.user.is_authenticated():
        platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])


    cust = get_object_or_404(Customer, key__iexact=slug)
    contracts = Contract.objects.filter(customer__id__iexact=cust.id)

    bank = {}
    for index, i in enumerate(contracts):
        if i.outstanding():
            bank[index] = {}
            bank[index]['redeem'] = "link to purchase"
            bank[index]['refund'] = "link to refund"
            bank[index]['desc'] =  {
                                    'key': i.search.key,
                                    #'platform': i.platform.org_name,
                                    'origin_code': i.search.origin_code,
                                    'destination_code': i.search.destination_code,
                                    'exp_date': conv_to_js_date(i.search.exp_date),
                                    'purch_date': conv_to_js_date(i.purch_date),
                                    'depart_times': i.search.depart_times,
                                    'return_times': i.search.return_times,
                                    'convenience': i.search.nonstop,
                                    'deposit': i.search.locked_fare + i.search.holding_price,
                                    'refund_value': i.search.locked_fare,
                                    'depart_date_1': conv_to_js_date(i.search.depart_date1),
                                    'return_date_1': conv_to_js_date(i.search.return_date1),
                                    'depart_date_2': conv_to_js_date(i.search.depart_date2),
                                    'return_date_2': conv_to_js_date(i.search.return_date2),
                                    }

    return gen_search_display(request, {'results': bank}, True)


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
            #find_cust = Customer.objects.get(email=cd['email'], platform=cd['password'])
            build['results'] = {'success': True, 'key': find_cust.key}
        except:
            build['error_message'] = 'The customer is not registered in the system.'
            build['results'] = {'success': False, 'message': 'The customer is not registered in the system.'}
    return gen_search_display(request, build, clean)



def customer_login(request):
    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.GET if request.GET else None
    form = Customer_login(inputs)
    build = {'form': form, 'cust_title': "Customer Login"}
    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:
            find_org = Platform.objects.get(key=cd['platform_key'])
            find_cust = Customer.objects.get(email=cd['email'], platform=find_org)
            #find_cust = Customer.objects.get(email=cd['email'], password=cd['password'], platform_key=cd['platform_key'])
            if clean:
                return HttpResponseRedirect(reverse('open_contracts', kwargs={'slug': find_cust.key}))
            else:
                return HttpResponseRedirect(reverse('customer_detail', kwargs={'slug': find_cust.key}))
        except:
            build['error_message'] = 'The customer is not registered in the system.'
            build['results'] = {'error': 'The customer is not registered in the system.'}
    return gen_search_display(request, build, clean)


def customer_signup(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.GET if request.GET else None
    if clean:
        platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])


    form = Customer_signup(inputs)
    build = {'form': form, 'cust_title': "Customer Signup"}
    if (inputs) and form.is_valid():
        cd = form.cleaned_data

        try:
            find_org = Platform.objects.get(key=cd['platform_key'])
        except (Platform.DoesNotExist):
            build['error_message'] = 'The platform name is not valid.'
            build['results'] = {'success': False, 'message': 'The platform name is not valid.'}
        else:
            try:
                find_cust = Customer.objects.get(email=cd['email'], platform=find_org)
                message = 'The email address is already registered in the system with this platform.'
                build['error_message'] = message
                build['results'] = {'success': False, 'message': message} # , 'key': find_cust.key
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

    return gen_search_display(request, build, clean)


def purchase_option(request):

    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.GET if request.GET else None
    if clean:
        platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])


    form = Purchase_option(inputs)
    build = {'form': form, 'cust_title': "Purchase option"}

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:

            #find_org = Platform.objects.get(key=cd['platform_key'])
            find_search = Search_history.objects.get(key=cd['search_key'])
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
        except (Search_history.DoesNotExist):
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

                    # save non-sensitive cc data
                    find_cust.cc_last_four = cd['number'][-4:]
                    find_cust.cc_exp_month = cd['month']
                    find_cust.cc_exp_year = cd['year']
                    find_cust.save()

                    #new_contract = Contract(platform=find_org, customer=find_cust, purch_date=purch_date_time, search=find_search)
                    new_contract = Contract(customer=find_cust, purch_date=purch_date_time, search=find_search, gateway_id=response['trans_id'])
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

    return gen_search_display(request, build, clean, method='get')


@login_required()
def exercise_option(request):

    # find a way to calculate exericse fare
    """
    if request.user.is_authenticated():
        clean = False
    else:
        clean = True
    """
    clean = True

    inputs = request.GET if request.GET else None
    """
    if clean:
        platform = get_object_or_404(Platform, key__iexact=request.GET['platform_key'])
    """

    form = Exercise_option(inputs)
    build = {'form': form}

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:

            find_cust = Customer.objects.get(key__iexact=cd['cust_key'])
            find_contract = Contract.objects.get(customer=find_cust, search__key=cd['search_key'])

        except (KeyError, Customer.DoesNotExist, Contract.DoesNotExist):
            build['error_message'] = 'The user id and/or transaction id is not valid.'
            build['results'] = {'success': False, 'error': 'The user id and/or transaction id is not valid.'}

        else:
            if not find_contract.outstanding():
                build['error_message'] = 'The contract selected is either expired or already exercised.'
                build['results'] = {'success': False, 'error': 'The contract selected is either expired or already exercised.'}

            else:
                if cd['exercise']:
                    # if option is converted into airline ticket
                    current_fare = 500
                    find_contract.ex_fare = current_fare
                else:
                    # if option is refunded
                    #card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': cd['number'], 'month': cd['month'], 'year': cd['year'], 'code': cd['code']}
                    card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': find_cust.cc_last_four, 'month': find_cust.cc_exp_month, 'year': find_cust.cc_exp_month}
                    response = run_authnet_trans(find_contract.search.locked_fare, card_info, trans_id=find_contract.gateway_id)
                    if not response['success']:
                        form._errors[forms.forms.NON_FIELD_ERRORS] = form.error_class([response['status']])
                        #build['error_message'] = response['status']
                        build['results'] = {'success': False, 'error': response['status']}
                        return gen_search_display(request, build, clean)

                    find_contract.ex_fare = None

                exercise_date_time = current_time_aware()
                find_contract.ex_date = exercise_date_time
                find_contract.save()
                build['results'] = {'success': True, 'search_key': cd['search_key'], 'cust_key': cd['cust_key'], 'exercise_fare': find_contract.ex_fare, 'exercise_date': exercise_date_time.strftime('%Y-%m-%d')}
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
    #else:
    #    build['error_message'] = 'Inputs not valid.'
    #    build['results'] = {'success': False, 'error': 'Inputs not valid.'}

    return gen_search_display(request, build, clean)



# staging views

@login_required()
def add_to_staging(request, action, slug):

    find_contract = get_object_or_404(Contract, search__key__iexact=slug)

    try:
        find_stage = Staging.objects.get(contract=find_contract)
        return HttpResponse("already staged")
    except (Staging.DoesNotExist):
        exercise = True if action == 'exercise' else False
        staged_cont = Staging(contract=find_contract, exercise=exercise)
        staged_cont.save()
        return HttpResponseRedirect(reverse('staged_item', kwargs={'slug': slug}))



class StagingList(ListView):
    model = Staging
    context_object_name = "items"
    template_name='sales/staging_list.html'
    paginate_by = 100


def staged_item(request, slug):
    find_contract = get_object_or_404(Contract, search__key__iexact=slug)
    find_stage = get_object_or_404(Staging, contract=find_contract)

    inputs = request.POST if request.POST else None
    build = {}
    build['detail'] = find_stage

    if find_stage.exercise:
        form = StagingForm(inputs)
        build['form'] = form

    if inputs:
        api_vars = {'cust_key': find_contract.customer.key, 'search_key': slug}
        if find_stage.exercise:
            if form.is_valid():
                api_vars['exercise'] = True
                cd = form.cleaned_data
                api_vars.update(cd.items())

                info = call_api(api_vars,'/sales/exercise/')
                try:
                    return HttpResponse("%s - %s" % (info['success'], info['error']))
                except:
                    return HttpResponse(info)
            else:
                build['error_message'] = "Form not valid"
        else:
            api_vars['exercise'] = False
    return render_to_response('sales/staging.html', build, context_instance=RequestContext(request))