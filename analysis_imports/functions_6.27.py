import datetime
import random
from random import randint
import math
import json
import MySQLdb
import MySQLdb.cursors
import copy
from cholesky import *
from warnings import filterwarnings
import itertools
import decimal
from pprint import pprint
import time
import socket
import numpy
import pickle
import os

filterwarnings('ignore', category = MySQLdb.Warning) # filters all MySQL warnings

class db(object):

    def __init__(self, host = "localhost", db = "steadyfa_sf_model", cursorclass = None):

        if socket.gethostname() == "a1.steadyfare.net":
            # these are the login credentials for the steadyfare.net server
            self.user = "steadyfa_model"
            self.passwd = "buttwatercruises"
            self.unix_socket = '/tmp/mysql.sock'
        else:
            # these credentials should work on Ryan's local machine and the api.levelskies.com server
            self.user = "root"
            self.passwd = "bitnami"
            self.unix_socket = '/opt/bitnami/mysql/tmp/mysql.sock'

        self.host = host
        self.db = db
        self.cursorclass = cursorclass
        self.cur = self.db_connect()


    def db_connect(self):
        #connect to db
        if self.cursorclass:
            self.connection = MySQLdb.connect(host=self.host,
                                              user=self.user,
                                              passwd=self.passwd,
                                              db=self.db,
                                              cursorclass=self.cursorclass,
                                              unix_socket=self.unix_socket
                                              )
        else:
            self.connection = MySQLdb.connect(host=self.host,
                                              user=self.user,
                                              passwd=self.passwd,
                                              db=self.db,
                                              unix_socket=self.unix_socket
                                              )
        return self.connection.cursor()


    def db_disconnect(self):
        #disconnect from db
        self.cur.close()
        self.connection.close()

    def import_table(self, source):
        data = self.sel_crit('all', source, ['*'], {})
        return data

    def get_cols(self, source):
        query = "SHOW columns FROM `%s`" % (source)
        query_ex = self.cur.execute(query)
        query_res =  self.cur.fetchall()
        bank = []
        for i in query_res:
          bank.append(i[0])
        return bank

    def get_distinct(self, source, col):
        query = "SELECT DISTINCT `%s` FROM `%s`" % (col, source)
        query_ex = self.cur.execute(query)
        query_res =  self.cur.fetchall()
        bank = []
        for i in query_res:
          bank.append(i[0])
        return bank

    def show_tables(self, db_name=None):
        if not db_name:
            db_name = self.db
        try:
            query = "SHOW TABLES FROM %s" % (db_name)
            query_ex = self.cur.execute(query)
            query_res =  self.cur.fetchall()
            return query_res
        except:
            return None


    def show_table_stats(self, table, db_name=None):
        if not db_name:
            db_name = self.db
        try:
            query = "SHOW TABLE STATUS FROM %s LIKE '%s'" % (db_name, table)
            query_ex = self.cur.execute(query)
            query_res =  self.cur.fetchall()
            return query_res
        except:
            return None


    def close_and_drop(self, table):
        self.db.drop_existing(table)
        self.db.db_disconnect()


    def get_random_row(self, table, column=None):
        if not column:
            what = '*'
        else: what = column

        rows = self.sel_crit('all', table, [what], {})
        rand = randint(0, len(rows)-1)

        if column:
            return rows[rand][0]
        else:
            return rows[rand]


    def drop_existing(self, table):
        query = "DROP TABLE IF EXISTS %s" % (table)
        query_ex = self.cur.execute(query)


    def does_table_exist(self, table, db=None):
        if db:
            query = "SHOW TABLES IN %s LIKE '%s' " % (db, table)
        else:
            query = "SHOW TABLES LIKE '%s'" % (table)
        query_ex = self.cur.execute(query)
        return query_ex


    def rename_table(self, old_name, new_name):
        try:
            query = "RENAME TABLE %s TO %s" % (old_name, new_name,)
            query_ex = self.cur.execute(query)
        except Exception as err:
            print "Error renaming exisiting %s table to %s: %s" % (old_name, new_name, err,)


    def replace_existing_table(self, table, columns):
        self.drop_existing(table)
        self.create_table(table, columns)


    def copy_table_from_other_db(self, local_table, foreign_table, foreign_db, drop=False):
        self.drop_existing(local_table)
        try:
            query = "CREATE TABLE %s SELECT * FROM %s.%s" % (local_table, foreign_db, foreign_table,)
            query_ex = self.cur.execute(query)
        except Exception as err:
            print "Error moving existing %s table to current db: %s" % (foreign_table, err)
        else:
            if drop:
                self.drop_existing("%s.%s" % (foreign_db, foreign_table))


    def flight_type_add(self, flight_type, max_trip_length):

        if flight_type == 'ow':
            return " AND trip_length = 0"
        elif flight_type == 'rt':
            return " AND trip_length >= 3 AND trip_length <= %s" % (max_trip_length * 7)


    def sel_amt(self,amt):
        if amt == 'one':
            query_res =  self.cur.fetchone()
        if amt == 'all':
            query_res =  self.cur.fetchall()
        return query_res


    def sel_crit(self, amt, table, what, where=None, greater=None, less=None, db_dict=False):

        """
        what_string = ', '.join(what)
        query = "SELECT %s FROM %s" % (what_string, table)
        if len(where)>0:
            count = 1
            query += ' WHERE '
            for k,v in where.iteritems():
                query += "%s = '%s'" % (self.format_column(k), v)
                if count < len(where):
                    query += " AND "
                count += 1
        #print query
        """
        if where or greater or less:
            where_string = "WHERE "
            if where:
                count = 1
                for k,v in where.iteritems():

                    where_string += "%s = '%s'" % (self.format_column(k), v)
                    if count < len(where):
                        where_string += " AND "
                    count += 1

            if greater:
                if where:
                    where_string += " AND "
                count = 1
                for k,v in greater.iteritems():
                    where_string += "%s >= '%s'" % (self.format_column(k), v)
                    if count < len(greater):
                        where_string += " AND "
                    count += 1

            if less:
                if where or greater:
                    where_string += " AND "
                count = 1
                for k,v in less.iteritems():
                    where_string += "%s <= '%s'" % (self.format_column(k), v)
                    if count < len(less):
                        where_string += " AND "
                    count += 1

        else:
            where_string = ""

        what_string = ', '.join(what)
        query = ("SELECT %s FROM %s "
                "%s " % (what_string, table, where_string))


        query_ex = self.cur.execute(query)
        query_res = self.sel_amt(amt)
        return query_res


    def sel_distinct(self, column, table, db_dict=False):

        query = "SELECT DISTINCT %s FROM `%s`" % (self.format_column(column), table)
        #return query

        query_ex = self.cur.execute(query)
        query_res =  self.cur.fetchall()

        results = []
        if db_dict:
            for i in query_res:
                for v in i.itervalues():
                    results.append(int(v))
        else:
            for i in query_res:
                results.append(int(i[0]))

        return results


    def find_simple_sum_stat(self, table, sum_stat, column, where=None, greater=None, less=None, db_dict=False):

        if where or greater or less:
            where_string = "WHERE "
            if where:
                count = 1
                for k,v in where.iteritems():

                    where_string += "%s = '%s'" % (self.format_column(k), v)
                    if count < len(where):
                        where_string += " AND "
                    count += 1

            if greater:
                if where:
                    where_string += " AND "
                count = 1
                for k,v in greater.iteritems():
                    where_string += "%s >= '%s'" % (self.format_column(k), v)
                    if count < len(greater):
                        where_string += " AND "
                    count += 1

            if less:
                if where or greater:
                    where_string += " AND "
                count = 1
                for k,v in less.iteritems():
                    where_string += "%s <= '%s'" % (self.format_column(k), v)
                    if count < len(less):
                        where_string += " AND "
                    count += 1

        else:
            where_string = ""

        query = ("SELECT %s(`%s`) AS `%s` "
                 "FROM `%s` "
                 "%s" % (sum_stat, column, column, table, where_string))
        #print query
        query_ex = self.cur.execute(query)
        query_res = self.cur.fetchone()

        if db_dict:
            return query_res[column]
        else:
            return query_res[0]


    def format_column(self, input):
            items = input.split(',')
            if len(items) == 1:
                return "`%s`" % (items[0])
            if len(items) == 2:
                return "(`%s` + `%s`)" % (items[0], items[1])
            if len(items) == 3:
                return "(`%s` %s `%s`)" % (items[0], items[2], items[1])
            if len(items) == 4:
                if items[3] == 'date_inc':
                    return "(`%s` %s INTERVAL `%s` DAY)" % (items[0], items[2], items[1])
                else:
                    raise Exception("Impropper Mysql data formatter input")


    def create_table(self, table, columns):
        query = "CREATE TABLE %s" % (table)
        if len(columns)>0:
            count = 1
            query += ' ( id INT PRIMARY KEY AUTO_INCREMENT, '
            for k, v in columns.iteritems():
                query += "`%s` %s" % (k, v)
                if count < len(columns):
                    query += " , "
                else:
                    query += " )"
                count += 1

        query_ex = self.cur.execute(query)


    def insert_data(self, table, values):

        query = "INSERT INTO %s" % (table)
        if len(values)>0:
            count = 1
            query += ' ( '
            for k in values.iterkeys():
                query += "`%s`" % (k,)
                if count < len(values):
                    query += " , "
                else:
                    query += " ) VALUES"
                count += 1

        if len(values)>0:
            count = 1
            query += ' ( '
            for v in values.itervalues():
                query += "%s" % (v,)
                if count < len(values):
                    query += " , "
                else:
                    query += " )"
                count += 1

        query_ex = self.cur.execute(query)


    def multi_line_write(self, table, keys_sql_final, vars_sql_bank):
                vars_sql_final = ', '.join(vars_sql_bank)
                query = ("INSERT INTO %s %s VALUES %s" % (table, keys_sql_final, vars_sql_final,))
                self.cur.execute(query)


    def analysis_graph_search(self, stat, depart_length, trip_length, start_date=False):

        if start_date:
            select_string = "depart_length"
            date_string = "WHERE depart_date >= ('%s' - INTERVAL %s DAY) AND depart_date <= ('%s' - INTERVAL %s DAY) " % (start_date, (depart_length), start_date, (depart_length - 7))
        else:
            select_string = "depart_date"
            date_string = "WHERE depart_length = %s " % (depart_length)

        query = ("SELECT %s, %s(min_fare) as min_fare "
                 "FROM `graph_build_minimums` "
                 "%s"
                 "AND trip_length >= %s AND trip_length <= %s "
                 "GROUP BY %s " % (select_string, stat, date_string, trip_length[0], trip_length[1], select_string))


        """
        query = ("SELECT depart_date, depart_length, trip_length, %s(min_fare) as min_fare "
                 "FROM `graph_build_minimums` "
                 "WHERE depart_length = %s AND trip_length >= %s AND trip_length <= %s "
                 "GROUP BY depart_date, depart_length " % (stat, depart_length, trip_length[0], trip_length[1]))
        """


        query_ex = self.cur.execute(query)
        query_res = self.sel_amt('all')
        return query_res



    def pull_mins(self, origin, destination, earliest_source_date, start_date, flight_type, max_trip_length, prefs, num_high_days=None, adj_name=''):

        self.drop_existing('%sminimums' % (adj_name))

        flight_type_add = self.flight_type_add(flight_type, max_trip_length)

        if num_high_days:
            num_high_days_string = "AND num_high_days = %s " % (num_high_days)
        else: num_high_days_string = ""


        if num_high_days:
            query = ("CREATE table %sminimums "
                     "SELECT depart_date, depart_length, trip_length, min_fare "
                     "FROM steadyfa_projection_prep.%s%s "
                     "WHERE (depart_date) >= '%s' "
                     "AND (date_collected) <= '%s' "
                     "AND prefs = %s %s%s" % (adj_name, origin, destination, earliest_source_date, start_date, prefs, num_high_days_string, flight_type_add))
        else:
            query = ("CREATE table %sminimums "
                     "SELECT depart_date, depart_length, trip_length, min(min_fare) as min_fare "
                     "FROM steadyfa_projection_prep.%s%s "
                     "WHERE (depart_date) >= '%s' "
                     "AND (date_collected) <= '%s' "
                     "AND prefs = %s %s%s "
                     "GROUP BY depart_date, depart_length, trip_length " % (adj_name, origin, destination, earliest_source_date, start_date, prefs, num_high_days_string, flight_type_add))

        self.cur.execute(query)


    def find_mins(self, origin, destination, earliest_source_date, start_date, prefs, flight_type, num_high_days, max_trip_length, update_projection_prep=False):

        start_mins = time.time()
        self.drop_existing('holding_1')
        self.drop_existing('holding_2')
        self.drop_existing('holding_3')
        self.drop_existing('holding_4')
        self.drop_existing('minimums_%s' % (num_high_days))
        flight_type_add = self.flight_type_add(flight_type, max_trip_length)

        if update_projection_prep:
            #print "in here"
            self.db_alt_db = db(db="steadyfa_projection_prep")
            if not self.db_alt_db.does_table_exist("%s%s" % (origin, destination)):
                #print "tried creating table"
                columns = {'date_collected': 'DATE', 'depart_date': 'DATE', 'depart_length': 'INT(4)', 'trip_length': 'INT(3)', 'min_fare': 'FLOAT', 'num_high_days': 'INT(4)', 'prefs': 'INT(4)'}
                self.db_alt_db.create_table("steadyfa_projection_prep.%s%s" % (origin, destination), columns)
                min_date = '2000-01-01'
            else:
                #print "thinks table exists"
                query = ("SELECT max(`date_collected`) FROM `%s%s` WHERE `prefs` = '%s' " % (origin, destination, prefs.id))
                self.db_alt_db.cur.execute(query)
                min_date = str(self.db_alt_db.sel_amt('one')[0])
                #print str(min_date)
                if min_date == 'None':
                    min_date = '2000-01-01'
            #print "pref: %s - latest date: %s" % (prefs.id, min_date)
            query = ("CREATE table holding_1 "
                 "SELECT date_collected, (date_collected + INTERVAL depart_length DAY) AS depart_date, depart_length, trip_length, min_price AS fare "
                 "FROM steadyfa_sf_analysis.%s%s "
                 "WHERE (date_collected) > '%s' "
                 "%s%s" % (origin, destination, min_date, prefs.build_query(), flight_type_add))
            #print query
            self.cur.execute(query)
            #print "Completed hold1 in " + `time.time()-start_mins` + " seconds"

        else:
            query = ("CREATE table holding_1 "
                     "SELECT date_collected, (date_collected + INTERVAL depart_length DAY) AS depart_date, depart_length, trip_length, min_price AS fare "
                     "FROM steadyfa_sf_analysis.%s%s "
                     "WHERE (date_collected + INTERVAL depart_length DAY) >= '%s' "
                     "AND (date_collected) <= '%s'%s%s" % (origin, destination, earliest_source_date, start_date, prefs.build_query(), flight_type_add))
            #print query
            self.cur.execute(query)
            #print "Completed hold1 in " + `time.time()-start_mins` + " seconds"
        if num_high_days >= 0:

            # used for generating standard projection data source
            weekday_vals = weekday_pairs(flight_type)
            query_inserts = weekday_vals.tag_query_values()

            query = ("CREATE table holding_2 "
                     "SELECT date_collected, depart_date, depart_length, trip_length, fare, Weekday(depart_date) AS day_tag_d , Weekday(depart_date + INTERVAL trip_length DAY) AS day_tag_r "
                     "FROM holding_1" )
            self.cur.execute(query)
            #print query
            #print "Completed hold2 in " + `time.time()-start_mins` + " seconds"

            query = ("CREATE table holding_3 "
                     "SELECT date_collected, depart_date, depart_length, trip_length, fare, %s , %s "
                     "FROM holding_2" ) % (query_inserts['depart_tag'], query_inserts['return_tag'])
            self.cur.execute(query)
            #print query
            #print "Completed hold3 in " + `time.time()-start_mins` + " seconds"

            query = ("CREATE table holding_4 "
                     "SELECT date_collected, depart_date, depart_length, trip_length, fare, %s "
                     "FROM holding_3" ) % (query_inserts['convert_tags'])
            self.cur.execute(query)
            #print query
            #print "Completed hold4 in " + `time.time()-start_mins` + " seconds"

            if update_projection_prep:
                for i in weekday_vals.pair_ids.iterkeys():
                    query = ("INSERT INTO %s%s (date_collected, depart_date, depart_length, trip_length, min_fare, num_high_days, prefs)"
                           "SELECT date_collected, depart_date, depart_length, trip_length, min(fare) as min_fare, num_high_days, %s "
                           "FROM %s.holding_4 "
                           "WHERE num_high_days = '%s' "
                           "GROUP BY depart_date, depart_length, trip_length, num_high_days "
                           "ORDER BY depart_length, depart_date DESC" % (origin, destination, prefs.id, self.db, i))
                    self.db_alt_db.cur.execute(query)

                #print "Completed mins in " + `time.time()-start_mins` + " seconds"

                self.db_alt_db.db_disconnect()

            else:
                query = ("CREATE table minimums_%s "
                       "SELECT depart_date, depart_length, trip_length, min(fare) as min_fare, num_high_days "
                       "FROM holding_4 "
                       "WHERE num_high_days = '%s' "
                       "GROUP BY depart_date, depart_length, trip_length, num_high_days "
                       "ORDER BY depart_length, depart_date DESC" % (num_high_days, num_high_days))
                self.cur.execute(query)
                #print query
                #print "Completed mins in " + `time.time()-start_mins` + " seconds"


            self.drop_existing('holding_2')
            self.drop_existing('holding_3')
            self.drop_existing('holding_4')
            #print "Deleted holds in " + `time.time()-start_mins` + " seconds"
        else:
            # used in search_summary, where num_high_day differentiation not relevant
            query = ("CREATE table minimums_%s "
                     "SELECT depart_date, depart_length, trip_length, min(fare) as min_fare "
                     "FROM holding_1 "
                     "GROUP BY depart_date, depart_length, trip_length "
                     "ORDER BY depart_length, depart_date DESC" % (num_high_days))

            self.cur.execute(query)

        self.drop_existing('holding_1')



    def find_single_min_fare(self, origin, destination, sel_dep_date, sel_ret_date, flight_type, lockin_per, prefs, depart_length_width, max_trip_length, weekday_types):

        flight_type_add = self.flight_type_add(flight_type, max_trip_length)
        trip_length = int((sel_ret_date-sel_dep_date).days)

        query_res = None
        width = 0

        def matching_price_type_range(trip_length, sel_ret_date, width, weekday_types):
            # ensures that widening the range of acceptable return dates does not introduce data from a different price level weekday
            if weekday_types.find_weekday_cat((sel_ret_date + datetime.timedelta(days = -width)).weekday()) == weekday_types.find_weekday_cat(sel_ret_date.weekday()):
                low = trip_length - width
            else: low = trip_length

            if weekday_types.find_weekday_cat((sel_ret_date + datetime.timedelta(days = +width)).weekday()) == weekday_types.find_weekday_cat(sel_ret_date.weekday()):
                high = trip_length + width
            else: high = trip_length

            return (low, high)


        while not query_res:
            # incrementally expands acceptable range of trip lengths if initially returns blank data set
            trip_length_range = matching_price_type_range(trip_length, sel_ret_date, width, weekday_types)

            depart_length = (lockin_per * 7, (lockin_per * 7) + depart_length_width)

            query = ("SELECT min_price "
                     "FROM steadyfa_sf_analysis.%s%s "
                     "WHERE (date_collected + INTERVAL depart_length DAY) = '%s' "
                     "AND (trip_length >= %s AND trip_length <= %s) "
                     "AND (depart_length >= %s AND depart_length <= %s) "
                     "%s%s" % (origin, destination, sel_dep_date, trip_length_range[0], trip_length_range[1], depart_length[0], depart_length[1], prefs.build_query(), flight_type_add))
            query_ex = self.cur.execute(query)

            query_res = self.sel_amt('all')

            if width == 0:
                break
            width += 1

        bank = []
        for i in query_res:
            bank.append(i[0])

        return (min(bank),len(bank))

    def find_min_sum_stat(self, sum_stat, depart_dates, depart_lengths, trip_length=None):

        if depart_dates:
            build_where = []
            for i in depart_dates:
                build_where.append("(depart_date >= '%s' AND depart_date <= '%s')" % (i[0], i[1]))
            where_dep_dat = ' OR '.join(build_where)
            where_dep_dat = ' AND ' + where_dep_dat
        else: where_dep_dat = ''

        if trip_length:
            if type(trip_length) is list:
                if type(trip_length[0]) is list:
                    for index, i in enumerate(trip_length):
                        if index == 0:
                            where_trip_len = "AND ((trip_length >= '%s' AND trip_length <= '%s')" % (i[0], i[1])
                        else:
                            where_trip_len += " OR (trip_length >= '%s' AND trip_length <= '%s')" % (i[0], i[1])
                    where_trip_len += ")"
                else:
                    where_trip_len = " AND trip_length >= '%s' AND trip_length <= '%s' " % (trip_length[0], trip_length[1])
            else:
                where_trip_len = " AND trip_length = '%s' " % (trip_length)
        else: where_trip_len = ''

        query = ("SELECT %s(min_fare) AS %s_min_fare "
                 "FROM minimums "
                 "WHERE (depart_length >= %s AND depart_length <= %s)%s%s" % (sum_stat, sum_stat.lower(), depart_lengths[0], depart_lengths[1], where_dep_dat, where_trip_len))

        #print query

        query_ex = self.cur.execute(query)
        query_res = self.cur.fetchone()
        return query_res[0]


    def rename_and_archive(self, backup_db, temp_db, table, time):
        # move existing projection table to archive location
        temp_table = 'temp_%s' % (table)
        if (self.does_table_exist(temp_table, temp_db)):

            if (self.does_table_exist(table)):
                archive_name = ('%s_%s') % (table, time,)
                #self.rename_table(table, archive_name)
                try:
                    query = "CREATE TABLE %s.%s SELECT * FROM %s" % (backup_db, archive_name, table,)
                    query_ex = self.cur.execute(query)
                except Exception as err:
                    #self.rename_table(archive_name, table,)
                    print "Error moving existing %s table to archive: %s" % (table, err)
                else:
                    self.drop_existing(table)

            # move temp_projection table from temp_tables db to model db
            self.copy_table_from_other_db(table, temp_table, temp_db, drop=True)
            """
            if not self.does_table_exist(table):
                try:
                    query = "CREATE TABLE %s SELECT * FROM %s.%s" % (table, temp_db, temp_table,)
                    query_ex = self.cur.execute(query)
                except Exception as err:
                    print "Error moving existing %s table to model db: %s" % (temp_table, err)
                else:
                    self.drop_existing("%s.%s" % (temp_db, temp_table))
            """
        else:
            print "No existing table: %s" % (temp_table,)



    def build_min_fare_table(self, route, max_date_collected=None, min_date_collected=None):
        # update these queries to allow for alternate routes and prefs

        self.drop_existing('%s_min_fares' % (route))

        if min_date_collected and not max_date_collected:
            from_string = "(SELECT * FROM steadyfa_sf_analysis.%s WHERE (`date_collected`) >= '%s') temp " % (route, min_date_collected)
        elif max_date_collected and not min_date_collected:
            from_string = "(SELECT * FROM steadyfa_sf_analysis.%s WHERE (`date_collected`) <= '%s') temp " % (route, max_date_collected)
        elif max_date_collected and min_date_collected:
            if isinstance(min_date_collected, int):
                min_date_collected = max_date_collected - datetime.timedelta(weeks = min_date_collected)
            from_string = "(SELECT * FROM steadyfa_sf_analysis.%s WHERE (`date_collected` >= '%s' AND `date_collected` <= '%s')) temp " % (route, min_date_collected, max_date_collected)
        else:
            from_string = "steadyfa_sf_analysis.%s" % (route)

        #"Dayname(`date_collected` + INTERVAL `depart_length` DAY) as dep_wk_day, "
        #"Dayname(`date_collected` + INTERVAL `depart_length` DAY + INTERVAL `trip_length` DAY) as ret_wk_day, "
        query = ("CREATE TABLE %s_min_fares "
                "SELECT min(`min_price`) as price, count(`min_price`) as count, `date_collected`, `depart_length`, `trip_length`, "
                "(`depart_length` + `trip_length`) as return_length, "
                "(`date_collected` + INTERVAL `depart_length` DAY) as depart_date, "
                "(`date_collected` + INTERVAL `depart_length` DAY + INTERVAL `trip_length` DAY) as return_date, "
                "Weekday(`date_collected` + INTERVAL `depart_length` DAY) AS day_tag_d, "
                "Weekday(`date_collected` + INTERVAL `depart_length` DAY + INTERVAL `trip_length` DAY) AS day_tag_r "
                "FROM %s "
                "GROUP BY `date_collected`, `depart_length`, `trip_length` "
                "ORDER BY `date_collected` DESC "
                % (route, from_string))
        query_ex = self.cur.execute(query)


    def group_weekdays(self,route, min_dep_date=None):
        self.drop_existing('labels')
        self.build_min_fare_table(route, min_dep_date=min_dep_date)
        query = ("SELECT avg(`price`), stddev(`price`) "
                "FROM `%s_min_fares` " % (route))
        query_ex = self.cur.execute(query)
        avg, st_dev = self.cur.fetchone()

        query = ("CREATE TABLE labels "
                "SELECT `dep_wk_day`, `ret_wk_day`, "
                "`price`, ((`price`-%s) / %s) as zscore, "
                 "IF(((`price`-%s) / %s)>1, 'xhigh',IF(((`price`-%s) / %s)>0,'high',IF(((`price`-%s) / %s)>-1,'low','xlow'))) as label "
                "FROM `%s_min_fares` " % (avg, st_dev, avg, st_dev,avg, st_dev, avg, st_dev, route))

        query_ex = self.cur.execute(query)


    def join_fares(self, route, max_dist=None, flex=True, max_date_collected=None, min_date_collected=None):

        if not self.does_table_exist("%s_min_fares" % (route)):
            self.build_table_a(route, max_date_collected=None, min_date_collected=None)
        self.drop_existing('%s_price_change_source' % (route))

        if flex:
            dep_len_window, date_window = 4, 7
        else:
            dep_len_window, date_window = 4, 1

        query = ("CREATE TABLE %s_price_change_source "
                "SELECT a.price as beg_price, b.price as end_price, a.count, a.date_collected, a.trip_length, "
                "a.depart_date, a.return_date, a.day_tag_d, a.day_tag_r, "
                "a.depart_length as depart_length, (a.depart_length + a.trip_length) as return_length, "
                "b.price-a.price as abs_inc,  b.price/a.price as rel_inc, "
                "(a.depart_length - b.depart_length) as proj_length "
                "FROM %s_min_fares, a as b "
                "WHERE a.depart_length > b.depart_length "
                "AND (a.depart_date - b.depart_date) = 0 "
                "AND (a.return_date - b.return_date) = 0 "
                "ORDER BY a.date_collected DESC " % (route, route))

        query_ex = self.cur.execute(query)
        #self.drop_existing('%s_min_fares' % (route))


    def pop_inputs(self, route, historical_windows):

        flight_type = 'rt'

        columns = {'date_collected': "DATE", 'depart_date': "DATE", 'return_date': "DATE", 'proj_length': 'INT(3)'}
        for i in ('depart','return'):
            for j in historical_windows:
                columns['%s_date_avg_fare_%s' % (i,j)] = "DOUBLE"
                columns['%s_date_st_dev_fare_%s' % (i,j)] = "DOUBLE"
                columns['%s_length_avg_change_%s' % (i,j)] = "DOUBLE"
                columns['%s_length_st_dev_change_%s' % (i,j)] = "DOUBLE"
        self.replace_existing_table('%s_hist_movement_analysis' % (route), columns)

        # get unique search params
        unique_inputs = {}
        query = ("SELECT DISTINCT `date_collected`, `depart_date`, `day_tag_r`  FROM `%s_price_change_source` " % (route))
        query_ex = self.cur.execute(query)
        unique_inputs['price_depart_date'] = self.cur.fetchall()

        query = ("SELECT DISTINCT `date_collected`, `return_date`, `day_tag_d`  FROM `%s_price_change_source` " % (route))
        query_ex = self.cur.execute(query)
        unique_inputs['price_return_date'] = self.cur.fetchall()

        query = ("SELECT DISTINCT `date_collected`, `depart_date`, `day_tag_r`, `proj_length`  FROM `%s_price_change_source` " % (route))
        query_ex = self.cur.execute(query)
        unique_inputs['inc_depart_date'] = self.cur.fetchall()

        query = ("SELECT DISTINCT `date_collected`, `return_date`, `day_tag_d`, `proj_length`  FROM `%s_price_change_source` " % (route))
        query_ex = self.cur.execute(query)
        unique_inputs['inc_return_date'] = self.cur.fetchall()

        return unique_inputs


    def find_hist_analysis(self, route, unique_inputs, historical_windows):

        flight_type = 'rt'

        master = {}
        for index, i in enumerate(('depart','return',)):

            # filter by date
            row_bank = []
            full_length = len(unique_inputs['price_%s_date' % (i)])
            for counter, inp in enumerate(unique_inputs['price_%s_date' % (i)]):

                print "%s - out of %s: %s" % (i, full_length, counter)
                row = dict(inp.items())
                depart_weekday = inp['%s_date' % (i)].weekday() if '%s_date' % (i) in inp else inp['day_tag_d']
                return_weekday = inp['%s_date' % (i)].weekday() if '%s_date' % (i) in inp else inp['day_tag_r']
                travel_date = inp['%s_date' % (i)]
                upper_date = travel_date + datetime.timedelta(days = 3)
                lower_date = travel_date - datetime.timedelta(days = 3)
                travel_date_length = (travel_date-inp['date_collected']).days

                query = ("SELECT * "
                        "FROM `%s_price_change_source` "
                        "WHERE (`%s_date` >= '%s' AND `%s_date` <= '%s') "
                        "AND (`day_tag_d` = %s AND `day_tag_r` = %s) "
                        "" % (route, i, lower_date, i, upper_date, depart_weekday, return_weekday))
                query_ex = self.cur.execute(query)
                table = self.cur.fetchall()

                if len(table) > 0:
                    columns = [x for x in table[0].keys()]
                    temp_rows = numpy.asarray([[x for x in line.values()] for line in table])

                    for index_2, j in enumerate(historical_windows):

                        upper_date_length = travel_date_length - 3 + (7 * j)
                        inc = 0 if index_2 == 0 else historical_windows[index_2-1]
                        lower_date_length = travel_date_length - 3 + (7 * inc)

                        group = temp_rows[(
                                    (temp_rows[:,columns.index('%s_length' % (i))]>=lower_date_length) &
                                    (temp_rows[:,columns.index('%s_length' % (i))]<=upper_date_length)
                                    )][:,columns.index('end_price')]

                        if group.size > 0:
                            avg =  numpy.mean(group)
                        else:
                            avg = None
                        if group.size > 1:
                            st_dev = numpy.std(group)
                        else:
                            st_dev = None

                        row['%s_date_avg_fare_%s' % (i,j)] = avg
                        row['%s_date_st_dev_fare_%s' % (i,j)] = st_dev
                else:
                    for index_2, j in enumerate(historical_windows):
                        row['%s_date_avg_fare_%s' % (i,j)] = None
                        row['%s_date_st_dev_fare_%s' % (i,j)] = None

                row_bank.append(row)

            master['price_%s_date' % (i)] = row_bank


            # filter by proj length and travel length
            row_bank = []
            full_length = len(unique_inputs['inc_%s_date' % (i)])
            for counter, inp in enumerate(unique_inputs['inc_%s_date' % (i)]):

                row = dict(inp.items())
                print "%s - out of %s: %s" % (i, full_length, counter)

                depart_weekday = inp['%s_date' % (i)].weekday() if '%s_date' % (i) in inp else inp['day_tag_d']
                return_weekday = inp['%s_date' % (i)].weekday() if '%s_date' % (i) in inp else inp['day_tag_r']
                travel_date = inp['%s_date' % (i)]
                travel_date_length = (travel_date-inp['date_collected']).days
                upper_date_length = travel_date_length + 3
                lower_date_length = travel_date_length - 3
                proj_length_pair = (inp['proj_length']+3,inp['proj_length']-3,)

                query = ("SELECT * "
                        "FROM `%s_price_change_source` "
                        "WHERE (`%s_length` >= '%s' AND `%s_length` <= '%s') "
                        "AND (`proj_length` >= '%s' AND `proj_length` <= '%s') "
                        "AND (`day_tag_d` = %s AND `day_tag_r` = %s) "
                        "" % (route, i, lower_date_length, i, upper_date_length, proj_length_pair[1], proj_length_pair[0], depart_weekday, return_weekday))
                query_ex = self.cur.execute(query)
                table = self.cur.fetchall()
                if len(table) > 0:
                    columns = [x for x in table[0].keys()]
                    temp_rows = numpy.asarray([[x for x in line.values()] for line in table])

                    for index_2, j in enumerate(historical_windows):

                        upper_date = inp['date_collected'] - datetime.timedelta(days = (7 * j) - 3)
                        inc = 0 if index_2 == 0 else historical_windows[index_2-1]
                        lower_date = inp['date_collected'] - datetime.timedelta(days = (7 * inc) - 3)

                        group = temp_rows[(
                                    (temp_rows[:,columns.index('date_collected')]<=lower_date) &
                                    (temp_rows[:,columns.index('date_collected')]>=upper_date)
                                    )][:,columns.index('rel_inc')]

                        if group.size > 0:
                            avg =  numpy.mean(group)
                        else:
                            avg = None
                        if group.size > 1:
                            st_dev = numpy.std(group)
                        else:
                            st_dev = None

                        row['%s_length_avg_change_%s' % (i,j)] = avg
                        row['%s_length_st_dev_change_%s' % (i,j)] = st_dev
                else:
                    for index_2, j in enumerate(historical_windows):
                        row['%s_length_avg_change_%s' % (i,j)] = None
                        row['%s_length_st_dev_change_%s' % (i,j)] = None

                row_bank.append(row)

            master['inc_%s_date' % (i)] = row_bank



        # create temp tables for master and insert data
        for t in ('depart', 'return'):
            for s in ('price', 'inc'):
                print "%s_%s" % (t,s)
                for index, item in enumerate(master['%s_%s_date' % (s,t)]):

                    # build table on first row
                    if index == 0:

                        columns = {}
                        for k, v in item.iteritems():
                            if k == 'date_collected' or k == '%s_date' % (t):
                                columns['%s' % (k)] = "DATE"
                            else:
                                columns['%s' % (k)] = "DOUBLE"
                        self.replace_existing_table('%s_hist_movement_%s_%s' % (route,t,s), columns)

                    # insert each row into table
                    temp = copy.deepcopy(item)

                    for k, v in temp.iteritems():
                        if k == 'date_collected' or k == '%s_date' % (t):
                            temp[k] = "'%s'" % (v)
                        else:
                            try:
                                int(v)
                            except:
                                temp[k] = "NULL"
                    self.insert_data('%s_hist_movement_%s_%s' % (route,t,s), temp)



    def join_fares_on_hist_analysis(self, route):

        price_changes = self.import_table('%s_price_change_source' % (route))

        new_table = []
        for index, i in enumerate(price_changes):

            print "price changes index: %s " % (index)

            i['date_completed'] = i['date_collected'] + datetime.timedelta(days = i['proj_length'])

            row = dict(i.items())
            add_row = True
            for t in ('depart', 'return'):

                day_label = 'day_tag_r' if t == 'depart' else 'day_tag_d'

                res = self.sel_crit('one', '%s_hist_movement_%s_price' % (route,t), ['*'], {'%s_date' % (t): i['%s_date' % (t)], 'date_collected': i['date_collected'], "%s" % (day_label): i[day_label]})
                j = copy.deepcopy(res)
                if not j:
                    add_row = False
                else:
                    del j['id']
                    del j['%s_date' % (t)]
                    del j['date_collected']
                    row.update(j)

                res = self.sel_crit('one', '%s_hist_movement_%s_inc' % (route,t), ['*'], {'%s_date' % (t): i['%s_date' % (t)], 'date_collected': i['date_collected'], "%s" % (day_label): i[day_label], 'proj_length': i['proj_length']})
                j = copy.deepcopy(res)
                if not j:
                    add_row = False
                else:
                    del j['id']
                    del j['%s_date' % (t)]
                    del j['date_collected']
                    del j['proj_length']
                    row.update(j)

            if add_row:
                del row['depart_date']
                del row['return_date']
                new_table.append(row)


        columns = {}
        for k, v in new_table[0].iteritems():
            if k == 'date_collected' or k == 'date_completed':
                columns['%s' % (k)] = "DATE"
            else:
                columns['%s' % (k)] = "DOUBLE"

        self.replace_existing_table('%s_inputs' % (route), columns)


        for i in new_table:
            for k, v in i.iteritems():
                if k == 'date_collected' or k == 'date_completed':
                    i[k] = "'%s'" % (v)
                if v is None or v is 'nan':
                    i[k] = "NULL"
            self.insert_data('%s_inputs' % (route), i)


