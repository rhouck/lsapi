from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
import datetime
import socket

from api.views import current_time_aware, conv_to_js_date, gen_alphanum_key, gen_search_display
from sales.models import *
from forms import *

from analysis.models import Cash_reserve, Search_history, Additional_capacity
from api.views import gen_search_display

from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
from django.views.generic import DetailView, ListView


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


def find_open_contracts(request, slug, slug_2=None):
    cust = get_object_or_404(Customer, key__iexact=slug)
    if slug_2:
        plat = get_object_or_404(Platform, key__iexact=slug_2)
        contracts = Contract.objects.filter(customer__id__iexact=cust.id, platform__id__iexact=plat.id)
    else:
        contracts = Contract.objects.filter(customer__id__iexact=cust.id)

    bank = {}
    for index, i in enumerate(contracts):
        if i.outstanding():
            bank[index] = {}
            bank[index]['redeem'] = "link to purchase"
            bank[index]['refund'] = "link to refund"
            bank[index]['desc'] =  {
                                    'key': i.search.key,
                                    'platform': i.platform.org_name,
                                    'origin_code': i.search.origin_code,
                                    'destination_code': i.search.destination_code,
                                    'exp_date': conv_to_js_date(i.search.exp_date),
                                    'purch_date': conv_to_js_date(i.purch_date),
                                    'depart_times': i.search.depart_times,
                                    'return_times': i.search.return_times,
                                    'nonstop': i.search.nonstop,
                                    'deposit': i.search.locked_fare + i.search.holding_price,
                                    'refund_value': i.search.locked_fare,
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
            find_cust = Customer.objects.get(email=cd['email'], password=cd['password'])
            build['results'] = {'success': True, 'key': find_cust.key}
        except:
            build['error_message'] = 'The customer is not registered in the system.'
            build['results'] = {'success': False, 'error': 'The customer is not registered in the system.'}
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
            find_cust = Customer.objects.get(email=cd['email'])
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
    form = Customer_signup(inputs)
    build = {'form': form, 'cust_title': "Customer Signup"}
    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:
            find_cust = Customer.objects.get(email=cd['email'])
            message = 'The email address is already registered in the system.'
            """
            # updated name information if given
            if cd['first_name'] or cd['last_name']:
                if find_cust.first_name != cd['first_name']:
                    find_cust.first_name = cd['first_name']
                    message += "Updated first name."
                if find_cust.last_name != cd['last_name']:
                    find_cust.last_name = cd['last_name']
                    message += "Updated last name."
                find_cust.save()
            """
            build['error_message'] = message
            build['results'] = {'success': False, 'message': message} # , 'key': find_cust.key
        except:
            cust_key = gen_alphanum_key()
            new_cust = Customer(first_name=cd['first_name'], last_name=cd['last_name'], email=cd['email'], password=cd['password'], phone=cd['phone'], address=cd['address'], city=cd['city'], state_prov=cd['state_prov'], zip_code=cd['zip_code'], country=cd['country'], reg_date=current_time_aware().date(), key=cust_key)
            new_cust.save()
            build['results'] = dict({'success': True}.items() + new_cust.__dict__.items())
            del build['results']['password']
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
    form = Purchase_option(inputs)
    build = {'form': form, 'cust_title': "Purchase option"}

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:
            """
            #if customer email not in system, create account
            try:
                find_cust = Customer.objects.get(email=cd['email'])
                # updated name information if given
                if cd['first_name'] or cd['last_name']:
                    if find_cust.first_name != cd['first_name']:
                        find_cust.first_name = cd['first_name']
                    if find_cust.last_name != cd['last_name']:
                        find_cust.last_name = cd['last_name']
                    find_cust.save()
            except (Customer.DoesNotExist):
                cust_key = gen_alphanum_key()
                find_cust = Customer(first_name=cd['first_name'], last_name=cd['last_name'], email=cd['email'], reg_date=current_time_aware().date(), key=cust_key)
                find_cust.save()
            """

            find_org = Platform.objects.get(key=cd['platform_key'])
            find_search = Search_history.objects.get(key=cd['search_key'])
            find_cust = Customer.objects.get(key=cd['cust_key'])

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

        except (Platform.DoesNotExist):
            build['error_message'] = 'The platform name is not valid.'
            build['results'] = {'success': False, 'error': 'The platform name is not valid.'}
        except (Search_history.DoesNotExist):
            build['error_message'] = 'The option id entered is not valid.'
            build['results'] = {'success': False, 'error': 'The option id entered is not valid.'}
        except (Exception):
            build['error_message'] = 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'
            build['results'] = {'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}
        else:
            new_contract = Contract(platform=find_org, customer=find_cust, purch_date=purch_date_time, search=find_search)
            new_contract.save()
            confirmation_url = "https://www.google.com/" # '%s/platform/%s/customer/%s' % (socket.gethostname(), find_org.key, find_cust.key)
            build['results'] = {'success': True, 'search_key': cd['search_key'], 'customer_key': cd['cust_key'], 'platform_key': cd['platform_key'], 'purchase_date': purch_date_time.strftime('%Y-%m-%d'), 'confirmation': confirmation_url}

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

    return gen_search_display(request, build, clean)


def exercise_option(request):
    if request.user.is_authenticated():
        clean = False
    else:
        clean = True

    inputs = request.GET if request.GET else None
    form = Exercise_option(inputs)
    build = {'form': form, 'cust_title': "Exercise option"}

    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        try:
            find_cust = Customer.objects.get(email=cd['cust_email'], password=cd['cust_password'])
            find_org = Platform.objects.get(org_name=cd['org_name'])
            find_contract = Contract.objects.get(platform=find_org, customer=find_cust, search__key=cd['search_key'])
        except (KeyError, Customer.DoesNotExist, Platform.DoesNotExist, Contract.DoesNotExist):
            build['error_message'] = 'The login/password, platform name, and transaction id combination is not valid.'
            build['results'] = {'success': False, 'error': 'The login/password, platform name, and transaction id combination is not valid.'}

        else:
            if not find_contract.outstanding():
                build['error_message'] = 'The contract selected is either expired or already exercised.'
                build['results'] = {'success': False, 'error': 'The contract selected is either expired or already exercised.'}

            else:
                find_contract.ex_fare = cd['exercise_fare']
                exercise_date_time = current_time_aware()
                find_contract.ex_date = exercise_date_time
                find_contract.save()
                build['results'] = {'success': True, 'key': cd['search_key'], 'cust_email': cd['cust_email'], 'exercise_fare': cd['exercise_fare'], 'exercise_date': exercise_date_time.strftime('%Y-%m-%d')}
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

    return gen_search_display(request, build, clean)