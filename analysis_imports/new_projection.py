from multi_model import *

class Projection(object):


  def __init__(self, route, historical_windows=(1,2,4,8), proj_date=None):
    self.proj_model = MachineLearn()
    self.route = route
    self.historical_windows = historical_windows
    self.proj_date = proj_date


  def load_model(self, source):
    self.proj_model.load_saved_model('%s' % (source))


  def build_inputs(self,max_date_collected=None, min_date_collected=None):
    """
    @summary: Creates input table for running/fitting the model_type
    @todo: Update this function to not simply re-create and replace inputs tables, but to append where neccessary
    @todo: Update to move inputs table to alternate database
    """

    # fix pop inputs function, currently splits two types of anlaysis, but they should be combined

    #try:
    temp_db = DB(db="steadyfa_temp_tables", cursorclass=MySQLdb.cursors.DictCursor)
    temp_db.join_fares(self.route, max_date_collected=max_date_collected, min_date_collected=min_date_collected)
    print "joined"
    """
    #unique_inputs = temp_db.pop_inputs(self.route, self.historical_windows)
    print "found unique"
    temp_db.find_hist_analysis(self.route, self.historical_windows,)
    print "found historical movement"
    #temp_db.join_fares_on_hist_analysis(self.route)
    #print "joined tables"
    temp_db.db_disconnect()
    print "Created '%s' inputs" % (self.route)
    """
    #except Exception as err:
    #  print "Did not create '%s' inputs: %s" % (self.route, err)


  def fit_model(self, dist_look_back=20, hyper={'static': {'max_depth': 10, 'loss':'ls','n_estimators':50}}, alg=GradientBoostingRegressor, thin_data=0.3, impute=False, remove_empty_vals=False):

    """
    @todo: Find a way to remove looping/iterating when imputing values
    """
    cats = ('date_avg_fare', 'date_st_dev_fare', 'length_avg_change', 'length_st_dev_change')
    look_back_date = self.proj_date - datetime.timedelta(weeks = dist_look_back)
    temp_db = DB(db="steadyfa_temp_tables")
    # consider filtering on date_completed
    table = numpy.asarray(temp_db.sel_crit('all', '%s_inputs' % (self.route), ['*'], greater={'date_collected': look_back_date}, less={'date_collected': self.proj_date}))
    columns = temp_db.get_cols('%s_inputs' % (self.route))
    temp_db.db_disconnect()


    if impute:

      invalid_indices = {}
      for i in ('depart','return'):
        for c in cats:
          for index, j in enumerate(self.historical_windows):
            invalid_indices['%s_%s_%s' % (i,c,j)] = numpy.ma.masked_values(table[:,columns.index('%s_%s_%s' % (i,c,j))], None).mask


      # create bank of average changes between values in each historical window
      ag_change_bank = {'forward': {}, 'backward': {}}

      for i in ('depart','return'):
        for c in cats:
            for direction in ('forward','backward'):
              for index, j in enumerate(self.historical_windows):

                if (index == 0 and direction == 'forward') or (index == (len(self.historical_windows)-1) and direction == 'backward'):
                  pass
                else:

                  current = '%s_%s_%s' % (i,c,j)
                  adjusted_index = (index-1) if direction == 'forward' else (index+1)
                  adjusted = '%s_%s_%s' % (i,c,self.historical_windows[adjusted_index])
                  one = invalid_indices[current]

                  if one.size > 1:
                    if invalid_indices[adjusted].size > 1:
                      two = invalid_indices[adjusted]
                    else:
                      two = numpy.empty((one.size,))
                      two[:] = False
                    com = numpy.vstack((one.T,two.T)).T

                    # figure out how to remove this generator and check for multiple conditions with numpy
                    calc_indices = [cal_in for cal_in, line in enumerate(com.tolist()) if not line[0] and not line[1]]
                    divs = numpy.divide(table[:,columns.index(current)][calc_indices], table[:,columns.index(adjusted)][calc_indices]).mean()
                    ag_change_bank[direction][current] = divs

      self.ag_change_bank = ag_change_bank
      #pprint(ag_change_bank)


      # use values from avg change bank to impute missing values in inputs
      for i in ('depart','return'):
        for c_index, c in enumerate(cats):
            for hist_index in range(len(self.historical_windows)):

                current_item = '%s_%s_%s' % (i,c,self.historical_windows[hist_index])

                prev_item = '%s_%s_%s' % (i,c,self.historical_windows[hist_index - 1]) if hist_index != 0 else None
                following_item = '%s_%s_%s' % (i,c,self.historical_windows[hist_index + 1]) if  (hist_index + 1) != len(self.historical_windows) else None

                # find imputed values if any data is missing
                if invalid_indices[current_item].size > 1:

                  # try forward moving method
                  if prev_item:
                    rel_set = numpy.ma.masked_values(table[:,columns.index(prev_item)][invalid_indices[current_item]],None)
                    one = rel_set.data
                    one[numpy.invert(rel_set.mask)] = one[numpy.invert(rel_set.mask)] * float(ag_change_bank['forward'][current_item])
                  else:
                    one = numpy.empty((table[:,columns.index(current_item)][invalid_indices[current_item]].size,1,), dtype=numpy.object)
                    one[:] = None


                  # try backward moving method
                  if following_item:
                    rel_set = numpy.ma.masked_values(table[:,columns.index(following_item)][invalid_indices[current_item]],None)
                    two = rel_set.data
                    two[numpy.invert(rel_set.mask)] = two[numpy.invert(rel_set.mask)] * float(ag_change_bank['backward'][current_item])
                  else:
                    two = numpy.empty((table[:,columns.index(current_item)][invalid_indices[current_item]].size,1,), dtype=numpy.object)
                    two[:] = None


                  # combine, average when possible, and replace
                  com = numpy.vstack((one.T,two.T)).T
                  calc_indices = [ind for ind, line in enumerate(com.tolist()) if line[0] or line[1]]   # figure out how to remove this generator and check for multiple conditions with numpy
                  com_m = numpy.ma.masked_values(com[calc_indices], None)
                  if com_m.mask.size > 1:
                    # figure out how to get rid of this iterator
                    averages = []
                    for n in range(com_m.data.shape[0]):
                      nm = numpy.ma.masked_values(com_m.data[n], None)

                      averages.append(numpy.mean(numpy.ma.masked_array(nm.data,nm.mask)))
                    #averages = numpy.mean(numpy.ma.masked_array(com_m.data,com_m.mask))
                  else:
                    averages = numpy.mean(com_m.data,1)

                  table[:,columns.index(current_item)][calc_indices] = averages


    # delete rows that contain None values
    if remove_empty_vals:
      for i in ('depart','return'):
        for c_index, c in enumerate(cats):
          for hist_index in range(len(self.historical_windows)):
            column = '%s_%s_%s' % (i,c,self.historical_windows[hist_index])
            mask_inds = numpy.ma.masked_values(table[:,columns.index(column)], None)

            if numpy.invert(mask_inds.mask).size > 1:
              table = table[numpy.invert(mask_inds.mask)]

    table = numpy.vstack((columns,table))

    data = DataSet(('%s_inputs' % (self.route),table), db_name=None, target_index='rel_inc', thin_data=thin_data, ignore=('id', 'count','date_collected','abs_inc','beg_price','end_price'))
    self.proj_model = MachineLearn(source=data, supervised_model=alg)
    self.proj_model.quick_fit(hyper=hyper, test_data_end=0.2)
    pprint(self.proj_model.sup_metrics)
    self.proj_model.save_model("%s_%s" % (self.route,self.proj_date))


  def build_price_change_estimates(self):

    temp_db = DB(db="steadyfa_temp_tables")
    recent_fares = numpy.asarray(temp_db.sel_crit('all', '%s_min_fares' % (self.route), ['*'], greater={'date_collected': (self.proj_date-datetime.timedelta(days=3))}, less={'date_collected': self.proj_date}))
    print recent_fares.shape
    temp_db.db_disconnect()
    """
    primary_inps = []
    for d in depart_length:
      for t in trip_length:
        for p in range(3,d,3):
          depart_date = self.proj_date + datetime.timedelta(days = d)
          return_date = depart_date + datetime.timedelta(days = t)
          #primary_inps.append({'date_collected': self.proj_date, 'depart_date': depart_date, 'return_date': return_date, 'proj_length': p})
          primary_inps.append({'date_collected': self.proj_date, 'depart_date': depart_date, 'return_date': return_date, 'proj_length': p})


    temp_db = DB(db="steadyfa_temp_tables", cursorclass=MySQLdb.cursors.DictCursor)
    hist_movement = temp_db.find_hist_analysis(self.route, primary_inps, historical_windows=self.historical_windows)
    """

    """
    X_inp = []
    for d in range(20,31):
      for r in [3,6,9,12]:
        date_collected = datetime.date(2013,3,1)
        depart_date =  date_collected + datetime.timedelta(days = d)
        return_date =  depart_date + datetime.timedelta(days = r)

        X_inp.append([10,datetime.date(2013,3,1), d, r, d+r, depart_date, return_date, depart_date.weekday(), return_date.weekday(),1])
    X_inp.insert(0,example.proj_model.data.unexpanded_columns[:])
    X_inp = numpy.asarray(X_inp)
    """

    #self.proj_inputs = inputs
    #self.projections = self.proj_model.predict_on_fitted(inputs,)

  def graph_projections(self,column, group=True):
      try:
        fig, axes = pl.subplots()
        fig.suptitle("Projections")
        fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3)

        agg_proj = pl.subplot2grid((1,1), (0,0), colspan=1)


        def build_plot(sub_plot, group, projection_data, title):
          x_axis_input_index = self.proj_inputs[0].tolist().index(column)
          if not group:
            sub_plot.scatter(self.proj_inputs[1:,x_axis_input_index], projection_data, lw=2, label = title)
          else:
            grouped = []
            unique_xs = numpy.unique(self.proj_inputs[1:, x_axis_input_index])
            for i in unique_xs:
              indexes = numpy.where(self.proj_inputs[1:, x_axis_input_index]==i)
              grouped.append(numpy.mean(projection_data[indexes]))
            sub_plot.plot(unique_xs, grouped, lw=2, label = '%s grouped' % (title))
          return sub_plot

        agg_proj = build_plot(agg_proj, group, self.projections['standard'], 'standard set')
        if 'prediction_probability_intervals' in self.projections:
          for index, i in enumerate(self.projections['prediction_probability_intervals'][0]):
              agg_proj = build_plot(agg_proj, group, self.projections['prediction_probability_intervals'][1][:,index], 'quantile - %s' % (i))

        agg_proj.legend(loc=0)
        agg_proj.set_xlabel('%s' % (column))
        agg_proj.set_ylabel('Fare')
        agg_proj.set_title('Aggregate')
        pl.show()

      except:
        print "No projections to display"


  def est_current_fares(self, departing, returning):

    temp_db = DB(db="steadyfa_temp_tables")
    raw_fares = numpy.asarray(temp_db.recent_min_fares(self.route, departing, returning))
    temp_db.db_disconnect()

    return raw_fares[:,3].max()


if __name__ == "__main__":

  start = time.time()

  example = Projection('SFOHNL') # proj_date=datetime.date(2013,4,1)
  example.build_inputs()
  #print example.est_current_fares((datetime.date(2013,5,12),datetime.date(2013,5,20)), (datetime.date(2013,6,12),datetime.date(2013,6,20)))
  #example.load_model('sfojfk_inputs_GradientBoostingRegressor_2013-06-28_sfojfk_2013-04-01')
  #example.build_price_change_estimates()


  """
  data = DataSet('sfojfk_price_change_source_hist_movement', db_name='steadyfa_temp_tables', thin_data=0.4, target_index='rel_inc', ignore=('id', 'count','date_collected', 'date_completed', 'depart_date', 'return_date', 'abs_inc','beg_price','end_price'))
  example = MachineLearn(data, supervised_model=RandomForestRegressor)
  example.run_supervised() # test_data_end=True

  #example = MachineLearn()
  #example.load_saved_model('sfojfk_inputs_GradientBoostingRegressor_2013-06-28_no_count_og_data')

  example.show_graph()
  pprint(example.sup_metrics)
  """

  print "end of script in %s seconds" % (time.time()-start)
