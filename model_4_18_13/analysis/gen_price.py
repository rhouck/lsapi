from functions import *
from pprint import pprint
    
class simulation(search_inputs):
        
    def __init__(self, inputs):
        self.initialize(inputs)
        self.output = dict()
        self.db = db()
        self.db_dict = db(cursorclass=MySQLdb.cursors.DictCursor, db=self.db_proj_source)
        self.weekday_types = weekday_pairs(self.flight_type)
        
        # stop script if errors in found in inputs    
        self.error = sim_errors(self.db, self.origin,self.destination,self.flight_type,self.lockin_per,self.start_date,self.d_date1,self.d_date2,self.r_date1,self.r_date2,self.final_proj_week, self.max_trip_length, self.geography) 
        if len(self.error.error_list) > 0:
            self.output['error'] = self.error.describe()
            self.output['dates'] = ''
            self.output['locked_fare'] = ''
            self.output['holding_price'] = ''    
        else:
            
            self.combined_date_string = self.date_to_string(self.d_date1) + ', ' + self.date_to_string(self.d_date2) + ', ' + self.date_to_string(self.r_date1) + ', ' + self.date_to_string(self.r_date2)
            
            beg_prefs_id = self.prefs.id          
            rows = self.find_rows()
            if not rows and self.prefs.id != 0:
                while not rows:
                    self.prefs = relax_prefs(self.prefs)  
                    rows = self.find_rows()
                    if self.prefs.id == 0:
                        break
                            
            end_prefs_id = self.prefs.id
    
            if not rows:
                self.error.error_list.append(14)
                self.output['error'] = self.error.describe()
                self.output['dates'] = self.combined_date_string
                self.output['locked_fare'] = ''
                self.output['holding_price'] = ''
            else:
                try:
                            
                    if end_prefs_id != beg_prefs_id:
                        self.changed_prefs = {'depart_times': self.prefs.dep_time_pref, 'return_times': self.prefs.ret_time_pref, 'nonstop': self.prefs.stop_pref, 'airline': self.prefs.airline_pref}
                        
                    date_proj = []
                    for i in rows:
                        date_proj.append({'date': format_as_date(i['beg_period']), 'proj_week': i['proj_week']})
                    
                    date_list = []
                    for i in date_proj:
                        date_list.append(i['date'])
                    sorted(date_list)
                    
                    self.numdays_dep = int((self.d_date2 - self.d_date1).days) + 1     
                    prev_date1 = self.search_date(self.d_date1, date_list, 0) # determines number of days allocated to the first flight price
                    prev_date2 = self.search_date(self.d_date2, date_list, 0) # determines number of days allocated to the second flight price
                           
                    # find number of departure days related to earlier projection date and later projection date
                    if (prev_date1 is not prev_date2):  
                        d_numdays1 = (prev_date2 - self.d_date1).days
                    else:
                        d_numdays1 = self.numdays_dep;
                    d_numdays2 = self.numdays_dep - d_numdays1
                    
                    
                    if self.flight_type == 'rt':         
                        self.numdays_ret = int((self.r_date2 - self.r_date1).days) + 1
                        
                        # use weekday types to ID each departure and return date, then find all possible combinations of travel dates
                        self.first_week_combos = self.weekday_types.travel_date_combos(self.d_date1, d_numdays1, self.r_date1, self.numdays_ret)
                        if d_numdays2 > 0:
                            self.second_week_combos = self.weekday_types.travel_date_combos(prev_date2, d_numdays2, self.r_date1, self.numdays_ret)
                        else: self.second_week_combos = {}
                    else:
                        self.numdays_ret = 0
                        
                        # use weekday types to ID each departure and return date, then find all possible combinations of travel dates
                        self.first_week_combos = self.weekday_types.travel_date_combos(self.d_date1, d_numdays1)
                        if d_numdays2 > 0:
                            self.second_week_combos = self.weekday_types.travel_date_combos(prev_date2, d_numdays2)
                        else: self.second_week_combos = {}
                    
                    
                    first_week_pricing = dict()
                    for i in self.first_week_combos.iterkeys():
                        first_week_pricing[i] = dict()
                        first_week_pricing[i]['fare'] = self.db_dict.sel_crit('one', '%sprojections' % (self.source), ['*'], {'route': self.route, 'beg_period': prev_date1, 'flight_type': self.flight_type, 'num_high_days': i, 'prefs': self.prefs.id})
                        first_week_pricing[i]['st_dev'] = self.db_dict.sel_crit('one', '%sstandard_deviations' % (self.source), ['*'], {'route': self.route, 'beg_period': prev_date1, 'flight_type': self.flight_type, 'num_high_days': i, 'prefs': self.prefs.id})
                    
                    second_week_pricing = dict()
                    for i in self.second_week_combos.iterkeys():
                        second_week_pricing[i] = dict()
                        second_week_pricing[i]['fare'] = self.db_dict.sel_crit('one', '%sprojections' % (self.source), ['*'], {'route': self.route, 'beg_period': prev_date2, 'flight_type': self.flight_type, 'num_high_days': i, 'prefs': self.prefs.id})
                        second_week_pricing[i]['st_dev'] = self.db_dict.sel_crit('one', '%sstandard_deviations' % (self.source), ['*'], {'route': self.route, 'beg_period': prev_date2, 'flight_type': self.flight_type, 'num_high_days': i, 'prefs': self.prefs.id})            
        
        
                    adjusted_val = markup_lockin(first_week_pricing, second_week_pricing, self.first_week_combos, self.second_week_combos, self.lockin_per)
                    self.markup = adjusted_val.markup            
                     
                    self.first_week_stats = adjusted_val.first_week_max_stats
                    self.second_week_stats = adjusted_val.second_week_max_stats 
                                
                    #current = current_max(self, prev_date1, prev_date2, self.first_week_combos, self.second_week_combos)
                    #self.steadyfare = math.ceil(max(adjusted_val.lockin, current.max_fare))
                    self.steadyfare = math.ceil(adjusted_val.lockin)

                    
                except Exception as err:
                    # stop running script if there is error generating inputs for simulation
                    print "gen_price error: %s - likely no projections exist for the flight dates selected" % (err)
                    self.error.error_list.append(1)
                    self.output['error'] = self.error.describe()
                    self.output['dates'] = self.combined_date_string
                    self.output['locked_fare'] = ''
                    self.output['holding_price'] = ''
                
        self.db.db_disconnect() 
        self.db_dict.db_disconnect()    
    
                
    def instance_gen_random(self, p,sd,l):
        sample = random.gauss(p,sd)
        if (sample>l):
            payout = sample - l
        else: payout = 0
        return payout


    def instance_supply_random(self, p,sd,l,draw):
        sample = p + (sd*draw)
        if (sample>l):
            payout = sample - l
        else: payout = 0
        return payout
    
    
    # run correlated simulation model
    def sim_correlated(self):
                
        payouts = []
        for k in range(self.cycles):
            ret_day_mult = self.numdays_ret if self.numdays_ret > 0 else 1 
            random_nums = self.draw_correlated(self.numdays_dep * ret_day_mult, self.correl_coef)
            instance_bank = [] # builds list of random payouts for every combination of travel day
            
            for num_highs, combos in self.first_week_combos.iteritems():
                 for i in range(combos):
                    selected = random_nums.pop()
                    instance_bank.append(self.instance_supply_random(self.first_week_stats[num_highs]['fare'], self.first_week_stats[num_highs]['st_dev'], self.steadyfare, selected))
            
            for num_highs, combos in self.second_week_combos.iteritems():
                 for i in range(combos):
                    selected = random_nums.pop()
                    instance_bank.append(self.instance_supply_random(self.second_week_stats[num_highs]['fare'], self.second_week_stats[num_highs]['st_dev'], self.steadyfare, selected))

            payouts.append(max(instance_bank))
        return sum(payouts) / self.cycles
    
    
    # this finds the date in projection records that relates to the appropriate projected price for d_date...
    def search_date(self, d, a, b):
        for i in range(len(a)):
            if i is not (len(a)-1):
                if (d < a[i+1]): 
                    reldate = a[i-b]
                    break
            else: 
                reldate = a[i-b]
                break    
        if (d - reldate).days > 7:
            raise Exception("Insufficient projection data in 'search_date' function")
        return reldate;
    
    
    def date_to_string(self, date_arg):
        
        def fix_at_two(val):
            if val < 10:
                return `0` + `val`
            else: return `val`
                
        return `date_arg.year` + `date_arg.month` + fix_at_two(date_arg.day)


    def draw_correlated(self, num_draws, correlation_est):
        """
        @todo: look into creating a matrix using scipy
        """
        rand_draws = []
    
        if correlation_est == 1:
            rand_draw = random.gauss(0,1)
            for i in range(num_draws):
                rand_draws.append(rand_draw)
            return rand_draws 
        
        elif correlation_est == 0:
            for i in range(num_draws):
                rand_draw = random.gauss(0,1)
                rand_draws.append(rand_draw)
            return rand_draws 
        
        else:
            # generate requisite number of random numbers, uncorrelated
            for i in range(num_draws):
                rand_draws.append(random.gauss(0,1))
             
            # correlation matrix
            pvals = []
            for i in range(num_draws):
                pvals.append([])
                for j in range(num_draws):
                    value = 1 if i == j else correlation_est
                    pvals[i].append(value) 
            
            # runs cholesky decomposition on matrix
            A = Cholesky(pvals)
            
            # multiplies random generated matrix by decomposed correlation matrix
            corr_rands = []
            for i in range(len(rand_draws)):
                sum = 0
                for j in range(len(rand_draws)):
                    sum = rand_draws[j]*A[j][i] + sum
                corr_rands.append(sum)
                     
            return corr_rands
        
        
    def return_standard_results(self):        
        # calculate holding price
        wtp_floor = self.steadyfare * self.wtp 
        buffered_risk = self.expected_risk + self.buffer
        un_adjusted = math.ceil(( max(wtp_floor, buffered_risk) )/self.round_to) * self.round_to
        double_count_fix = -1 if self.flight_type == 'rt' else 0
        flexibility_fee = ((self.numdays_dep + self.numdays_ret - 1 + double_count_fix) * self.wtpx )
        holding_per = ((self.d_date1 + datetime.timedelta(weeks = -self.lockin_per)) - self.start_date).days / 7 
        holding_time_fee = max((holding_per-1),0) * self.wtpx
        holding_price = un_adjusted + flexibility_fee + holding_time_fee
        
        #format date output
        #combined_date_string = self.date_to_string(self.d_date1) + self.date_to_string(self.d_date2) + self.date_to_string(self.r_date1) + self.date_to_string(self.r_date2)
        if (self.expected_risk > 0) and (self.steadyfare > 0) and (holding_price > 0):
            if (holding_price > 200) or (holding_price > .25 * self.steadyfare):
                # all unreasonably expensive option prices are assumed to be due to insufficient data
                self.error.error_list.append(12)
                self.output['error'] = self.error.describe()
                self.output['dates'] = self.combined_date_string
                self.output['locked_fare'] = ''
                self.output['holding_price'] = ''
            else:
                self.error.error_list.append(0)
                self.output['error'] = self.error.describe()
                self.output['dates'] = self.combined_date_string
                self.output['locked_fare'] = self.steadyfare
                self.output['holding_price'] = holding_price
                if hasattr(self, 'changed_prefs'): 
                    self.output['changed_prefs'] = self.changed_prefs
                    
        else:
            self.error.error_list.append(1)
            self.output['error'] = self.error.describe() 
            self.output['dates'] = self.combined_date_string
            self.output['locked_fare'] = ''
            self.output['holding_price'] = ''

        return self.output        
    
    
    def return_simulation(self, expanded=False):    
        
        if not self.output:
            self.expected_risk = self.sim_correlated()
            
            if expanded:
                self.return_standard_results()
                expanded = self.__dict__
                expanded['error_description'] = self.error.describe()
                return expanded
            else: 
                return self.return_standard_results()
        else:   
            return self.output
        
    
    def find_rows(self):
        """
        @summary: this serves two purposes: 
            1) ensures there is projection data available for the set of preferences in question
            2) builds the set of date ranges to use for selecting appropriate projection data
                - these ranges should be the same regardless of which "num_high_days" is being referenced, it loops over all six just to ensure the data is available 
        """
        possible_weekday_pairs = self.weekday_types.travel_date_combos(self.d_date1, (self.d_date2-self.d_date1).days+1, self.r_date1, (self.r_date2-self.r_date1).days+1)
        for i in possible_weekday_pairs.iterkeys():
            rows = self.db_dict.sel_crit('all', '%sprojections' % (self.source), ['beg_period', 'proj_week'], {'route': self.route, 'flight_type': self.flight_type, 'num_high_days': i, 'prefs': self.prefs.id})
            if not rows:
                return None
            # check if projections include the departure dates relevant to the search
            if rows:
                #pprint(rows)
                date_bank = []
                for j in rows:
                    date_bank.append(j['beg_period'])
                if max(date_bank) + datetime.timedelta(days = 7) < self.d_date1:
                    return None   
        return rows
    
    