# General functions unrelated to any class
def relax_prefs(prefs):
    """
    @summary: In the event that there is not enough data to calculate holding prices with given preferences, test a less restrictive set of prefs
                Assumes that "non-stop" preferences are more important than flight time preferences to most consumers.
    @attention: as of 1/13/2013,  does not account for airline prefs
    """

    def relax_time(pref):
        if pref == [3]:
            pref = []
        else:
            pref = [3]
        return pref

    if prefs.stop_pref:
        prefs.stop_pref = []
        prefs.asign_id(prefs.dep_time_pref, prefs.ret_time_pref, prefs.stop_pref, prefs.airline_pref)
        return prefs
    elif prefs.ret_time_pref:
        prefs.ret_time_pref = relax_time(prefs.ret_time_pref)
        prefs.asign_id(prefs.dep_time_pref, prefs.ret_time_pref, prefs.stop_pref, prefs.airline_pref)
        return prefs
    elif prefs.dep_time_pref:
        prefs.dep_time_pref = relax_time(prefs.dep_time_pref)
        prefs.asign_id(prefs.dep_time_pref, prefs.ret_time_pref, prefs.stop_pref, prefs.airline_pref)
        return prefs
    else:
        return prefs


def import_table(source, db_name=None):
    # save full mysql table as dictionary
    if db_name:
        db_dict = db(cursorclass=MySQLdb.cursors.DictCursor, db=db_name)
    else:
        db_dict = db(cursorclass=MySQLdb.cursors.DictCursor)
    data = db_dict.sel_crit('all', source, ['*'], {})
    db_dict.db_disconnect()
    return data


