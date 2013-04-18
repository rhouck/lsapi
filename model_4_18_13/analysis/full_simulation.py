#!/usr/bin/env python
from functions import *
#from projection import *
from gen_price import *
from accuracy_testing import *

from random import choice
import copy
from pprint import pprint
import time
from decimal import Decimal                  
import math
import functools

class full_simulation(object):
    
    # this class generates an option and attempts to exercise it
    def __init__(self, source = 'temp_options', num_proj_groups = 5, options_per_group = 50, start_date_days_back = 150, start_date_width = 100, 
                 valid_attempts = 1, max_hold_per = 10, no_prefs = True, single_day_only = False, early_exercise = False, geography="eu"):
        
        self.db = db(db='steadyfa_temp_tables')
        self.db_routes = db()
        self.options_table = self.errors = None
        
        # full_simulation specific assumptions
        self.source = source
        self.num_proj_groups = num_proj_groups
        self.options_per_group = options_per_group                    
        self.start_date_days_back = start_date_days_back
        self.start_date_width = start_date_width
        self.valid_attempts = valid_attempts 
        self.max_hold_per = max_hold_per
        self.no_prefs = no_prefs
        self.single_day_only = single_day_only 
        self.early_exercise = early_exercise
        self.geography = geography
        
        if self.db.does_table_exist(self.source):
            self.summary = data_set_analysis(import_table(self.source, db_name='steadyfa_temp_tables'))   
    
        
    def run(self, test_projections=False):
        
        start = time.time()
        self.errors = []
        # create options table
        columns = {'route': 'VARCHAR(8)', 'flight_type': 'VARCHAR(4)', 'prefs': 'INT(3)', 'errors': 'VARCHAR(8)', 
                   'proj_week': 'INT(1)', 'num_fare_data': 'INT(3)', 'lockin_per': 'INT(3)', 'hold_per': 'INT(3)', 'exercise_per': 'INT(3)', 'markup': 'DOUBLE',  
                   'locked_fare': 'DOUBLE', 'holding_price': 'DOUBLE', 'exercised_fare': 'DOUBLE', 'amt_in_money': 'DOUBLE', 'cash_effect': 'DOUBLE',
                   'numdays_dep': 'INT(1)', 'numdays_ret': 'INT(1)', 'total_flex': 'INT(2)', 'depart_date': 'DATE', 'return_date': 'DATE', 'purchase_date': 'DATE',
                   'first_week_max_fare': 'DOUBLE', 'first_week_avg_fare': 'DOUBLE', 'first_week_max_st_dev': 'DOUBLE', 'first_week_avg_st_dev': 'DOUBLE', 'second_week_max_fare': 'DOUBLE', 'second_week_avg_fare': 'DOUBLE', 'second_week_max_st_dev': 'DOUBLE', 'second_week_avg_st_dev': 'DOUBLE'}
                   
        self.db.replace_existing_table(self.source, columns)
        
        if test_projections:
            self.db.drop_existing('temp_accuracy_testing')
        
        for i in range(self.num_proj_groups):    
            self.db.drop_existing('temp_projections')
            
            # begin process of randomizing projections, if valid projection set generated, then attempt to generate and 'exercise' options
            if not self.geography:
                options = ['us', 'eu']
                sel_geo = choice(options)
            else:
                sel_geo = self.geography
            
            origin = self.db_routes.get_random_row('hubs_%s' % (sel_geo), column='Airport')
            destination = self.db_routes.get_random_row('destinations_%s' % (sel_geo), column='Airport')
            rand_start_interval = randint(0, self.start_date_width)
            start_date = datetime.datetime.now().date() + datetime.timedelta(days = -self.start_date_days_back+rand_start_interval)
            print "Simulation date: %s" % (start_date)
            
            valid = False
            counter = 0
            while valid == False:   
                counter += 1
                inputs = search_inputs(purpose=('projection','simulation'), source = 'temp_', start_date=start_date, origin=origin, destination=destination, geography=self.geography)
                
                if self.no_prefs or counter == self.valid_attempts:
                    prefs_id = 0
                else: 
                    if counter == 1:
                        prefs_id = randint(0, len(inputs.prefs.id_list)-1)
                        inputs.prefs.set_inputs_by_id(prefs_id)
                    else:
                        inputs.prefs = relax_prefs(inputs.prefs)      
    
                try:
                    # build temporary projection table if possible
                    # if after x attempts, no valid projection set is generated, no projections are stored and the process is skipped
                    projection = projection_set(inputs, record=True)
                    projection.loop_num_high_days() 
                    
                    self.max_proj_week = self.db.sel_crit('one', 'temp_projections', ['max(`proj_week`)'], {})[0]  
                    if not self.max_proj_week:
                        self.db.drop_existing('temp_projections')
                        raise Exception("temp_projection table empty")
                        
                    else:    
                        if test_projections:
                            test_projections = projection_analysis(inputs, source_projected=('temp_projections')) 
                            test_projections.run(replace=False)
                        valid = True
                    
                except Exception as err: 
                    #print err
                    self.errors.append("Error- origin: %s, destination: %s, start_date: %s, prefs_id: %s - Did not generate projection set - %s" % (origin, destination, start_date, prefs_id, err))
                    if counter == self.valid_attempts:
                        break
                    else: print "No projection set generated, attempt %s" % (counter+1)
                    
            if valid:    
                for j in range(self.options_per_group):
                    # create random options based on temporary projection table, 
                    # inputs must not create options for pricing that has not taken place yet
                    # if after x attempts, no valid inputs are generated, no option is calculated and the process is skipped
                    valid = False
                    counter = 0
                    while valid == False:   
                        counter += 1
                        first_dep_days_out = randint((inputs.final_proj_week+1)*7, min(self.max_proj_week, inputs.num_wks_proj_out)*7)
                        inputs.d_date1 = inputs.start_date + datetime.timedelta(days = first_dep_days_out)
                        if self.single_day_only:
                            inputs.d_date2 = inputs.d_date1
                        else:
                            inputs.d_date2 = min(inputs.d_date1 + datetime.timedelta(days = randint(0,4)), inputs.start_date + datetime.timedelta(days = (inputs.num_wks_proj_out*7 + 6)))
                        
                        inputs.proj_week = floor((inputs.d_date1-inputs.start_date).days / 7) 
                        inputs.lockin_per = randint(max(inputs.final_proj_week,(inputs.proj_week-self.max_hold_per)), (inputs.proj_week-1))
                        if (inputs.d_date2 - datetime.timedelta(days = inputs.lockin_per * 7)) < datetime.datetime.now().date():
                            valid = True
                        elif counter == self.valid_attempts:
                            self.errors.append("Soft error- origin: %s, destination: %s, start_date: %s, prefs_id: %s - Did not generate valid input set in ten cycles; did not attempt to generate option" % (origin, destination, start_date, prefs_id))
                            break
                    
                    if valid:   
                        inputs.r_date1 = inputs.d_date2 + datetime.timedelta(days = randint(1,(inputs.max_trip_length*7)-1))  
                        if self.single_day_only:
                            inputs.r_date2 = inputs.r_date1
                        else:
                            inputs.r_date2 = inputs.r_date1 + datetime.timedelta(days = randint(0,4))
                            
                        option = simulation(inputs)
                        results = option.return_simulation(expanded=True)                
                        
                        if 'output' not in results:
                            #pprint(results)
                            self.errors.append("Error- origin: %s, destination: %s, error_code: (%s), prefs_id: %s - Error generating option price with 'gen_price'" % (origin, destination, results['error'], prefs_id))  
                        else:
                            exercise = exercise_option(results, self.source, self.db, self.early_exercise)
                            exercise.random_exercise()
                            
                            if exercise.error:
                                self.errors.append(exercise.error)

                        print "route %s: %s - attempted %s transactions" % (i+1, inputs.route, (j+1)) 
            
        self.summary = data_set_analysis(import_table(self.source, db_name='steadyfa_temp_tables'))                
        print "Completed in " + `((time.time()-start)/60.0)` + " minutes"
    
    
    def find_percentile(self, sample_size, trials, category, stat):
        """
        @param category: specify the type of summarized data, eg - cash_effect, amt_in_money, exercised_fare, holding_price, locked_fare
        @param stat: specify the summary statistic in question, eg - Avg, St_Dev, Med, Min, Max 
        """
        if self.db.does_table_exist(self.source):
            percentile_summary = dict()
            bank = []
            for i in range(trials):
                print 'trial: %s' % (i)
                trial = data_set_analysis(import_table(self.source, db_name='steadyfa_temp_tables'))
                trial.select_subset(sample_size)
                trial.group_data_on([], on_category=True)
                trial.stats = summarize_grouped_data(trial.grouped_data)
                trial.stats.full_stats(on_exercise=True)
                bank.append(trial.stats.stat_set[0][category][stat])
            
            percentile_summary['sample_size'] = sample_size
            percentile_summary['.01'] = percentile(bank, .01)
            percentile_summary['.25'] = percentile(bank, .25)
            percentile_summary['.50'] = percentile(bank, .5)
            percentile_summary['.75'] = percentile(bank, .75)

            return percentile_summary        
        else: 
            return "No available source data-set. Try building source with 'run' function."
    
                
