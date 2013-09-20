#!/usr/bin/env python
from functions import *
import time

class projection(search_inputs):

    def __init__(self, inputs):

        start = time.time()
        self.initialize(inputs)
        self.hist_movement = dict()
        self.adjusted_fares = dict()
        self.errors = []
        # this serves as a marker so that unnecessary operations aren't run
        self.is_previous = False

        if self.black_list_error:

            class Blank(search_inputs):
                pass

            self.previous = Blank()
            self.previous.initialize(inputs)
            self.previous.hist_movement = dict()
            self.previous.adjusted_fares = dict()
            self.previous.errors = []
            self.previous.earliest_source_date += datetime.timedelta(days = -7)
            self.previous.start_date += datetime.timedelta(days = -7)
            self.previous.end_period += datetime.timedelta(days = -7)
            self.previous.beg_period += datetime.timedelta(days = -7)
            self.previous.is_previous = True


        # pull minimums for this num_high_days and prefs setting
        self.db_mins = db(cursorclass=MySQLdb.cursors.DictCursor, db='steadyfa_temp_tables')
        try:
            #adjust dates to allow for testing previous week's accuracy
            selected_earliest_source_date = self.earliest_source_date if not self.black_list_error else self.previous.earliest_source_date
            self.db_mins.pull_mins(self.origin, self.destination, selected_earliest_source_date, self.start_date, self.flight_type, self.max_trip_length, self.prefs.id, self.num_high_days)
        except Exception as err:
                self.errors.append("Error: route %s_%s, prefs %s, numhighs %s - problem pulling small subset of minimum fares from projection_prep (%s)" % (self.origin, self.destination, self.prefs.id, self.num_high_days, err))
        self.db_mins.db_disconnect()


        # generate set of average current prices on future flights
        try:
            self.base_fares = current_fares(self)
            self.base_fares.projection()

            if self.black_list_error:
                self.previous.base_fares = current_fares(self.previous)
                self.previous.base_fares.projection()

        except Exception as err:
                self.errors.append("Error: route %s_%s, prefs %s, numhighs %s - problem generating set of current fares on future flights (%s)" % (self.origin, self.destination, self.prefs.id, self.num_high_days, err))

        # apply rates of change, etc, to generate projection set
        self.project()


    def project(self):

        #start = time.time()
        if 1 > self.weight_on_imp > 0:

            switch = ('implied', 'historical',)
            for i in switch:
                self.type = i
                self.process()

            try:
                # find weighted average of implied and historical values
                self.adjusted_fares['combined'] = apply_change_rates(self)

                keys = []
                for k in self.adjusted_fares['implied'].projected.iterkeys():
                    keys.append(k)
                for k in self.adjusted_fares['historical'].projected.iterkeys():
                    keys.append(k)
                latest_proj_week = min(keys)
                earliest_proj_week = max(keys)


                #for i in range(self.final_proj_week, self.num_wks_proj_out + 1):
                for i in range(latest_proj_week, earliest_proj_week + 1):

                    self.adjusted_fares['combined'].projected[i] = dict()
                    self.adjusted_fares['combined'].standard_deviations[i] = dict()

                    if i in self.adjusted_fares['implied'].projected:
                        self.adjusted_fares['combined'].standard_deviations[i]['beg_period'] = self.adjusted_fares['combined'].projected[i]['beg_period'] = self.adjusted_fares['implied'].projected[i]['beg_period']
                        self.adjusted_fares['combined'].standard_deviations[i]['end_period'] = self.adjusted_fares['combined'].projected[i]['end_period'] = self.adjusted_fares['implied'].projected[i]['end_period']
                    else:
                        self.adjusted_fares['combined'].standard_deviations[i]['beg_period'] = self.adjusted_fares['historical'].projected[i]['beg_period'] = self.adjusted_fares['historical'].projected[i]['beg_period']
                        self.adjusted_fares['combined'].standard_deviations[i]['end_period'] = self.adjusted_fares['historical'].projected[i]['end_period'] = self.adjusted_fares['historical'].projected[i]['end_period']

                    #for j in range(self.final_proj_week, i + 1):
                    for j in range(latest_proj_week, i + 1):

                        self.adjusted_fares['combined'].projected[i][j] = self.adjusted_fares['combined'].standard_deviations[i][j] = None


                        if i in self.adjusted_fares['implied'].projected and i in self.adjusted_fares['historical'].projected:
                            if self.adjusted_fares['implied'].projected[i][j] and self.adjusted_fares['historical'].projected[i][j]:
                                self.adjusted_fares['combined'].projected[i][j] = (self.weight_on_imp * self.adjusted_fares['implied'].projected[i][j]) + ( (1-self.weight_on_imp) * self.adjusted_fares['historical'].projected[i][j])

                        if not self.adjusted_fares['combined'].projected[i][j]:
                            if i in self.adjusted_fares['implied'].projected:
                                if self.adjusted_fares['implied'].projected[i][j]:
                                    self.adjusted_fares['combined'].projected[i][j] = self.adjusted_fares['implied'].projected[i][j]

                        if not self.adjusted_fares['combined'].projected[i][j]:
                            if i in self.adjusted_fares['historical'].projected:
                                if self.adjusted_fares['historical'].projected[i][j]:
                                    self.adjusted_fares['combined'].projected[i][j] = self.adjusted_fares['historical'].projected[i][j]


                        if i in self.adjusted_fares['implied'].standard_deviations and i in self.adjusted_fares['historical'].standard_deviations:
                            if self.adjusted_fares['implied'].standard_deviations[i][j] and self.adjusted_fares['historical'].standard_deviations[i][j]:
                                self.adjusted_fares['combined'].standard_deviations[i][j] = (self.weight_on_imp * self.adjusted_fares['implied'].standard_deviations[i][j]) + ( (1-self.weight_on_imp) * self.adjusted_fares['historical'].standard_deviations[i][j])

                        if not self.adjusted_fares['combined'].standard_deviations[i][j]:
                            if i in self.adjusted_fares['implied'].standard_deviations:
                                if self.adjusted_fares['implied'].standard_deviations[i][j]:
                                    self.adjusted_fares['combined'].standard_deviations[i][j] = self.adjusted_fares['implied'].standard_deviations[i][j]

                        if not self.adjusted_fares['combined'].standard_deviations[i][j]:
                            if i in self.adjusted_fares['historical'].standard_deviations:
                                if self.adjusted_fares['historical'].standard_deviations[i][j]:
                                    self.adjusted_fares['combined'].standard_deviations[i][j] = self.adjusted_fares['historical'].standard_deviations[i][j]

            except Exception as err:
                    self.errors.append("Error: route %s_%s, prefs %s, numhighs %s - problem combining historical and implied data sets (%s)" % (self.origin, self.destination, self.prefs.id, self.num_high_days, err))

            self.type = 'combined'


        elif self.weight_on_imp == 1:
            self.type = 'implied'
            self.process()

        else:
            self.type = 'historical'
            self.process()

        #print "Completed in " + `time.time()-start` + " seconds"


    def process(self):

        if self.black_list_error:
            self.previous.type = self.type
            self.previous.hist_movement[self.previous.type] = wkly_fare_movement(self.previous)
            self.previous.hist_movement[self.previous.type].run()
            self.previous.errors.extend(self.previous.hist_movement[self.previous.type].errors)

            self.previous.adjusted_fares[self.previous.type] = apply_change_rates(self.previous)
            self.previous.adjusted_fares[self.previous.type].run(self.previous.base_fares.set, self.previous.hist_movement[self.previous.type])
            self.previous.errors.extend(self.previous.adjusted_fares[self.previous.type].errors)


            # build list of previous projected values
            try:
                previous_final_projections = {}
                for k, v in self.previous.adjusted_fares[self.previous.type].projected.iteritems():
                    previous_final_projections[k] = {'avg_fare': v[self.previous.final_proj_week], 'beg_period': v['beg_period'], 'end_period': v['end_period']}
                #pprint(self.previous_adjusted_fares[self.type].projected)

                # build black out date list
                self.previous.black_list = {}
                for i in self.base_fares.set.iterkeys():
                    for j in range(1, self.max_trip_length+1):
                        try:
                            error = abs((previous_final_projections[i+1]['avg_fare'] / self.base_fares.set[i]['split_trip_lengths'][j]) - 1)
                            if error > self.black_list_error:
                                if i not in self.previous.black_list:
                                    self.previous.black_list[i] = {}
                                ret_beg_period = self.base_fares.set[i]['beg_period'] + datetime.timedelta(weeks = j-1)
                                ret_end_period = self.base_fares.set[i]['end_period'] + datetime.timedelta(weeks = j-1)

                                self.previous.black_list[i][j] = {'trip_length_week': j, 'beg_period': self.base_fares.set[i]['beg_period'], 'end_period': self.base_fares.set[i]['end_period'], 'error': error, 'ret_beg_period': ret_beg_period, 'ret_end_period': ret_end_period}
                        except:
                            pass
            except:
                self.previous.black_list = None

        # generate weekly fare increase estimates
        self.hist_movement[self.type] = wkly_fare_movement(self)
        self.hist_movement[self.type].run()
        self.errors.extend(self.hist_movement[self.type].errors)

        # apply compounded change rate to current values of future departure dates to develop projections
        self.adjusted_fares[self.type] = apply_change_rates(self)
        self.adjusted_fares[self.type].run(self.base_fares.set, self.hist_movement[self.type])
        self.errors.extend(self.adjusted_fares[self.type].errors)


    def find_depart_length_range(self, proj_week):

        depart_length_days = proj_week * 7
        depart_lengths = (depart_length_days, depart_length_days + self.depart_length_width)

        return depart_lengths