def standard_deviation(alist):
    # find standard deviation of a list
    if alist:
        try:
            mean = sum(alist)/len(alist)
            sum_squares = 0
            for i in alist:
                sum_squares = sum_squares + (i - mean)**2
            st_dev = math.sqrt( sum_squares / (len(alist) -1) )
            return st_dev
        except:
            return None
    else:
        return None


def median(alist):
    # find median of a list
    srtd = sorted(alist) # returns a sorted copy
    mid = len(alist)/2   # remember that integer division truncates

    if len(alist) % 2 == 0:  # take the avg of middle two
        return (srtd[mid-1] + srtd[mid]) / 2.0
    else:
        return srtd[mid]


def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    N = sorted(N)
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1


# searches list of dictionaries for provided items (in second arguement), returns list index and respective dictionary
def find_sub_index_dict(list, where, loop=False):
    #next(((index, dict) for index, dict in enumerate(list) if all(k in dict.items() for k in where.items())), None)
    g = ((index, dict) for index, dict in enumerate(list) if all(k in dict.items() for k in where.items()))
    if loop:
        set = []
        entry = True
        while entry:
            entry = next(g, None)
            if entry:
                set.append(entry)
        if set:
            return set
        else: None
    else:
       return next(g, None)


# format input as a date type if possible
def format_as_date(arg):
    if type(arg) is not datetime.date:
        if type(arg) is datetime.datetime:
            arg = arg.date()
        elif "/" in arg:
            arg = datetime.datetime.strptime(arg,'%m/%d/%Y').date()
        elif ":" in arg:
            arg = datetime.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S').date()
        elif "-" in arg:
            arg = datetime.datetime.strptime(arg,'%Y-%m-%d').date()
    return arg