class exercise_option(object): 
    
    def __init__(self, option, source, db_curs, early_exercise, max_attempts = 5):
    
        self.db = db_curs
        self.option = option
        self.error = None
        self.source = source
        self.early_exercise = early_exercise
        self.max_attempts = max_attempts
        
    def random_exercise(self):
        # chooses a single depart and return date at random, and exercises as late as possible
        try:
            if self.early_exercise:
                gap = self.option['proj_week'] - self.option['lockin_per'] - 1
                sample = abs(random.gauss(0, (gap/2.0)))
                exercise_per = int(min(floor(self.option['lockin_per'] + sample), (self.option['proj_week']-1)))
            else:
                sample = 0
                exercise_per = self.option['lockin_per']
            #print "proj_wk: %s, lockin: %s, exercise: %s, sample: %s" % (self.option['proj_week'], self.option['lockin_per'], exercise_per, sample)  
            
            valid_attempts = min(self.max_attempts,(self.option['numdays_dep']*self.option['numdays_ret']))
            for i in range(valid_attempts):
                #print "try %s out of %s" % ((i+1), valid_attempts)
                self.sel_dep_date = self.option['d_date1'] + datetime.timedelta(days = randint(0,self.option['numdays_dep']-1))
                self.sel_ret_date = self.option['r_date1'] + datetime.timedelta(days = randint(0,self.option['numdays_ret']-1))       
                try:
                    self.exercised_fare = self.db.find_single_min_fare(self.option['origin'], self.option['destination'], self.sel_dep_date, self.sel_ret_date, self.option['flight_type'], exercise_per, self.option['prefs'], self.option['depart_length_width'], self.option['max_trip_length'], self.option['weekday_types'])       
                except:
                    self.exercised_fare = None
                
                if self.exercised_fare or (i+1) == valid_attempts:
                    break
                
            self.amt_in_money = (self.exercised_fare[0] - self.option['output']['locked_fare']) if (self.exercised_fare[0] > self.option['output']['locked_fare']) else 0  
            self.cash_effect = self.option['output']['holding_price'] - self.amt_in_money
            
            try:
                first_week_max_avg = avearege_max_projected_stats(self.option['first_week_stats'], self.option['first_week_combos'])
                first_week_max_fare = first_week_max_avg['max_fare'] 
                first_week_max_st_dev = first_week_max_avg['max_st_dev']
                first_week_avg_fare = first_week_max_avg['avg_fare']
                first_week_avg_st_dev = first_week_max_avg['avg_st_dev']
            except:
                first_week_max_fare = first_week_max_st_dev = first_week_avg_fare = first_week_avg_st_dev = "NULL"
            try:
                second_week_max_avg = avearege_max_projected_stats(self.option['second_week_stats'], self.option['second_week_combos'])
                second_week_max_fare = second_week_max_avg['max_fare'] 
                second_week_max_st_dev = second_week_max_avg['max_st_dev']
                second_week_avg_fare = second_week_max_avg['avg_fare']
                second_week_avg_st_dev = second_week_max_avg['avg_st_dev']
            except:
                second_week_max_fare = second_week_max_st_dev = second_week_avg_fare = second_week_avg_st_dev = "NULL"
            
                        
            values = {'route': "'%s'" % (self.option['route']), 'flight_type': "'%s'" % (self.option['flight_type']), 'prefs': self.option['prefs'].id, 'errors': "'%s'" % (','.join(str(e) for e in self.option['output']['error'])), 
                   'proj_week': self.option['proj_week'], 'num_fare_data': self.exercised_fare[1], 'lockin_per': self.option['lockin_per'], 'hold_per': (self.option['proj_week']-self.option['lockin_per']), 'exercise_per': exercise_per, 'markup': (self.option['markup']*100), 
                   'locked_fare': self.option['output']['locked_fare'], 'holding_price': self.option['output']['holding_price'], 'exercised_fare': self.exercised_fare[0], 'amt_in_money': self.amt_in_money, 'cash_effect': self.cash_effect,
                   'numdays_dep': self.option['numdays_dep'], 'numdays_ret': self.option['numdays_ret'], 'total_flex': (self.option['numdays_dep']+self.option['numdays_ret']), 'depart_date': "'%s'" % (self.sel_dep_date), 'return_date': "'%s'" % (self.sel_ret_date), 'purchase_date': "'%s'" % (self.option['start_date']),
                   'first_week_max_fare': first_week_max_fare, 'first_week_avg_fare': first_week_avg_fare, 'first_week_max_st_dev': first_week_max_st_dev, 'first_week_avg_st_dev': first_week_avg_st_dev, 
                   'second_week_max_fare': second_week_max_fare, 'second_week_avg_fare': second_week_avg_fare, 'second_week_max_st_dev': second_week_max_st_dev, 'second_week_avg_st_dev': second_week_avg_st_dev}
                   
            self.db.insert_data(self.source, values)
            
        except Exception as err:
            self.error = "Error- origin: %s, destination: %s, dep_date: %s, ret_date: %s, flight_type: %s,  lockin_per: %s, prefs_id: %s,  - %s" % (self.option['origin'], self.option['destination'], self.sel_dep_date, self.sel_ret_date, self.option['flight_type'], self.option['lockin_per'], self.option['prefs'].id, err)
           
        
