#!/usr/bin/env python

from functions import *
from projection import *
from accuracy_testing import data_set_analysis

class aggregate_search_summaries(projection_set):

    def __init__(self, inputs=None, source='temp_options', record=False):

        if inputs:
            self.inputs = inputs
        else:
            self.inputs = search_inputs(purpose='projection')

        self.source = source

        self.record = record
        if self.record:
            self.setup_temp_table()

        # this input is from projection_set and not relevant here
        self.update_projection_prep = False

        self.set = []
        self.errors = []


    def incremental_record(self):
        self.db = db(db='steadyfa_temp_tables')
        for i in self.set:
            #insert search summary data into temp_search_summary table
            values = {'route': ("'%s'" % (i['route'],)), 'flight_type': ("'%s'" % (i['flight_type'],)), 'prefs': i['prefs']}
            values['recent_peak_fare'] = ("'%s'" % (i['recent_peak_fare'],)) if i['recent_peak_fare'] else "NULL"
            values['previous_savings'] = ("'%s'" % (i['previous_savings'],)) if i['previous_savings'] else "NULL"
            values['popular_purchase'] = ("'%s'" % (i['popular_purchase'],)) if i['popular_purchase'] else "NULL"
            values['price_swings'] = ("'%s'" % (i['price_swings'],)) if i['price_swings'] else "NULL"
            self.db.insert_data('temp_search_summary', values)
        self.db.db_disconnect()

        self.set = []


    def display_single_search(self):
        criteria = {'route': self.inputs.route, 'flight_type': self.inputs.flight_type, 'prefs': self.inputs.prefs.id}

        db_dict = db(cursorclass=MySQLdb.cursors.DictCursor)
        entry = db_dict.sel_crit('one', 'search_summary', ['*'], criteria)
        db_dict.db_disconnect()
        # this handles situations when no customer education data is availalbe
        if not entry:
            entry = dict(criteria.items())
            entry['previous_savings'] = None
            entry['recent_peak_fare'] = None
            entry['popular_purchase'] = None
            entry['price_swings'] = None
            entry['id'] = None

        entry['review'] = self.pull_rand_review()
        return entry


    def pull_rand_review(self):
        data = import_table('cust_reviews')
        selected = data[randint(0, len(data)-1)]
        return "%s - %s" % (selected['cust_name'], selected['review'])


    def complete_route(self):
        # loops through all combinations of prefs, differs from "projection_set" in that it does not loop through "num_high_days"
        self.loop_prefs()


    def build_entry(self):

        print 'route: %s, prefs id: %s, flight_type: %s' % (self.inputs.route, self.inputs.prefs.id, self.inputs.flight_type)

        item = search_summary(self.inputs, source=self.source)
        item.run()

        entry = dict()
        entry['prefs'] = item.prefs.id
        entry['route'] = item.route
        entry['flight_type'] = item.flight_type
        entry.update(item.summary)
        self.errors.extend(item.errors)

        item = None
        return entry


    def setup_temp_table(self):

            self.db = db(db='steadyfa_temp_tables')
            columns = {'route': 'VARCHAR(8)', 'flight_type': 'VARCHAR(4)', 'prefs': 'INT(3)', 'recent_peak_fare': 'TEXT', 'previous_savings': 'TEXT', 'popular_purchase': 'TEXT', 'price_swings': 'TEXT'}
            self.db.replace_existing_table('temp_search_summary', columns)
            self.db.db_disconnect()