class apply_change_rates(projection):

    def __init__(self, inputs):

        self.initialize(inputs)
        self.projected = dict()
        self.standard_deviations = dict()
        self.errors = []
        #self.db = db()

    def run(self, current_fares, wkly_fare_movement):

        try:
            keys = []
            for k in wkly_fare_movement.avg_change.iterkeys():
                keys.append(k)
            max_proj_week = max(keys)

            # if projected changes in fares were cut off due to insufficient data, limit range of projection extrapolation
            if max_proj_week < self.first_proj_week:
                limiter = max_proj_week + 1
                cap = min(self.num_wks_proj_out, limiter)
            else:
                cap = self.num_wks_proj_out


            for i in range(self.final_proj_week, cap + 1):
                try:
                    proj_week = dict()
                    st_dev_week = dict()

                    proj_week['beg_period'] = st_dev_week['beg_period'] = current_fares[i]['beg_period']
                    proj_week['end_period'] = st_dev_week['end_period'] = current_fares[i]['end_period']

                    for j in range (self.final_proj_week, i + 1):
                        try:
                            if current_fares[i]['avg_fare'] == None:
                                current_fares[i]['avg_fare'] = self.replace_null_average(current_fares, i)

                            if i == j:
                                proj_change = regressed_change = 1
                                st_dev = None

                            else:

                                if i > (max_proj_week + 1):
                                    start = max_proj_week + 1
                                else: start = i

                                if j > max_proj_week:
                                    end = max_proj_week
                                else: end = j

                                proj_change = wkly_fare_movement.avg_change[end][start]
                                st_dev = wkly_fare_movement.change_st_dev[end][start]

                                avg_price = wkly_fare_movement.avg_price[end][start]
                                st_dev_avg_price = wkly_fare_movement.st_dev_avg_price[end][start]


                                z_score = (current_fares[i]['avg_fare'] - avg_price) / st_dev_avg_price
                                sign = -1 if proj_change > 1 else 1

                                regressed_change = sign * (z_score * (proj_change-1) * st_dev) + proj_change

                                #print "%s:%s current: %s, average: %s, st_dev: %s,  change: %s, regressed: %s, z-score: %s" % (i,j, current_fares[i]['avg_fare'], avg_price, st_dev_avg_price, proj_change, regressed_change, z_score)

                            if self.regressed:
                                selected_change = regressed_change
                            else:
                                selected_change = proj_change

                            projected_fare = selected_change * current_fares[i]['avg_fare']
                            proj_week[j] = projected_fare
                            st_dev_week[j] = st_dev * projected_fare if st_dev else None

                            #print "%s:%s  proj_change: %s, regressed: %s, current: %s, projected: %s" % (i,j, proj_change, regressed_change, current_fares[i]['avg_fare'], projected_fare)
                        except:
                            proj_week[j] = st_dev_week[j] = None

                    self.projected[i] = proj_week
                    self.standard_deviations[i] = st_dev_week

                except:
                    self.projected[i] = self.standard_deviations[i] = None

        except Exception as err:
            self.projected = {}
            self.errors.append("Error: route %s_%s, prefs %s, numhighs %s, type: %s - problem applying change rates to current prices (%s)" % (self.origin, self.destination, self.prefs.id, self.num_high_days, self.type, err))

        #self.db.db_disconnect()


    def replace_null_average(self, fare, i):
        # sets average fare to neighboring average fare if data is insufficient
        replace_with = None
        if i != self.first_proj_week:
            if (i-1) in fare and (i+1) in fare:
                if fare[i-1]['avg_fare'] and fare[i+1]['avg_fare']:
                    replace_with = sum((fare[i-1]['avg_fare'],fare[i+1]['avg_fare'],))/2
            elif (i+1) in fare:
                if fare[i+1]['avg_fare']:
                    replace_with = fare[i+1]['avg_fare']
        if not replace_with:
            if (i-1) in fare:
                if fare[i-1]['avg_fare']:
                    replace_with = fare[i-1]['avg_fare']

        self.errors.append("proj week %s - Insufficient data to find current average fare, applied neighboring fare values if available" % (i))

        return replace_with