# gives weighted average and max projection and standard deviation for a gen_price simulation, used in full_simulation, and api search records
def avearege_max_projected_stats(stats, combos):
    max_fare = max_st_dev = count = avg_fare_sum = avg_st_dev_sum = 0
    for k, v in stats.iteritems():
        if v['fare'] > max_fare:
            max_fare = v['fare']
        if v['st_dev'] > max_st_dev:
            max_st_dev = v['st_dev']
        count += combos[k]
        avg_fare_sum += combos[k] * v['fare']
        avg_st_dev_sum += combos[k] * v['st_dev']
    avg_fare = avg_fare_sum / count
    avg_st_dev = avg_st_dev_sum / count
    return {'max_fare': max_fare, 'max_st_dev': max_st_dev, 'avg_fare': avg_fare, 'avg_st_dev': avg_st_dev}


class preferences(object):

    # flight preferences codes, to suggest combinations of flight times, non-stop, and other requirements
    def __init__(self, flight_type, dep_time_pref=[], ret_time_pref=[], stop_pref=[], airline_pref=[]):

        self.dep_time_pref = dep_time_pref
        self.ret_time_pref = ret_time_pref
        self.stop_pref = stop_pref
        self.airline_pref = airline_pref
        self.flight_type = flight_type
        self.generate_ids()
        self.run()


    def run(self):
        self.asign_id(self.dep_time_pref, self.ret_time_pref, self.stop_pref, self.airline_pref)
        self.dep_time_pref_str = self.time_pref_strings(self.dep_time_pref, 'depart_time')
        self.ret_time_pref_str = self.time_pref_strings(self.ret_time_pref, 'return_time') if self.flight_type == 'rt' else None
        self.stop_pref_str = self.num_stops_strings(self.stop_pref)


    def set_inputs_by_id(self, id):
        inputs = self.id_list[id]
        self.dep_time_pref = inputs['dep_time_pref']
        self.ret_time_pref = inputs['ret_time_pref']
        self.stop_pref = inputs['stop_pref']
        self.run()


    def generate_ids(self):

        self.id_list = dict()   # current setup assumes at most one of three choices can be selected relating to flight times, and at most one option can be selected for number of stops
                                # does not take into account airline preferences
        if self.flight_type == 'rt':
            dep_time_pref = [1, 2, 3]
            ret_time_pref = [1, 2, 3]
            stop_prefs = [1]
            count = 0

            for dtp in range(0, 2):
              for subset in itertools.combinations(dep_time_pref, dtp):
                for rtp in range(0, 2):
                    for subset2 in itertools.combinations(ret_time_pref, rtp):
                        for sp in range(0, 2):
                            for subset3 in itertools.combinations(stop_prefs, sp):
                                self.id_list[count] = {'dep_time_pref': list(subset), 'ret_time_pref': list(subset2), 'stop_pref': list(subset3)}
                                count += 1

        if self.flight_type == 'ow':
            dep_time_pref = [1, 2, 3]
            stop_prefs = [1]
            count = 0

            for dtp in range(0, 2):
                for subset in itertools.combinations(dep_time_pref, dtp):
                    for sp in range(0, 2):
                        for subset2 in itertools.combinations(stop_prefs, sp):
                            self.id_list[count] = {'dep_time_pref': list(subset), 'stop_pref': list(subset2)}
                            count += 1


    def build_query(self):

        query = ['']
        if (self.dep_time_pref_str[1]):
            query.append(self.dep_time_pref_str[1])
        if self.flight_type == 'rt':
            if (self.ret_time_pref_str[1]):
                query.append(self.ret_time_pref_str[1])
        if (self.stop_pref_str[1]):
            query.append(self.stop_pref_str[1])
        return ' AND '.join(query)


    def describe(self):
        text = []
        text.append('potential departure time: ' + self.dep_time_pref_str[0])
        if self.flight_type == 'rt':
            text.append('potential return time: ' + self.ret_time_pref_str[0])
        text.append('potential number of stops: ' + self.stop_pref_str[0])
        return '\n'.join(text)


    def num_stops_strings(self, stop_pref):
        if not stop_pref:
            text_desc = ('flights with fewer than 3 connections ok')
            query_add = ('(depart_num_stops < 3 AND return_num_stops < 3)')
        if (stop_pref):
            text_desc = ('non-stop flights only')
            query_add = ('(depart_num_stops = 0 AND return_num_stops = 0)')
        return [text_desc, query_add]


    def time_pref_strings(self, time_pref, direction_time):
        time_splits = dict() # sets the hours of the day asigned to each time_split, for building select query
        time_splits[1] = (5,11)
        time_splits[2] = (12,22)
        time_splits[3] = (5,22)

        if not time_pref:
            text_desc = ('anytime')
            query_add = ''
        else:
            if 1 in time_pref:
                text_desc = ('morning')
                query_add = ('(%s >= %s AND %s <= %s)' % (direction_time, time_splits[1][0], direction_time, time_splits[1][1]))
            if 2 in time_pref:
                text_desc = ('afternoon and evening')
                query_add = ('(%s >= %s AND %s <= %s)' % (direction_time, time_splits[2][0], direction_time, time_splits[2][1]))
            if 3 in time_pref:
                text_desc = ('no red-eyes')
                query_add = ('(%s >= %s OR %s <= %s)' % (direction_time, time_splits[3][0], direction_time, time_splits[3][1]))
        return [text_desc, query_add]


    def asign_id(self, dep_time_pref, ret_time_pref, stop_pref, airline_pref):

        if self.flight_type == 'rt':
            to_match = {'dep_time_pref': dep_time_pref, 'ret_time_pref': ret_time_pref, 'stop_pref': stop_pref}
        if self.flight_type == 'ow':
            to_match = {'dep_time_pref': dep_time_pref, 'stop_pref': stop_pref}
        self.to_match = to_match
        self.id = [key for (key,value) in self.id_list.items() if value == to_match][0]


