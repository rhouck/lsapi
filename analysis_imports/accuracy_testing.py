 #!/usr/bin/env python
from projection import *
from projection import current_fares
from functions import *
from pprint import pprint
import itertools
from decimal import Decimal
import time

class projection_analysis(current_fares):

    def __init__(self, inputs, source_projected='temp_projections', source_analyzed='temp_accuracy_testing'):

        self.inputs = inputs
        self.db = db(db='steadyfa_temp_tables')
        self.db_mins = db(db='steadyfa_projection_prep')
        self.errors = []
        self.projected = import_table(source_projected, db_name='steadyfa_temp_tables')
        if self.db.does_table_exist(source_analyzed):
            self.summary = data_set_analysis(import_table(source_analyzed, db_name='steadyfa_temp_tables'))

    def run(self, replace=True):
        if self.projected:
            try:
                start = time.time()
                self.gen_actual_set()
                self.find_proj_over_act()
                self.build_proj_over_act_table(replace)
                self.summary = data_set_analysis(import_table('temp_accuracy_testing', db_name='steadyfa_temp_tables'))
                self.db.db_disconnect()
                self.db_mins.db_disconnect()
                print "Completed in " + `time.time()-start` + " seconds"
            except:
                print "Problem analyzing projections"

    def build_proj_over_act_table(self, replace):
        if self.proj_over_act:
            #print "should we build? - table exists is: %s,    replace is : %s" % (self.db.does_table_exist('temp_accuracy_testing'), replace)
            if not self.db.does_table_exist('temp_accuracy_testing') or replace:
                columns = {'route': 'VARCHAR(8)', 'flight_type': 'VARCHAR(4)', 'prefs': 'INT(3)', 'proj_week': 'INT(1)', 'num_high_days': 'INT(1)', 'beg_period': 'DATE', 'end_period': 'DATE'}
                proj_week_range = []
                """
                for i in self.proj_over_act:
                    if i['proj_week'] not in proj_week_range:
                        proj_week_range.append(i['proj_week'])
                for i in proj_week_range:
                    columns['%s' % (i,)] = 'DOUBLE'
                """
                for i in range(self.inputs.final_proj_week, self.inputs.first_proj_week + 1):
                    columns['%s' % (i,)] = 'DOUBLE'
                self.db.replace_existing_table('temp_accuracy_testing', columns)

            #insert projection data into temp_proj_over_act table
            for i in self.proj_over_act:
                values = {'route': "'%s'" % (i['route'],), 'flight_type': "'%s'" % (i['flight_type'],), 'prefs': i['prefs'], 'proj_week': i['proj_week'], 'num_high_days': i['num_high_days'], 'beg_period': "'%s'" % (i['beg_period']), 'end_period': "'%s'" % (i['end_period'])}
                for k, v in i['quotients'].iteritems():
                    values['%s' % (k,)] = v
                self.db.insert_data('temp_accuracy_testing', values)


    def find_proj_over_act(self):
        # divide all projected fares by actual fares where available, return set of quotients
        self.proj_over_act = []

        for i in self.actual_set:
            base = {'beg_period': i['beg_period'], 'end_period': i['end_period'], 'num_high_days': i['num_high_days'], 'route': i['route'], 'flight_type': i['flight_type'], 'prefs': i['prefs']}
            corresp_proj = find_sub_index_dict(self.projected, base)
            quotients = dict()
            for k, v in i['act_fare'].iteritems():
                if type(v) is float:
                    try:
                        quotients[`k`] = corresp_proj[1][`k`] / v
                    except Exception as err:
                        self.errors.append("Error finding     'projection' to 'actual' ratio: %s" % (err))
            base['quotients'] = quotients
            base['proj_week'] = corresp_proj[1]['proj_week']
            self.proj_over_act.append(base)


    def gen_actual_set(self):
        # build inputs for finding actual price data
        self.actual_set = []
        for index, i in enumerate(self.projected):
            print "route: %s, prefs id: %s - finding actual fares for row: %s" % (self.inputs.route, self.inputs.prefs.id, index)
            proj_weeks = []
            for k in i.iterkeys():
                if k.isdigit():
                    if i[k]:
                        proj_weeks.append(int(k))
            final_proj_week =  min(proj_weeks)
            first_proj_week =  max(proj_weeks)

            # find minimum fares
            split_route = str.split(i['route'],'_')
            #prefs = preferences(i['flight_type'])
            #prefs.set_inputs_by_id(i['prefs'])
            try:
                self.db_mins.pull_mins(split_route[0], split_route[1], i['beg_period'] + datetime.timedelta(weeks = -(first_proj_week+2)), i['beg_period'] + datetime.timedelta(weeks = 2), i['flight_type'], self.inputs.max_trip_length, i['prefs'], i['num_high_days'])
                #self.db.find_mins(split_route[0], split_route[1], i['beg_period'] + datetime.timedelta(weeks = -(first_proj_week+2)), i['beg_period'] + datetime.timedelta(weeks = 2), prefs, i['flight_type'], i['num_high_days'], self.inputs.max_trip_length)
            except Exception as err:
                self.errors.append("Error: route %s_%s, prefs %s, numhighs %s, flight_type: %s - problem generating set of minimum historical fares (%s)" % (split_route[0], split_route[1], i['prefs'], i['num_high_days'], i['flight_type'], err))

            actual = current_fares(self.inputs)
            actual.act_avg(self.db_mins, final_proj_week, first_proj_week, i['beg_period'], i['end_period'], i['num_high_days'], i['route'], i['flight_type'], i['prefs'])
            #self.db.drop_existing('minimums_%s' % (i['num_high_days']))
            self.actual_set.append(actual.set)