class current_fares(projection):

    def __init__(self, inputs):

        self.initialize(inputs)
        self.set = dict()

    def projection(self):

        self.db_current = db(db='steadyfa_temp_tables')

        for i in range(self.final_proj_week, self.num_wks_proj_out + 1):

            adj_beg_period = self.beg_period + datetime.timedelta(weeks = (i-(self.width_of_avg-1)))
            adj_end_period = self.end_period + datetime.timedelta(weeks = i)

            depart_dates = [(adj_beg_period, adj_end_period)]
            depart_lengths = self.find_depart_length_range(i)

            avg_fare = self.db_current.find_min_sum_stat('Avg', depart_dates, depart_lengths)
            self.set[i] = {'avg_fare': avg_fare, 'beg_period': adj_beg_period, 'end_period': adj_end_period}

            if not self.is_previous:
                split_trip_lengths = {}
                for j in range(self.max_trip_length):
                    trip_lengths = [j*7+1,(j+1)*7]
                    avg_fare = self.db_current.find_min_sum_stat('Avg', depart_dates, depart_lengths, trip_lengths)
                    split_trip_lengths[j+1] = avg_fare
                    self.set[i]['split_trip_lengths'] = split_trip_lengths

        self.db_current.db_disconnect()


    def act_avg(self, db, final_proj_week, first_proj_week, beg_period, end_period, num_high_days, route, flight_type, prefs):

        self.set = {'act_fare': dict(), 'beg_period': beg_period, 'end_period': end_period, 'num_high_days': num_high_days, 'route': route, 'flight_type': flight_type, 'prefs': prefs}

        for i in range(final_proj_week, first_proj_week + 1):

            depart_dates = [(beg_period, end_period)]
            depart_lengths = self.find_depart_length_range(i)

            #avg_fare = db.find_min_sum_stat('Avg', num_high_days, depart_dates, depart_lengths)
            avg_fare = db.find_min_sum_stat('Avg', depart_dates, depart_lengths)
            self.set['act_fare'][i] = avg_fare