class search_summary(search_inputs):

    def __init__(self, inputs, source, weeks_back=4):
        self.initialize(inputs)
        #self.db = db()
        self.errors = []

        self.num_high_days = None
        self.source = source
        if weeks_back:
            # sets the length of window to find historical max, etc
            self.weeks_back = weeks_back
            self.earliest_source_date = self.format_as_date(datetime.timedelta(weeks = -self.weeks_back), self.start_date)
        else:
            self.weeks_back = 'several'


    def run(self):
        self.matches = find_sub_index_dict(import_table(self.source), {'route': self.route, 'prefs': self.prefs.id, 'flight_type': self.flight_type}, loop=True)
        self.gen_min_set()
        self.recent_peak_fare = self.find_recent_peak_fare()
        self.previous_savings = self.find_previous_savings()
        self.popular_purchase = self.find_popular_purchase()
        self.price_swings = self.find_price_swings()
        self.summary = {'recent_peak_fare': self.recent_peak_fare, 'previous_savings': self.previous_savings, 'popular_purchase': self.popular_purchase, 'price_swings': self.price_swings}

    def gen_min_set(self):
        try:
            self.db_mins = db(cursorclass=MySQLdb.cursors.DictCursor, db='steadyfa_projection_prep')
            self.db_mins.pull_mins(self.origin, self.destination, self.earliest_source_date, self.start_date, self.flight_type, self.max_trip_length, self.prefs.id, self.num_high_days, 'search_sum_')
            self.db_mins.db_disconnect()
            min_table = import_table('search_sum_minimums', db_name='steadyfa_projection_prep')
            self.min_set = data_set_analysis(min_table)
            #self.db.find_mins(self.origin, self.destination, self.earliest_source_date, self.prefs, self.flight_type, self.num_high_days, self.hi_price_wk_day-1)
            #min_table = import_table('minimums_None')
            #self.db.drop_existing('minimums_None')
        except Exception as err:
            self.min_set = False
            self.errors.append("Error: route %s_%s, prefs %s, flight_type: %s - problem generating set of minimum fares (%s)" % (self.origin, self.destination, self.prefs.id, self.flight_type, err))


    def find_recent_peak_fare(self):
        if self.min_set:
            try:
                bank = []
                for i in self.min_set.input:
                    bank.append(i['min_fare'])
                max_fare = max(bank)

                return "Similar trips on this route cost as much as $%s in the past %s weeks" % (max_fare, self.weeks_back)
            except:
                return None
        else:
            self.errors.append("Error: route %s_%s, prefs %s, flight_type: %s - problem finding recent peak fare" % (self.origin, self.destination, self.prefs.id, self.flight_type))
            return None


    def find_price_swings(self):
        # find max price change on specific travel date combinations over course of a given time period
        if self.min_set:
            try:
                dates = self.min_set.find_uniques(['depart_date'])

                # randomly select the lesser of 'limit' or number items in date list to process quick
                limit = 20
                if len(dates) > limit:
                    pick = limit
                else: pick = len(dates)

                trunc_dates = []
                for i in range(pick):
                    rand = randint(0, len(dates)-1)
                    trunc_dates.append(dates.pop(rand))

                bank = []
                for index, i in enumerate(trunc_dates):
                    # cycle through dates
                    for j in range(self.final_proj_week, self.final_proj_week+3):
                        # cycle through depart_lengths to find multiple differences in prices over a week for each item in date_trips
                        for k in range(2):
                            # cycles through three potential trip lengths
                            trip_length = (k * 6) + 9
                            try:
                                # print "%s-%s-%s out of %s" % (index, j, k, len(dates))
                                later_price = find_sub_index_dict(self.min_set.input, {'depart_date': i['depart_date'], 'trip_length': trip_length, 'depart_length': (j*7)}, loop=False)[1]['min_fare']
                                earlier_price = find_sub_index_dict(self.min_set.input, {'depart_date': i['depart_date'], 'trip_length': trip_length, 'depart_length': ((j*7)+7)}, loop=False)[1]['min_fare']
                                bank.append(later_price - earlier_price)

                            except Exception as err:
                                self.errors.append("Error: route %s_%s, prefs %s, flight_type: %s, depart_length week: %s - problem finding change in fares over week (%s)" % (self.origin, self.destination, self.prefs.id, self.flight_type, j, err))

                if bank:
                    max_bank = max(bank)
                    if max_bank >= 20:
                        return "Similar trips on this route have experienced one-week price increases of $%s in the past %s weeks" % (max_bank, self.weeks_back)
                    else: return None
                else: return None
            except:
                return None
        else:
            return None


    def find_previous_savings(self):
        # gives the maximum amount an exercised option was in the money
        try:
            bank = []
            for i in self.matches:
                bank.append(i[1]['amt_in_money'])
            max_savings = max(bank)

            return "%s recently saved $%s on a flight from %s to %s" % (self.rand_name(), max_savings, self.origin, self.destination)

        except Exception as err:
            self.errors.append("Error: route %s_%s, prefs %s, flight_type: %s - problem finding previous savings (%s)" % (self.origin, self.destination, self.prefs.id, self.flight_type, err))
            return None

    def find_popular_purchase(self):
        # mentions how many customers purchased a steadyfare similar to this one recently
        try:
            count = len(self.matches)
            return "%s customers recently purchased a similar steadyfare from %s to %s" % (count, self.origin, self.destination)
        except Exception as err:
            self.errors.append("Potential error: route %s_%s, prefs %s, flight_type: %s - did not find any records of past purchases (%s)" % (self.origin, self.destination, self.prefs.id, self.flight_type, err))
            return None

    def rand_name(self):
        names = ['Brian Holbrook', 'Eddard Stark', 'Saul Goodman', 'Tommy Wiseau', 'Jeff Baker']
        rand = randint(0, len(names)-1)
        return names[rand]


if __name__ == "__main__":

    """
    inputs = search_inputs(purpose='projection')
    example = search_summary(inputs, source='temp_options')
    example.run()
    #print example.errors
    print example.summary
    """
    example = aggregate_search_summaries(source='temp_options')
    example.complete_route_set()
    #pprint(example.set)
    example.replace_current_records('search_summary')