class sim_errors(object):

    def __init__(self, db, origin, destination, flight_type, lockin_per, start_date, d_date1, d_date2, r_date1, r_date2, final_proj_week, max_trip_length, geography):

        self.error_list = []
        self.check_inputs(db, origin, destination, flight_type, lockin_per, start_date, d_date1, d_date2, r_date1, r_date2, final_proj_week, max_trip_length, geography)

        self.error_desc = dict() # descriptions of each error code
        self.error_desc[0] = 'No error'
        self.error_desc[1] = 'Sorry, something went wrong.'
        self.error_desc[2] = 'Dates are either not in valid date format or are empty.'
        self.error_desc[3] = 'Selected holding period is too long relative to selected flight dates.'
        self.error_desc[4] = 'Return flights must leave after all departure flight dates.'
        self.error_desc[5] = 'Return flights must leave within %s weeks of departure.' % (max_trip_length)
        self.error_desc[6] = 'Must search flights that leave sooner than twenty four weeks from today.'
        self.error_desc[7] = 'Must select both a departure and return airport.'
        self.error_desc[8] = 'Cannot depart from and travel to same airport.'
        self.error_desc[9] = 'Sorry, we are not currently covering this departure location.'
        self.error_desc[10] = 'Sorry, we are not currently covering this return location.'
        self.error_desc[11] = 'Sorry, there was insufficient data to calculate your voucher value. Your search was re-run with more relaxed criteria.'
        self.error_desc[12] = 'Sorry, there was insufficient data to calculate your voucher value. Please try another search.'
        self.error_desc[13] = 'The steadyfare is set to expire prior to current date.'
        self.error_desc[14] = 'There are no flights available for some of the travel dates selected.'
        self.error_desc[15] = 'Sorry, date ranges for both departures and returns must not exceed seven days.'
        self.error_desc[16] = 'Sorry, we are currently not offering our product on this route for the travel dates selected.'


    def check_inputs(self, db, origin, destination, flight_type, lockin_per, start_date, d_date1, d_date2, r_date1, r_date2, final_proj_week, max_trip_length, geography):

        if (type(d_date1) is not datetime.date) or (type(d_date2) is not datetime.date) or (type(r_date1) is not datetime.date) or (type(r_date2) is not datetime.date):
            self.error_list.append(2)
        else:
            if  lockin_per < final_proj_week:
                self.error_list.append(3)
            if d_date2 >= r_date1:
                self.error_list.append(4)
            if r_date1 - d_date2 > datetime.timedelta(days = (max_trip_length*7)):
                self.error_list.append(5)
            if d_date2 - start_date > datetime.timedelta(days = 24*7):
                self.error_list.append(6)
            if start_date + datetime.timedelta(days = 7 * lockin_per) > d_date1:
                self.error_list.append(13)
            if (d_date2-d_date1).days > 7 or (r_date2-r_date1).days > 7:
                self.error_list.append(15)

        if (origin == "") or (destination == ""):
            self.error_list.append(7)
        else:
            if origin == destination:
                self.error_list.append(8)
            else:
                if db.sel_crit('one', 'hubs_%s' % (geography), ['*'], {'Airport': origin}) is None:
                    self.error_list.append(9)
                if db.sel_crit('one', 'destinations_%s' % (geography), ['*'], {'Airport': destination}) is None:
                    self.error_list.append(10)
        return self.error_list


    def describe(self):
        descriptions = dict()
        for e in self.error_list:
            descriptions[e] = self.error_desc[e]
        return descriptions