class wkly_fare_movement(projection):

    # calculates a series of CAGRs, one for each week before departure date
    def __init__(self,inputs):

        self.initialize(inputs)

        self.change_log = []
        self.avg_change = dict()
        self.raw_change_st_dev = dict()
        self.change_st_dev = dict()
        self.avg_price = dict()
        self.st_dev_avg_price = dict()

        self.errors = []

        self.db_movement = db(db='steadyfa_temp_tables')

    def run(self):
        try:
            if self.type == "implied" and self.seasonality_adjust:

                def calc_adjustment(k):

                    first_look_back = self.stats_on_mins(k, 0)
                    last_look_back = self.stats_on_mins(k, self.num_per_look_back - 1)

                    change = (first_look_back['avg_fare'] / last_look_back['avg_fare'])# **(1/(self.num_per_look_back-1)))
                    implied_change_adjustment = change

                    return implied_change_adjustment

                change_adjustment_bank = dict()
                for i in range(self.final_proj_week,(self.first_proj_week+1)):
                    try:
                        # find general implied trend
                        change_adjustment_bank[i] = calc_adjustment(i)
                    except:
                        change_adjustment_bank[i] = None
                #pprint(change_adjustment_bank)


            stats_on_mins_bank = {}
            for i in range(self.final_proj_week,(self.first_proj_week+2)):
                stats_on_mins_bank[i] = {}
                for j in range(self.num_per_look_back):
                    stats_on_mins_bank[i][j] = self.stats_on_mins(i,j)
            #pprint(stats_on_mins_bank)
            #print (stats_on_mins_bank)

            for i in range(self.final_proj_week,(self.first_proj_week+1)):
                for j in range(self.num_per_look_back):
                    for k in range((i+1), (self.first_proj_week+2)):
                        current = stats_on_mins_bank[i][j]
                        per_prior = stats_on_mins_bank[k][j]
                        #current = self.stats_on_mins(i,j)
                        #per_prior = self.stats_on_mins(k,j)

                        #print "--- i: %s, k: %s, perback: %s, type: %s" % (i, k, j, self.type)
                        #print "current: %s" % (current)
                        #print "prior: %s" % (per_prior)

                        if self.type == "implied" and self.seasonality_adjust:
                            short_bank = []
                            for c in change_adjustment_bank.iterkeys():
                                #if c >= i and change_adjustment_bank[c]:
                                if change_adjustment_bank[c]:
                                    short_bank.append(change_adjustment_bank[c])
                            #print short_bank
                            #print "%s - %s" % (sum(short_bank), len(short_bank))
                            try:
                                implied_change_adjustment = (sum(short_bank)/len(short_bank))**(1.00/(self.num_per_look_back-1))
                                #print implied_change_adjustment
                            except:
                                implied_change_adjustment = 1
                        else:
                            implied_change_adjustment = 1

                        if current['avg_fare'] and per_prior['avg_fare'] and implied_change_adjustment:
                            change = current['avg_fare'] / (per_prior['avg_fare'] / implied_change_adjustment)
                        else: change = None

                        self.change_log.append({'depart_length': i, 'look_back_per': j, 'proj_week': k, 'current_avg': current['avg_fare'], 'per_prior_avg': per_prior['avg_fare'], 'change': change, 'adj_beg_period': current['adj_beg_period'], 'adj_end_period': current['adj_end_period']})

                self.avg_change[i] = dict()
                self.raw_change_st_dev[i] = dict()

                # this is used to alter change values for fares that are over or under the historical average
                self.avg_price[i] = dict()
                self.st_dev_avg_price[i] = dict()


                for j in range((i+1), (self.first_proj_week+2)):

                    stats_1 = self.change_log_stats('per_prior_avg', i, j)
                    #self.avg_price[i][j] = stats_1[0]
                    #self.st_dev_avg_price[i][j] = stats_1[1]
                    stats_2 = self.change_log_stats('change', i, j)
                    #print "%s:%s - %s" % (i,j,stats_2)
                    if self.ensure_suf_data:
                        # raise error if believed insufficient data to generate reliable projection inputs
                        if i != 11 and j != 11: # historically no data collected for week 11, preventing change rates from being estimated here
                            if stats_2[2] < floor(self.ensure_suf_data * (self.num_per_look_back)):

                                self.avg_price[i][j] = None
                                self.st_dev_avg_price[i][j] = None
                                self.avg_change[i][j] = None
                                self.raw_change_st_dev[i][j] = None
                                #print 'User defined insufficient data: %s:%s - %s - %s data points available, %s required' % (i, j, self.type, stats_2[2], floor(self.ensure_suf_data * (self.num_per_look_back)))
                                self.errors.append('User defined insufficient data: %s:%s - %s - %s data points available, %s required' % (i, j, self.type, stats_2[2], floor(self.ensure_suf_data * (self.num_per_look_back))))

                            else:
                                self.avg_price[i][j] = stats_1[0]
                                self.st_dev_avg_price[i][j] = stats_1[1]
                                self.avg_change[i][j] = stats_2[0]
                                self.raw_change_st_dev[i][j] = stats_2[1]
                        else:
                            self.avg_price[i][j] = None
                            self.st_dev_avg_price[i][j] = None
                            self.avg_change[i][j] = None
                            self.raw_change_st_dev[i][j] = None

                    else:
                        self.avg_price[i][j] = stats_1[0]
                        self.st_dev_avg_price[i][j] = stats_1[1]
                        self.avg_change[i][j] = stats_2[0]
                        self.raw_change_st_dev[i][j] = stats_2[1]


            #for i in self.change_log:
            #    print "%s - %s - %s - %s - %s - %s - %s - %s" % (i['proj_week'], i['look_back_per'], i['change'], i['adj_beg_period'], i['adj_end_period'], i['current_avg'], i['depart_length'], i['per_prior_avg'])

            # truncate the empty dictionaries where data was insufficient to record a value
            self.avg_change = self.truncate_empty_data_set(self.avg_change)
            self.raw_change_st_dev = self.truncate_empty_data_set(self.raw_change_st_dev)
            self.avg_price = self.truncate_empty_data_set(self.avg_price)
            self.st_dev_avg_price = self.truncate_empty_data_set(self.st_dev_avg_price)

            # replace null values with neighboring values
            self.avg_change = self.format_change_set(self.avg_change, replace=True)
            self.raw_change_st_dev = self.format_change_set(self.raw_change_st_dev, replace=True)
            self.avg_price = self.format_change_set(self.avg_price, replace=True)
            self.st_dev_avg_price = self.format_change_set(self.st_dev_avg_price, replace=True)

            for i, j in self.avg_change.iteritems():
                self.change_st_dev[i] = dict()
                for k, v in j.iteritems():

                    # prevents each period's change from falling below a minimum allowed level
                    if self.min_change:
                        if v < self.min_change:
                            self.avg_change[i][k] = self.min_change

                    # remove effect of direction and magnitude of fare change from standard deviation
                    self.change_st_dev[i][k] = self.raw_change_st_dev[i][k] / self.avg_change[i][k]

            # then smooth standard deviation values by averaging each periods by neighboring values
            #self.change_st_dev = self.format_change_set(self.change_st_dev, replace=False)


        except Exception as err:
            self.errors.append("Error: route %s_%s, prefs %s, numhighs %s, type: %s, depart_length: %s - problem finding historical fare averages/st devs (%s)" % (self.origin, self.destination, self.prefs.id, self.num_high_days, self.type, i, err))


        finally:
            self.db_movement.db_disconnect()


    def truncate_empty_data_set(self, set):

        new_set = dict()
        for i, j in set.iteritems():
            temp_dict = dict()
            for k, v in j.iteritems():
                if v:
                    temp_dict[k] = v
            if temp_dict:
                new_set[i] = temp_dict

        drop_list = []
        for i in new_set.iterkeys():
            # this prevents adding keys after long gaps in which there was no data,
            # which would prevent projections from generating any results
            if (i-1) >= self.final_proj_week and (i-1) != 11:
                if (i-1) not in new_set:
                    drop_list.append(i)
                    #del new_set[i]

        for i in drop_list:
            del new_set[i]
        #print new_set

        if 12 in new_set and 10 in new_set:
            new_set[11] = dict()
            new_set[11][12] = None
            for k in new_set[12].iterkeys():
                if k in new_set[10]:
                    new_set[11][k] = None

            for k in new_set.iterkeys():
                if k < 11:
                    if 10 in new_set[k] or k == 10  :
                        new_set[k][11] = None

        return new_set


    def format_change_set(self, set, replace=True):
        """
        @param replace: if true, set empty values to average of neighboring values, if false, set each value to the average of itself and neighboring values
        """
        #pprint(set)
        bank = []
        for i in set.iterkeys():
            bank.append(i)
        first = min(bank)
        last = max(bank)

        for i, j in set.iteritems():
            for k, v in j.iteritems():
                if v and replace:
                    set[i][k] = v
                else:
                    set[i][k] = self.process_format(first, last, set, i, k, replace)

        #pprint(set)
        return set


    def process_format(self, first, last, set, i, k, replace):
        try:
            group = None

            if replace and k == 11:
                if (k - i) == 1 and i != last:
                    group = [set[i][k], set[i][k+1]]
                elif (k - i) == 1 and i == last:
                    group = [set[i][k], set[i-1][k], set[i-1][k-1]]
                elif k == (last+1):
                    group = [set[i][k-1], set[i][k]]
                else:
                    group = [set[i][k-1], set[i][k], set[i][k+1]]

            if not group:
                if i == first and (k - i) != 1:
                    group = [set[i][k], set[i+1][k]]
                elif i != first and (k - i) != 1:
                    group = [set[i-1][k], set[i][k], set[i+1][k]]
                elif i != first and (k - i) == 1:
                    group = [set[i][k], set[i-1][k]]
                else:
                    group = [set[i][k]]

            valid = []
            for i in group:
                if i:
                    valid.append(i)

            return sum(valid)/len(valid)

        except Exception as err:
            self.errors.append('i: %s, k: %s - error format set change - %s' % (i,k,err))
            return None


    def test_suf_data(self, depart_length, category):
        """
        @summary: prevents script from generating projections where data is too sparse to confidently price steadyfares
        @param category: the key in change_log to analyze, e.g. 'change' and 'current_std_dev'
        @param ensure_suf_data: the share of total possible data points that must be present in list to determine if available data is sufficient, e.g. 0.5
        """
        count = 0
        for j in self.change_log:
            if j['depart_length'] == depart_length and j[category]:
                count += 1

        #print"proj_week: %s, %s: %s : %s" % (depart_length, category, count, floor(self.ensure_suf_data * (self.num_per_look_back)))
        if count < floor(self.ensure_suf_data * (self.num_per_look_back)):
            raise Exception('User defined insufficient data: %s- %s data points available, %s required' % (category, count, floor(self.ensure_suf_data * (self.num_per_look_back))))


    def remove_dec_vals(self, list, min):
        """
        @attention: this is likely not needed as of 12/6/2012
        @summary: this removes rates of change that decrease value over a period, while preventing subsequent periods from over stating a rate of change due to a previous period's increased value
        """
        marker = min
        for i in sorted(list.keys(), reverse=True):
            if not marker < min:
                if list[i] < min:
                    marker *= list[i]
                    list[i] = min

            else:
                marker *= list[i]
                if not marker < min:
                    list[i] = marker
                    marker = min
                else: list[i] = min
        return list


    def change_log_stats(self, find, depart_length, proj_week):
        # sets an average change value and standard deviation
        items = []
        for j in self.change_log:
            if (j['depart_length'] == depart_length) and (j['proj_week'] == proj_week):
                if j[find]:
                    items.append(j[find])

        if items:
            average = sum(items)/len(items)
            st_dev = standard_deviation(items)

        else:
            average = None
            st_dev = None

        return (average, st_dev, len(items))


    def stats_on_mins(self, proj_week, look_back_per):

        adj_beg_period = self.beg_period + datetime.timedelta(weeks = -look_back_per)
        adj_end_period = self.end_period + datetime.timedelta(weeks = -look_back_per)

        depart_dates = self.def_depart_dates(proj_week, adj_beg_period, adj_end_period)

        depart_lengths = self.find_depart_length_range(proj_week)


        # this prevents blacked-out dates from factoring into the projections
        if self.is_previous is False and self.black_list_error and self.flight_type == 'rt':
            if proj_week in self.previous.black_list:
                trip_lengths = self.previous.black_list[proj_week].keys()

                if len(trip_lengths) == self.max_trip_length:
                    bank = -1
                else:
                    bank = []
                    for index, i in enumerate(trip_lengths):
                        if index == 0 and i > 1:
                            bank.append([1, (i-1)*7-1])
                        if index > 0:
                            if ((trip_lengths[index-1])*7) < (i-1)*7-1:
                                bank.append([(trip_lengths[index-1])*7, (i-1)*7-1])
                    if trip_lengths[-1] < self.max_trip_length:
                        bank.append([trip_lengths[-1]*7, self.max_trip_length*7])
            else:
                bank = None
        else:
            bank = None


        avg_fare = self.db_movement.find_min_sum_stat('Avg', depart_dates, depart_lengths, bank)
        #print "%s - %s, %s" % (avg_fare, bank, trip_lengths)
        return {'avg_fare': avg_fare, 'adj_beg_period': adj_beg_period, 'adj_end_period': adj_end_period, 'proj_week': proj_week, 'beg_dep_date': depart_dates[0][0], 'end_dep_date': depart_dates[0][1]}



    def def_depart_dates(self, proj_week, adj_beg_period, adj_end_period):
        depart_dates = []
        for i in range(self.width_of_avg):
            adj_beg_period = adj_beg_period + datetime.timedelta(weeks = -i)
            adj_end_period = adj_end_period + datetime.timedelta(weeks = -i)
            if (self.type == 'implied'):
                adj_beg_period = adj_beg_period + datetime.timedelta(weeks = proj_week)
                adj_end_period = adj_end_period + datetime.timedelta(weeks = proj_week)
            depart_dates.append((adj_beg_period, adj_end_period))
        return depart_dates