class markup_lockin(object):
    
    # build in error catcher
    def __init__(self, first_week_pricing, second_week_pricing, first_week_combos, second_week_combos, lockin_per):
        
        self.first_week_pricing = first_week_pricing
        self.second_week_pricing = second_week_pricing
        
        # find appropriate markup level
        self.average_sd = self.set_average_sd(first_week_combos, second_week_combos, lockin_per)
        self.markup = self.set_markup(self.average_sd)  
        
        # select highest risk price-standard deviation combination for each category and insert None-type elements
        self.first_week_max_stats = self.ensure_max_risk_stats(self.first_week_pricing, lockin_per)
        self.second_week_max_stats = self.ensure_max_risk_stats(self.second_week_pricing, lockin_per)
        
        # set lockin
        self.lockin = self.set_lockin()  
        
        
    def ensure_max_risk_stats(self, pricing, lockin_per):    
        """
        @summary: this helps account for the fact that periods before option expiration may be riskier than the period at expiration by 
                 selecting the highest risk set of prices and standard deviations given a set markup level.
                 In effect, this prevents arbitrage opportunities in which customers could otherwise save money by selecting a longer holding_period option because the route is less risky closer to departure
        @attention: while finding potentially higher risk periods before option expiration, this function assumes that the first None type 
                    element found in the dictionary means all other higher numbered lockin period values will also have None-type values
        """
        bank = dict()
        for k, v in pricing.iteritems():
            
            bank[k] = dict()
            max_lockin = 0
            max_week = None
        
            for i in range(lockin_per, v['fare']['proj_week']):
                try:
                    temp_lockin = v['fare']['%s' % (i)] + ( v['st_dev']['%s' % (i)] * self.markup )
                except:
                    temp_lockin = None
                if i == lockin_per and not temp_lockin:
                    raise Exception("ensure_max_risk_stats function didn't have min necessary data")
                if temp_lockin > max_lockin:
                    max_lockin = temp_lockin
                    max_week = i
                    
            bank[k]['fare'] = pricing[k]['fare']['%s' % (max_week)]
            bank[k]['st_dev'] = pricing[k]['st_dev']['%s' % (max_week)]
        
        return bank
    
        
    def set_average_sd(self, first_week_combos, second_week_combos, lockin_per):
        
        count, total = 0, 0
        
        for i in first_week_combos.itervalues():
            count += i
        for i in second_week_combos.itervalues():
            count += i
        
        for k, v in self.first_week_pricing.iteritems():
            total += v['st_dev']['%s' % (lockin_per)] * first_week_combos[k]
        
        for k, v in self.second_week_pricing.iteritems():
            total += v['st_dev']['%s' % (lockin_per)] * second_week_combos[k]
        
        average = total / count
        return average
    
    
    def set_markup(self, average_sd):
        """
        @summary: This list below sets 'ideal' markup levels for a given average standard deviation of flight prices for dates selected.
                  As of 1/11/13, these levels are set so that holding price on a low-flexibility option will be roughly 20 dollars at break-even 
                  (holding price does increase at extreme standard deviation values).
        """
        if average_sd <= 50:
            return 0.0
        elif average_sd <= 62.5:
            return 0.15
        elif average_sd <= 75:
            return 0.25
        elif average_sd <= 87.5:
            return 0.35
        elif average_sd <= 100:
            return 0.5
        elif average_sd <= 150:
            return 0.55
        else: 
            return 0.6

    
    def set_lockin(self):
        
        bank = []
        
        for k in self.first_week_max_stats.iterkeys():
            bank.append(self.first_week_max_stats[k]['fare'] + (self.first_week_max_stats[k]['st_dev'] * self.markup))
        for k in self.second_week_max_stats.iterkeys():
            bank.append(self.second_week_max_stats[k]['fare'] + (self.second_week_max_stats[k]['st_dev'] * self.markup))    
            
        return max(bank)


  