class weekday_pairs(object):

    def __init__(self, flight_type, order_matters=False):

        self.flight_type = flight_type
        self.order_matters = order_matters

        self.weekday_cats = {'low': [1,2],
                            'med': [0,3,5],
                            'high': [4,6],
                            }
        """
        self.weekday_cats = {'low': [0,1,2],
                            'high': [3,4,5,6],
                            }
        """
        self.generate_ids()


    def asign_id(self, weekday_dep, weekday_ret=None):

        self.dep_cat = self.find_weekday_cat(weekday_dep)

        if self.flight_type == 'rt':
            self.ret_cat = self.find_weekday_cat(weekday_ret)
        else:
            self.ret_cat = None

        pair_ids = copy.deepcopy(self.pair_ids)
        for k, v in pair_ids.iteritems():
            if self.order_matters:
                if self.flight_type == 'rt':
                    if self.dep_cat == v[0] and self.ret_cat == v[1]:
                        id = k
                        break
                else:
                    if self.dep_cat == v[0]:
                        id = k
                        break
            else:
                if self.dep_cat in v:
                    v.remove(self.dep_cat)
                if self.ret_cat:
                    if self.ret_cat in v:
                        v.remove(self.ret_cat)
                if len(v) == 0:
                    id = k
                    break
        try:
            return id
        except:
            return None


    def generate_ids(self):

        bank = []
        keylist = self.weekday_cats.keys()
        keylist.sort()
        for i in keylist:
            bank.append(i)

        count = 1
        self.pair_ids = dict()
        for i in range(len(bank)):
            if self.flight_type == 'rt':
                start = 0 if self.order_matters else i

                for j in range(start, len(bank)):
                    self.pair_ids[count] = [bank[i], bank[j]]
                    count += 1
            else:
                self.pair_ids[count] = [bank[i]]
                count += 1


    def find_weekday_cat(self, weekday):

        for k, v in self.weekday_cats.iteritems():
            if weekday in v:
                val = k
        try:
            return val
        except:
            return None


    def travel_date_combos(self, depart_beg, num_days_dep, return_beg=None, num_days_ret=None):

        date_combos = dict()

        def fill_dict(date_combos, id, weekday_1, weekday_2):
            id = self.asign_id(weekday_1, weekday_2)
            if id in date_combos:
                date_combos[id] += 1
            else:
                date_combos[id] = 1
            return date_combos


        for i in range(num_days_dep):
            weekday_1 = (depart_beg + datetime.timedelta(days = i)).weekday()
            if self.flight_type == 'rt':
                for j in range(num_days_ret):
                    weekday_2 = (return_beg + datetime.timedelta(days = j)).weekday()
                    date_combos = fill_dict(date_combos, id, weekday_1, weekday_2)
            else:
                weekday_2 = None
                date_combos = fill_dict(date_combos, id, weekday_1, weekday_2)

        return date_combos


    def tag_query_values(self):

        self.weekday_cats

        bank = dict()
        keylist = self.weekday_cats.keys()
        keylist.sort()
        val = 1
        for index, i in enumerate(keylist):
            if self.order_matters:
                val = (index + 1)
            else:
                val *= 2
            bank[val] = (self.weekday_cats[i],i)

        weekday_ids = {}
        for i in range(0,7):
            for k, v in bank.iteritems():
                if i in v[0]:
                    weekday_ids[i] = k

        depart_tag = "If(day_tag_d=0,%s,If(day_tag_d=1,%s,If(day_tag_d=2,%s,If(day_tag_d=3,%s,If(day_tag_d=4,%s,If(day_tag_d=5,%s,If(day_tag_d=6,%s,NULL))))))) as day_tag_d_cat " % (weekday_ids[0], weekday_ids[1], weekday_ids[2], weekday_ids[3], weekday_ids[4], weekday_ids[5], weekday_ids[6])
        return_tag = "If(day_tag_r=0,%s,If(day_tag_r=1,%s,If(day_tag_r=2,%s,If(day_tag_r=3,%s,If(day_tag_r=4,%s,If(day_tag_r=5,%s,If(day_tag_r=6,%s,NULL))))))) as day_tag_r_cat " % (weekday_ids[0], weekday_ids[1], weekday_ids[2], weekday_ids[3], weekday_ids[4], weekday_ids[5], weekday_ids[6])

        convert_ids = {}
        for k, v in self.pair_ids.iteritems():
            sum = 0
            for index, i in enumerate(v):
                for m, j in bank.iteritems():
                    if i == j[1]:
                        if self.order_matters and index:
                            m = (index * 10) * m
                        sum += m
            convert_ids[sum] = k

        convert_tags = ''
        end_string = "NULL"
        for k, v, in convert_ids.iteritems():
            if self.order_matters:
                 convert_tags += "If(day_tag_d_cat + (day_tag_r_cat * 10)=%s,%s," % (k, v)
            else:
                convert_tags += "If(day_tag_d_cat + day_tag_r_cat=%s,%s," % (k, v)
            end_string += ')'
        convert_tags += end_string + ' as travel_dates_cat '

        return {'depart_tag': depart_tag, 'return_tag': return_tag, 'convert_tags': convert_tags}