class projection_set(object):

    def __init__(self, inputs, record=False, update_projection_prep=False):

        self.inputs = inputs

        self.update_projection_prep = update_projection_prep
        if not self.update_projection_prep:

            self.set = []
            self.record = record
            if self.record:
                self.setup_temp_tables()


    def update_mins_table(self):
        # find minimum fares
        try:
            self.db = db(cursorclass=MySQLdb.cursors.DictCursor, db='steadyfa_temp_tables')
            self.db.find_mins(self.inputs.origin, self.inputs.destination, self.inputs.earliest_source_date, self.inputs.start_date, self.inputs.prefs, self.inputs.flight_type, self.inputs.num_high_days, self.inputs.max_trip_length, self.update_projection_prep)
            self.db.db_disconnect()
        except Exception as err:
            #self.errors.append("Error: route %s_%s, prefs %s - problem generating set of minimum historical fares (%s)" % (self.inputs.origin, self.inputs.destination, self.inputs.prefs.id, err))
            print "Error: route %s_%s, prefs %s - problem generating set of minimum historical fares (%s)" % (self.inputs.origin, self.inputs.destination, self.inputs.prefs.id, err)

    def incremental_record(self):
        self.insert_projection_data('proj_fare', 'temp_projections')
        self.insert_projection_data('st_dev', 'temp_standard_deviations')
        if self.inputs.black_list_error:
            self.insert_projection_data('black_list', 'temp_black_list')
        self.set = []

    def complete_route_set(self):
        # loops though all complete_route for each prefs combination
        start = time.time()
        geographies = ['us', 'eu']
        for i in geographies:
            self.inputs.geography = i
            self.loop_routes(self.complete_route)
        print "Completed in " + `time.time()-start` + " seconds"


    def route_set_no_prefs(self):
        # loops though all routes for but does not cycle prefs combinations
        start = time.time()
        geographies = ['us', 'eu']
        for i in geographies:
            self.inputs.geography = i
            self.loop_routes(self.loop_num_high_days)
        print "Completed in " + `time.time()-start` + " seconds"


    def complete_route(self):
        # loops through all combinations of prefs and num_high_day
        self.loop_prefs(self.loop_num_high_days)


    def loop_routes(self, action='final'):

        self.db_route = db()

        hubs = self.db_route.sel_crit('all','hubs_%s' % (self.inputs.geography),['Airport'],{})
        destinations = self.db_route.sel_crit('all','destinations_%s' % (self.inputs.geography),['Airport'],{})

        for i in hubs:
            for j in destinations:

                self.inputs.origin = i[0]
                self.inputs.destination = j[0]
                self.inputs.route = '%s_%s' % (self.inputs.origin, self.inputs.destination)

                if self.update_projection_prep:
                    if action == 'final':
                        self.build_entry()
                    else:
                        action()
                else:
                    if action == 'final':
                        self.set.append(self.build_entry())
                        if self.record:
                            self.incremental_record()
                    else:
                        action()

        self.db_route.db_disconnect()


    def loop_prefs(self, action='final'):

        for i in range(len(self.inputs.prefs.id_list)):
            self.inputs.prefs.set_inputs_by_id(i)

            if self.update_projection_prep:
                if action == 'final':
                    self.build_entry()
                else:
                    action()
            else:
                if action == 'final':
                    self.set.append(self.build_entry())
                    if self.record:
                        self.incremental_record()
                else:
                    action()

    def loop_num_high_days(self, action='final'):

        if self.update_projection_prep:
            if action == 'final':
                self.build_entry()
            else:
                action()
        else:
            high_days = weekday_pairs(self.inputs.flight_type)
            for i in high_days.pair_ids.iterkeys():
                self.inputs.num_high_days = i

                if action == 'final':
                    self.set.append(self.build_entry())
                    if self.record:
                        self.incremental_record()
                else:
                    action()


    def build_entry(self):

        if self.update_projection_prep:
            self.update_mins_table()
            print 'route: %s, prefs id: %s, full num_high_days set' % (self.inputs.route, self.inputs.prefs.id)
        else:
            item = projection(self.inputs)
            print 'route: %s, prefs id: %s, high days: %s' % (self.inputs.route, self.inputs.prefs.id, self.inputs.num_high_days)

            entry = dict()
            entry['num_high_days'] = item.num_high_days
            entry['prefs'] = item.prefs.id
            entry['route'] = item.route
            entry['flight_type'] = item.flight_type
            entry['proj_fare'] = item.adjusted_fares[item.type].projected
            entry['st_dev'] = item.adjusted_fares[item.type].standard_deviations
            entry['errors'] = item.errors
            if self.inputs.black_list_error:
                entry['black_list'] = item.previous.black_list
            item = None

            return entry


    def replace_current_records_combo(self):
        self.replace_current_records('projections')
        self.replace_current_records('standard_deviations')
        self.replace_current_records('black_list')


    def replace_current_records(self, table):

        # archive existing tables and replace them
        self.db = db()

        time = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
        self.db.rename_and_archive('steadyfa_sf_projection_archive', 'steadyfa_temp_tables', table, time)

        self.db.db_disconnect()


    def setup_temp_tables(self):

        self.db = db(db='steadyfa_temp_tables')

        # build projection and standard deviation table
        def build_columns(self, type):
            columns = {'route': 'VARCHAR(8)', 'flight_type': 'VARCHAR(4)', 'num_high_days': 'INT(1)', 'prefs': 'INT(3)', 'proj_week': 'INT(3)', 'beg_period': 'DATE', 'end_period': 'DATE'}

            if type == "black_list":
                columns['error'] = 'DOUBLE'
                columns['ret_beg_period'] = 'DATE'
                columns['ret_end_period'] = 'DATE'
                columns['trip_length_week'] = 'INT'
            else:
                for i in range(self.inputs.final_proj_week, self.inputs.first_proj_week + 1):
                    columns['%s' % (i,)] = 'DOUBLE'

            return columns

        columns_fares = build_columns(self, 'proj_fare')
        columns_st_devs = build_columns(self, 'st_dev')
        self.db.replace_existing_table('temp_projections', columns_fares)
        self.db.replace_existing_table('temp_standard_deviations', columns_st_devs)

        if self.inputs.black_list_error:
            columns_black_list = build_columns(self, 'black_list')
            self.db.replace_existing_table('temp_black_list', columns_black_list)

        self.db.db_disconnect()


    def insert_projection_data(self, type, table):
        #insert projection data into temp tables
        self.db_insert = db(db='steadyfa_temp_tables')

        def insert_line(values, data_set):
            for k, v in data_set.iteritems():
                if v == None:
                    values['%s' % (k,)] = ('NULL')
                else:
                    try:
                        float(v)
                        values['%s' % (k,)] = ('%.2f' % (v,))
                    except:
                        values['%s' % (k,)] = ("'%s'" % (v,))
            self.db_insert.insert_data(table, values)

        for i in self.set:
            for j in i[type].iterkeys():
                values = {'route': "'%s'" % (i['route'],), 'flight_type': "'%s'" % (i['flight_type'],), 'num_high_days': i['num_high_days'], 'prefs': i['prefs'], 'proj_week': j}
                if type is "black_list":
                    for k in i[type][j].iterkeys():
                        insert_line(values, i[type][j][k])
                else:
                    insert_line(values, i[type][j])

        self.db_insert.db_disconnect()

        """
        values = {'route': "'%s'" % (i['route'],), 'flight_type': "'%s'" % (i['flight_type'],), 'num_high_days': i['num_high_days'], 'prefs': i['prefs'], 'proj_week': j}
        for k, v in i[type][j].iteritems():
            if v == None:
                values['%s' % (k,)] = ('NULL')
            else:
                try:
                    float(v)
                    values['%s' % (k,)] = ('%.2f' % (v,))
                except:
                    values['%s' % (k,)] = ("'%s'" % (v,))
        self.db_insert.insert_data(table, values)
        """

if __name__ == "__main__":
    start_full = time.time()

    db_date = db(db='steadyfa_projection_prep')
    recent_add_date = db_date.find_simple_sum_stat('SFOMAD', 'MAX', 'date_collected')
    db_date.db_disconnect()

    # single projection set
    inputs = search_inputs(purpose='projection', start_date=recent_add_date)
    example = projection(inputs)
    pprint(example.adjusted_fares[example.type].projected)
    pprint(example.adjusted_fares[example.type].standard_deviations)
    if inputs.black_list_error:
        pprint(example.previous.black_list)
    pprint(example.errors)
    """
    # build multiple projection sets, covering each potential number of high-priced days and user preferences
    inputs = search_inputs(purpose='projection')
    example = projection_set(inputs, record=True, update_projection_prep=False)
    example.complete_route_set()
    pprint(example.set)
    example.replace_current_records_combo()
    """
    print "Completed in " + `time.time()-start_full` + " seconds"