class current_max(search_inputs):
    
    def __init__(self, inputs, prev_date1, prev_date2, first_week_combos, second_week_combos): 
                 
                 
        self.initialize(inputs)
        self.db = db(cursorclass=MySQLdb.cursors.DictCursor, db = self.db_proj_source)
        self.max_fare = self.loop_potential_fare_types(prev_date1, prev_date2, first_week_combos, second_week_combos)
    
        self.db.db_disconnect()
        
    
    def loop_potential_fare_types(self, prev_date1, prev_date2, first_week_combos, second_week_combos):
        try:
            bank = []
            for i in first_week_combos.iterkeys():
                bank.append(self.find_current_fare(prev_date1, i))
            for i in second_week_combos.iterkeys():
                bank.append(self.find_current_fare(prev_date2, i))
            
            return max(bank)
        except:
            print "Could not find current max fare"
            return None
        
        
    def find_current_fare(self, prev_date, num_high_days):
        
        fare_row = self.db.sel_crit('one', '%sprojections' % (self.source), ['*'], {'route': self.route, 'beg_period': prev_date, 'flight_type': self.flight_type, 'num_high_days': num_high_days, 'prefs': self.prefs.id})
        bank = []
        for k, v in fare_row.iteritems():
            if k.isdigit() and v:
                bank.append(k)
        return fare_row['%s' % (max(bank))]
                
        
    def potential_flight_dates(self):
        bank = []
        dep_range = (self.d_date2 - self.d_date1).days
        ret_range = (self.r_date2 - self.r_date1).days
        
        for i in range(dep_range + 1):
            for j in range(ret_range + 1):
                bank.append((self.d_date1 + datetime.timedelta(days = i), self.r_date1 + datetime.timedelta(days = j)))
        
        return bank

    
if __name__ == "__main__":
    
    inputs = search_inputs(purpose='simulation', lockin_per = 5, geography='eu', origin = "LHR", destination = "BOM", d_date1 = '2013-7-13', d_date2 = '2013-7-17', r_date1 = '2013-7-31', r_date2 = '2013-7-31')
    example = simulation(inputs)
    pprint(example.return_simulation())
    
    
    