class data_set_analysis(object):

    def __init__(self, input):

        self.input = list(input)

    def select_subset(self, sample_size):

        new_set = []
        for i in range(sample_size):
            if len(self.input) > 0:
                rand = randint(0, len(self.input)-1)
                new_set.append(self.input.pop(rand))
        self.input = new_set


    def find_uniques(self,keys):
        # provide list of dictionary keys to filter by (similar to 'group by' in mysql)
        bank = []
        for i in self.input:
            group = dict()
            if len(keys) == 1:
                group[keys[0]] = i[keys[0]]
            else:
                for j in keys:
                    group[j] = i[j]
            bank.append(group)
        bank.sort()
        return list(bank for bank,_ in itertools.groupby(bank))


    def group_data_on(self, where, on_distance=False, on_category=False):
        """
        @attention: if on_category is false, then assumes column names are numbers and groups accordingly,
                    otherwise if on_category is true it groups columns where data is float/double type
        """
        bank = self.find_uniques(where)
        self.grouped_data = []
        for index, i in enumerate(bank):
            entry = dict(i.items())
            for j in self.input:
                if all(n in j.items() for n in i.items()):
                    for k, v in j.iteritems():
                        if on_category:
                            if type(v) is float and k not in entry:
                                entry[k] = [v]
                            elif type(v) is float and k in entry:
                                entry[k].append(v)
                        else:
                            if k.isdigit():
                                if on_distance:
                                    column = str(j['proj_week']- int(k))
                                else:
                                    column = k

                                #if int(column) > 10:
                                #    print '%s: %s   (%s)' % (column, v, type(v))

                                if type(v) is float and column not in entry:
                                    entry[column] = [v]
                                elif type(v) is float and column in entry:
                                    entry[column].append(v)

            self.grouped_data.append(entry)

        return self.grouped_data

class summarize_grouped_data(object):

    def __init__(self, grouped_data):
        self.grouped_data = grouped_data


    def show_stats_where(self, where, week=False):
        if self.stat_set:
            set = find_sub_index_dict(self.stat_set, where, loop=True)
            format_set = []
            if set:
                for i in set:
                    if week:
                        format_set.append(i[1][str(week)])
                    else: format_set.append(i[1])
                    return format_set
            return "Searched items not in stat_set"
        else:
            return "No summary statistics generated: run 'full_stats'"


    def full_stats(self, on_exercise=False):
        functions = {'Avg': self.calc_avg, 'St_Dev': self.calc_st_dev, 'Med': self.calc_med, 'Min': self.calc_min, 'Max': self.calc_max}
        if on_exercise:
            functions['percent_exercised'] = self.percent_exercised
        self.stat_set = self.loop_set(functions)
    def avg(self):
        return self.loop_set({'Avg': self.calc_avg})
    def st_dev(self):
        return self.loop_set({'St_Dev': self.calc_st_dev})
    def med(self):
        return self.loop_set({'Med': self.calc_med})
    def min(self):
        return self.loop_set({'Min': self.calc_min})
    def max(self):
        return self.loop_set({'Max': self.calc_max})


    def loop_set(self, stats):
        set = []
        for i in self.grouped_data:
            entry = dict()
            for k, v in i.iteritems():
                if type(v) is list:
                #if str(k).isdigit():
                    if len(v) > 0:
                        entry[k] = dict()
                        for key in stats:
                            # ensures that 'percent_exercised' is only applied to the 'amt_in_money' category of option pricing anlaysis
                            if key == 'percent_exercised':
                                if k == 'amt_in_money':
                                    entry[k][key] = stats[key](v)
                            else: entry[k][key] = stats[key](v)
                else:
                    entry[k] = i[k]
            set.append(entry)
        return set


    def calc_avg(self, v):
        return sum(v)/len(v)
    def calc_st_dev(self, v):
        return standard_deviation(v)
    def calc_med(self, v):
        return median(v)
    def calc_min(self, v):
        return min(v)
    def calc_max(self, v):
        return max(v)
    def percent_exercised(self, v):
        return '%.2f' % (1-(Decimal(v.count(0)) / Decimal(len(v))))

if __name__ == "__main__":

    inputs = search_inputs(purpose='projection')
    example = projection_analysis(inputs)
    example.run()
    example.summary.group_data_on(['prefs'], on_distance=True)
    example.summary.stats = summarize_grouped_data(example.summary.grouped_data)
    example.summary.stats.full_stats()
    #pprint(example.summary.stats.stat_set)
    pprint(example.summary.stats.show_stats_where({'prefs': 0}, week=False))
    #pprint(example.errors)