if __name__ == "__main__":

    source='temp_options'
    
    example = full_simulation() 
    #pprint(example.find_percentile(500, 10, 'cash_effect', 'Avg'))
    example.run(test_projections=True)
    example.summary.group_data_on([], on_category=True)
    example.summary.stats = summarize_grouped_data(example.summary.grouped_data)
    example.summary.stats.full_stats(on_exercise=True)
    pprint(example.summary.stats.stat_set)
    #pprint(example.summary.stats.show_stats_where({'prefs': 0}))
    #pprint(example.errors)
    
    
    """
    example = full_simulation(source)
    example.summary.group_data_on(['hold_per', 'proj_week'], on_category=True)
    example.summary.stats = summarize_grouped_data(example.summary.grouped_data)
    example.summary.stats.full_stats(on_exercise=True)
    #pprint(example.summary.stats.stat_set)
    
    
    for j in range(1,11):    
        for k in range(1,16):
            new_dict = dict()
            new_dict['hold_per'] = j
            new_dict['proj_week'] = k
            try: 
                new_dict['cash_effect'] = '%.2f' % (example.summary.stats.show_stats_where({'hold_per': j, 'proj_week': k})[0]['cash_effect']['Avg'])
            except: 
                new_dict['cash_effect'] = None
            try: 
                new_dict['conversion'] = example.summary.stats.show_stats_where({'hold_per': j, 'proj_week': k})[0]['amt_in_money']['percent_exercised']
            except: 
                new_dict['conversion'] = None
            try: 
                new_dict['amt_in_money'] = '%.2f' % (example.summary.stats.show_stats_where({'hold_per': j, 'proj_week': k})[0]['amt_in_money']['Avg'])
            except: 
                new_dict['amt_in_money'] = None
            try: 
                new_dict['holding_price'] = '%.2f' % (example.summary.stats.show_stats_where({'hold_per': j, 'proj_week': k})[0]['holding_price']['Avg'])
            except: 
                new_dict['holding_price'] = None
            if new_dict['amt_in_money'] and new_dict['conversion'] and new_dict['cash_effect'] and new_dict['holding_price']:  
                print new_dict   
    
    
    
    example = full_simulation(source)
    example.summary.group_data_on(['route'], on_category=True)
    example.summary.stats = summarize_grouped_data(example.summary.grouped_data)
    example.summary.stats.full_stats(on_exercise=True)
    #pprint(example.summary.stats.stat_set)
    
    
    
    destinations = import_table('destinations')
    for index, i in enumerate(destinations):
        new_dict = dict()
        route = 'SFO_%s' % (i['Airport'])
        new_dict['route'] = route
        try: 
            new_dict['cash_effect'] = '%.2f' % (example.summary.stats.show_stats_where({'route': route})[0]['cash_effect']['Avg'])
        except: 
            new_dict['cash_effect'] = None
        try: 
            new_dict['conversion'] = example.summary.stats.show_stats_where({'route': route})[0]['amt_in_money']['percent_exercised']
        except: 
            new_dict['conversion'] = None
        try: 
            new_dict['amt_in_money'] = '%.2f' % (example.summary.stats.show_stats_where({'route': route})[0]['amt_in_money']['Avg'])
        except: 
            new_dict['amt_in_money'] = None
        try: 
            new_dict['holding_price'] = '%.2f' % (example.summary.stats.show_stats_where({'route': route})[0]['holding_price']['Avg'])
        except: 
            new_dict['holding_price'] = None
        if new_dict['amt_in_money'] and new_dict['conversion'] and new_dict['cash_effect'] and new_dict['holding_price']:  
            print new_dict   
    
    
    example = full_simulation(source)
    example.summary.group_data_on(['markup'], on_category=True)
    example.summary.stats = summarize_grouped_data(example.summary.grouped_data)
    example.summary.stats.full_stats(on_exercise=True)
    #pprint(example.summary.stats.stat_set)
    
    
    markups = [0, 15, 25, 35, 5, 55, 60]
    for i in markups:
        new_dict = dict()
        new_dict['markup'] = i
        try: 
            new_dict['cash_effect'] = '%.2f' % (example.summary.stats.show_stats_where({'markup': i})[0]['cash_effect']['Avg'])
        except: 
            new_dict['cash_effect'] = None
        try: 
            new_dict['conversion'] = example.summary.stats.show_stats_where({'markup': i})[0]['amt_in_money']['percent_exercised']
        except: 
            new_dict['conversion'] = None
        try: 
            new_dict['amt_in_money'] = '%.2f' % (example.summary.stats.show_stats_where({'markup': i})[0]['amt_in_money']['Avg'])
        except: 
            new_dict['amt_in_money'] = None
        try: 
            new_dict['holding_price'] = '%.2f' % (example.summary.stats.show_stats_where({'markup': i})[0]['holding_price']['Avg'])
        except: 
            new_dict['holding_price'] = None
        if new_dict['amt_in_money'] and new_dict['conversion'] and new_dict['cash_effect'] and new_dict['holding_price']:  
            print new_dict   
    
    
    example = full_simulation(source)
    example.summary.group_data_on(['hold_per'], on_category=True)
    example.summary.stats = summarize_grouped_data(example.summary.grouped_data)
    example.summary.stats.full_stats(on_exercise=True)
    #pprint(example.summary.stats.stat_set)
    
    
    for j in range(0,16):    
        new_dict = dict()
        new_dict['hold_per'] = j
        try: 
            new_dict['cash_effect'] = '%.2f' % (example.summary.stats.show_stats_where({'hold_per': j})[0]['cash_effect']['Avg'])
        except: 
            new_dict['cash_effect'] = None
        try: 
            new_dict['conversion'] = example.summary.stats.show_stats_where({'hold_per': j})[0]['amt_in_money']['percent_exercised']
        except: 
            new_dict['conversion'] = None
        try: 
            new_dict['amt_in_money'] = '%.2f' % (example.summary.stats.show_stats_where({'hold_per': j})[0]['amt_in_money']['Avg'])
        except: 
            new_dict['amt_in_money'] = None
        try: 
            new_dict['holding_price'] = '%.2f' % (example.summary.stats.show_stats_where({'hold_per': j})[0]['holding_price']['Avg'])
        except: 
            new_dict['holding_price'] = None
        if new_dict['amt_in_money'] and new_dict['conversion'] and new_dict['cash_effect'] and new_dict['holding_price']:  
            print new_dict   
    """