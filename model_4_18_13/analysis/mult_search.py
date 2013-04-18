#!/usr/bin/env python
from functions import *
from gen_price import simulation

import subprocess
import json
import multiprocessing
from multiprocessing import Queue
import sys
import time
import datetime
import pprint


class multi_simulation(search_inputs):

    def __init__(self, inputs, slider = 3, max_batch = 128):

        self.inputs = inputs
        self.slider = slider       
        self.max_batch = max_batch    
        self.q = Queue()
        self.dates = []
        self.wtpx = inputs.wtpx
        
        mid_depart = self.inputs.d_date1
        mid_return = self.inputs.r_date1
       
        
        #loop search parameters
        for d_slider_l in range(self.slider):
            for d_slider_r in range(self.slider):
                for r_slider_l in range(self.slider):
                    for r_slider_r in range(self.slider):                
                        sdate1 = mid_depart + datetime.timedelta(days = -1*d_slider_l)
                        sdate2 = mid_depart + datetime.timedelta(days = d_slider_r)
                        edate1 = mid_return + datetime.timedelta(days = -1*r_slider_l)
                        edate2 = mid_return + datetime.timedelta(days = r_slider_r)
                        collect = [sdate1,sdate2,edate1,edate2]
                        positions = (d_slider_l,d_slider_r,r_slider_l,r_slider_r)
                        collect.append(positions)
                        self.dates.append(collect)


    def run_simulation(self, correlated, expanded):
        
        self.inputs.d_date1 = self.d_date1
        self.inputs.d_date2 = self.d_date2
        self.inputs.r_date1 = self.r_date1
        self.inputs.r_date2 = self.r_date2
        self.inputs.wtpx = 0
        
        item = simulation(self.inputs)
        output = item.return_simulation(correlated, expanded)
        output_sliders = [output, self.sliders]
        self.q.put(output_sliders)    
        
    
    def run_multi_search(self, progress, correlated, expanded):
        
        start = time.time()
        results = []
        
        if (progress): print "set up " + `len(self.dates)` + " dates"
        while len(self.dates)>0:
            if (progress): print len(self.dates)                              
            if len(self.dates)>self.max_batch: 
                cycle = self.max_batch
            else:
                cycle = len(self.dates)
        
            jobs = []
            for i in range(cycle):
                if (progress): print `i` + " out of " + `len(self.dates)`
                
                self.d_date1 = self.dates[-1][0]
                self.d_date2 = self.dates[-1][1]
                self.r_date1 = self.dates[-1][2]
                self.r_date2 = self.dates[-1][3]
                self.sliders = self.dates[-1][4]
                p = multiprocessing.Process(target=self.run_simulation, args=(correlated, expanded))
                self.dates.pop()
                p.daemon = True
                jobs.append(p)
                p.start()

            for i in jobs:
                results.append(self.q.get())
                i.join()
                if (progress):  print '%s.exitcode = %s' % (i.name, i.exitcode)
        
        if (progress):  print "Completed " + `len(results)` + " jobs in " + `time.time()-start` + " seconds"    
        return results
    
    def format_prices(self, input):
        results = input
        d_slider_l = 0
        d_slider_r = 0
        r_slider_l = 0
        r_slider_r = 0
        
        def find_sublist_index(list, item):
            return next((i for i, sublist in enumerate(list) if item in sublist), None)
        
        def check_price_drop(raw, d_slider_l, d_slider_r, r_slider_l, r_slider_r, prev_base, prev_steadyfare):
            positions = (d_slider_l,d_slider_r,r_slider_l,r_slider_r)
            list_item = find_sublist_index(results, positions)
            cur_steadyfare = results[list_item][0]['steadyfare']
            cur_base = results[list_item][0]['holding_price']
            
            if cur_steadyfare == prev_steadyfare:
                if  prev_base > cur_base:
                    cur_base = prev_base
            results[list_item][0]['holding_price'] = cur_base
            
            return [cur_base, cur_steadyfare]
        
        # loop slider starting points to test of values if a slider notch moved one position outward results in a lower holding price, if so, it raises the price 
        for d_slider_l in range(self.slider):
            for d_slider_r in range(self.slider):
                for r_slider_l in range(self.slider):
                    for r_slider_r in range(self.slider):                
                        new_vals = check_price_drop(results, d_slider_l, d_slider_r, r_slider_l, r_slider_r, 0, 0)
                        if d_slider_l + 1 < (self.slider):
                            out_one = check_price_drop(results, d_slider_l + 1, d_slider_r, r_slider_l, r_slider_r, new_vals[0], new_vals[1])
                        if d_slider_r + 1 < (self.slider):
                            out_one = check_price_drop(results, d_slider_l, d_slider_r + 1, r_slider_l, r_slider_r, new_vals[0], new_vals[1])
                        if r_slider_l + 1 < (self.slider):
                            out_one = check_price_drop(results, d_slider_l, d_slider_r, r_slider_l + 1, r_slider_r, new_vals[0], new_vals[1])
                        if r_slider_r + 1 < (self.slider):
                            out_one = check_price_drop(results, d_slider_l, d_slider_r, r_slider_l, r_slider_r + 1, new_vals[0], new_vals[1])            
            
        # this increases the values of the holding prices according to the width of the slider ranges
        for i in range(len(results)):
            if (0 in results[i][0]['error']):
                slider_increment = sum(results[i][1])*self.wtpx
                results[i][0]['holding_price'] += slider_increment
        return results
    
    
    def fill_sliders(self, progress=False, formatted=True, correlated=True, expanded=False):
        results = self.run_multi_search(progress, correlated, expanded)
        if (formatted):
            results = self.format_prices(results)
        
        # extracts the simulation results dict from list, removing the slider position tuple
        bank = []
        for i in range(len(results)):
            bank.append(results[i][0])
        #return json.dumps(bank)
        return bank
    
    
if __name__ == "__main__":
    
    inputs = search_inputs(purpose='simulation')
    example = multi_simulation(inputs)
    print example.fill_sliders(progress=True)


        