class search_inputs(object):

    def __init__(self, origin = "SFO", destination = "MAD", flight_type = "rt", lockin_per = 2, source = 'temp_',
                 dep_time_pref = [], ret_time_pref = [], stop_pref = [], airline_pref = [], max_trip_length = 6,
                 start_date = datetime.datetime.now().date(), purpose = '',
                 # option price generation specific assumptions
                 d_date1 = datetime.timedelta(days = 33), d_date2 = datetime.timedelta(days = 1),
                 r_date1 = datetime.timedelta(days = 40), r_date2 = datetime.timedelta(days = 1),
                 cycles = 1000, wtp = 0, wtpx = 0, buffer = 7.5, correl_coef = 1, round_to = 1,
                 # projection specific assumptions
                 num_wks_proj_out = 20, final_proj_week = 1, first_proj_week = 20, num_per_look_back = 10, depart_length_width = 1, width_of_avg = 1, # width_of_avg greater than 1 relaxes searches for current price as well as minimum summary stats for finding changes in value
                 num_high_days = 1, min_change = None, weight_on_imp = 1, ensure_suf_data = .8, regressed = False, seasonality_adjust = False,
                 geography = "us", black_list_error=.9,
                 ):


        # general inputs
        self.start_date = self.format_as_date(start_date)
        self.origin = origin
        self.destination = destination
        self.flight_type = flight_type
        self.lockin_per = lockin_per
        self.prefs = preferences(flight_type, dep_time_pref, ret_time_pref, stop_pref, airline_pref)
        self.source = source
        self.route = '%s_%s' % (self.origin, self.destination)
        self.final_proj_week = final_proj_week   # the smallest number of weeks before departure that fares can be held until
        self.max_trip_length = max_trip_length
        self.geography = geography
        if not source:
            self.db_proj_source = "steadyfa_sf_model"
        else:
            self.db_proj_source = "steadyfa_temp_tables"

        if 'simulation' in purpose:
            # simulation assumptions
            self.cycles = cycles
            self.wtp = wtp
            self.wtpx = wtpx
            self.buffer = buffer # wtp must be at least this much greater than anticipated cost before use of "cost +" pricing takes effect
            self.correl_coef = correl_coef
            self.round_to = round_to # this sets the multiple holding prices are rounded to
            self.d_date1 = self.format_as_date(d_date1, start_date)
            self.d_date2 = self.format_as_date(d_date2, self.d_date1)
            self.r_date1 = self.format_as_date(r_date1, start_date)
            self.r_date2 = self.format_as_date(r_date2, self.r_date1)


        if 'projection' in purpose:
            # projection assumptions
            self.weight_on_imp = weight_on_imp
            if self.weight_on_imp == 1:
                self.earliest_source_date = self.format_as_date(datetime.timedelta(weeks = -(num_per_look_back + 1)), start_date)
            else:
                self.earliest_source_date = self.format_as_date(datetime.timedelta(weeks = -(first_proj_week + num_per_look_back + 1)), start_date)
            self.num_high_days = num_high_days
            self.num_wks_proj_out = num_wks_proj_out
            self.first_proj_week = first_proj_week     # the number of weeks before departure in which projections are calculated
            self.num_per_look_back = num_per_look_back
            self.width_of_avg = width_of_avg
            self.depart_length_width = depart_length_width
            self.min_change = min_change
            self.end_period = self.start_date + datetime.timedelta(days = -1)
            self.beg_period = self.end_period + datetime.timedelta(days = -6)
            self.type = type
            self.ensure_suf_data = ensure_suf_data
            self.regressed = regressed
            self.seasonality_adjust = seasonality_adjust
            self.black_list_error = black_list_error

    def format_as_date(self, arg, start_date=None):
        if type(arg) is not datetime.date:
            if type(arg) is datetime.datetime:
                arg = arg.date()
            if type(arg) is datetime.timedelta:
                arg = start_date + arg
            elif "/" in arg:
                arg = datetime.datetime.strptime(arg,'%m/%d/%Y').date()
            elif ":" in arg:
                arg = datetime.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S').date()
            elif "-" in arg:
                arg = datetime.datetime.strptime(arg,'%Y-%m-%d').date()
        return arg


    def acquire_attributes(self, inputs):
        d = inputs.__dict__
        ks = []
        vs = []
        for k, v in d.items():
            ks.append(k)
            vs.append(v)
        self.__dict__ = dict(zip(ks, vs))


    def initialize(self, inputs):
        self.acquire_attributes(inputs)


    def __str__(self):
        inputs = []
        d = self.__dict__
        for k, v in d.items():
            inputs.append("%s:  %s" % (k, v))
        inputs = sorted(inputs)
        return '\n'.join(inputs)


if __name__ == "__main__":
    example = search_inputs()
    print example

    db_status = db()
    tables = db_status.show_tables()
    print tables