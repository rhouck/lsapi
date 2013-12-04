from sales.models import *
from api.utils import current_time_aware, conv_to_js_date, gen_alphanum_key, check_creds, run_authnet_trans, test_trans


def exercise_option(cust_key, search_key, exercise, fare=None, dep_date=None, ret_date=None, flight_choice=None, use_gateway=True):

    build = {}

    try:

        find_cust = Customer.objects.get(key__iexact=cust_key)
        find_contract = Contract.objects.get(customer=find_cust, search__key=search_key)

    except (KeyError, Customer.DoesNotExist, Contract.DoesNotExist):
        build['error_message'] = 'The user id and/or transaction id is not valid.'
        build['results'] = {'success': False, 'error': 'The user id and/or transaction id is not valid.'}

    else:
        if not find_contract.outstanding() and exercise:
            build['error_message'] = 'The contract selected is either expired or already exercised.'
            build['results'] = {'success': False, 'error': 'The contract selected is either expired or already exercised.'}
        elif find_contract.ex_date:
            build['error_message'] = 'The contract has already been closed.'
            build['results'] = {'success': False, 'error': 'The contract has already been closed.'}
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

