from functions import *
import numpy
import numpy as np
import pylab as pl
import datetime
from scipy.stats import kde
from scipy import stats
import pandas as pd
from dateutil.relativedelta import *
import csv

from sklearn.neighbors.kde import KernelDensity
from sklearn.grid_search import GridSearchCV

class NonPModel(object):

  def __init__(self, data, single_d, use_grid_search=False, kde_bandwidth=None):

    #mod = kde.gaussian_kde(data, .1)
    #mod = KernelDensity(kernel='gaussian', bandwidth=0.015).fit(data[:, numpy.newaxis])

    if len(data.shape) == 1:
      data = data[:, numpy.newaxis]

    if use_grid_search:
      params = {'bandwidth': numpy.logspace(-1, 2, 20)}
      grid = GridSearchCV(KernelDensity(kernel='gaussian'), params)
      grid.fit(data)
      print "best bandwidth: {0}".format(grid.best_estimator_.bandwidth)
      mod = grid.best_estimator_
    else:
      if single_d:
        bandwidth = 0.015 if not kde_bandwidth else kde_bandwidth
      else:
        bandwidth = 0.05 if not kde_bandwidth else kde_bandwidth

      mod = KernelDensity(kernel='gaussian', bandwidth=bandwidth).fit(data)
    self.kde = mod


  def fill_values(self, bins):
    try:
      return self.kde(bins).tolist()
    except:
      bins = numpy.asarray(bins)[:, numpy.newaxis]
      return numpy.exp(self.kde.score_samples(bins)).tolist()

  def resample(self, size):
    try:
      samples = self.kde.resample(size=2000)[0]
    except:
      samples = self.kde.sample(n_samples=2000)
    return samples


class FareMovement(object):

  def __init__(self, route, depart_length =[0,1000], date_completed=[datetime.date(2000,1,1), datetime.date(3000,1,1)], proj_interval=7, dep_wkday=None, ret_wkday=None):

    # save params to self
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    del values['self']
    del values['frame']
    self.__dict__.update(values)

    self.sum_stats = []
    self.models = {'flat': [], 'by_fare': []}

    self.DB = db(db='steadyfa_temp_tables')

  def test_model(self, test_offset=None, grouped=True):

    # change test offset to look at date collected, not completed
    if test_offset:
      test_date_collected = [self.date_completed[1], (self.date_completed[1]+test_offset)]
    else:
      test_date_collected = [self.date_completed[1], (self.date_completed[1]+datetime.timedelta(weeks=1))]


    if grouped:
      # build list of service fees to charge based on value of fare
      stats_bank = []
      for i in self.sum_stats['grouped']:
        group_bank = []
        for j in i:
          group_bank.append([j['min_fare'], j['mean']])
        group_bank = numpy.asarray(group_bank)
        group_bank = group_bank[group_bank[:,0].argsort()]
        # change first fare item to 0
        group_bank[0,0] = 0
        stats_bank.append(group_bank.tolist())
    else:
      stats_bank = self.sum_stats['full']

    full_sim_sum = []
    for index, p in enumerate(stats_bank):

        proj_length = [(index+1)*self.proj_interval-3,(index+1)*self.proj_interval+3]

        if self.dep_wkday or self.ret_wkday:
          where = {}
          if self.dep_wkday:
            where['day_tag_d'] = self.dep_wkday
          if self.ret_wkday:
            where['day_tag_r'] = self.ret_wkday
        else:
          where = None

        res = self.DB.sel_crit('all', '%s_price_change_source' % (self.route), ['beg_price','end_price','date_completed', 'rel_inc', 'depart_date', 'return_date', 'date_collected'], where=where, greater={'proj_length': proj_length[0], 'depart_length': self.depart_length[0], 'date_collected': test_date_collected[0]}, less={'proj_length': proj_length[1], 'depart_length': self.depart_length[1], 'date_collected': test_date_collected[1]})

        sim_res = []
        temp_store = []
        threshold = 1

        count = 0
        for ind, i in enumerate(res):
          count = ind + 1
          if not grouped:
            fee_rate = p['mean'] - 1
          else:
            for f in p:
              if i[0] > f[0]:
                fee_rate = f[1] - 1

          if fee_rate < threshold:
            locked_fare = i[0]
            opt_val = i[0] * (fee_rate)
            boost = 0
          else:
            boost = fee_rate - threshold
            locked_fare = i[0] * (boost + 1)
            opt_val = i[0] * threshold

          gain = opt_val if locked_fare > i[1] else locked_fare - i[1] + opt_val
          temp_store.append([opt_val, gain, (i[3]-1), i[0]])
          sim_res.append({'beg_price': i[0], 'option_price': opt_val, 'option_price_relative': (opt_val / i[0]), 'locked_fare_increment': boost, 'gain': gain, 'date_completed': conv_date_to_datetime(i[2]), 'rel_inc': (i[3]), 'beg_price': i[0], 'depart_date': conv_date_to_datetime(i[4]), 'return_date': conv_date_to_datetime(i[5]), 'date_collected': conv_date_to_datetime(i[6])})

        temp_store = numpy.asarray(temp_store)
        sim_sum = {}

        try:
          sim_sum['avg_opt'] = numpy.mean(temp_store[:,0])
          sim_sum['avg_gain'] = numpy.mean(temp_store[:,1])
          sim_sum['avg_change'] = numpy.mean(temp_store[:,2])
          sim_sum['avg_beg_price'] = numpy.mean(temp_store[:,3])
        except:
          pass

        if count < 50:
          sample = random.sample(sim_res,count)
        else:
          sample = random.sample(sim_res,50)

        full_sim_sum.append({'index': index, 'count': count, 'summary': sim_sum, 'data': sample})

    return full_sim_sum

  def load_saved_model(self):

    form_date_completed = [conv_date_to_datetime(self.date_completed[0]),conv_date_to_datetime(self.date_completed[1])]
    mongo = mongo_connect()
    res = mongo.models.changes.find({'route': self.route, 'depart_length': self.depart_length, 'date_completed': form_date_completed, 'proj_interval': self.proj_interval, 'dep_wkday': self.dep_wkday, 'ret_wkday': self.ret_wkday}).sort('date_created',-1).limit(1)
    mongo.disconnect()

    for i in res:
      loaded_data = i

    if 'models' in loaded_data.keys():
      for i in loaded_data['models'].keys():
        for ind, m in enumerate(loaded_data['models'][i]):
          loaded_data['models'][i][ind] = pickle.loads(m)

    self.__dict__.update(loaded_data)

  def save(self,):

    data = {'date_created': datetime.datetime.now()}
    data.update(self.__dict__)

    if 'models' in data:
      for i in data['models'].keys():
        for ind, m in enumerate(data['models'][i]):
          data['models'][i][ind] = bson.binary.Binary(pickle.dumps( m, protocol=2))

    if 'DB' in data:
      del data['DB']

    data['date_completed'] = [conv_date_to_datetime(data['date_completed'][0]), conv_date_to_datetime(data['date_completed'][1])]

    try:
      mongo = mongo_connect()
      mongo.models.changes.insert(data)
      mongo.disconnect()
      print "Saved successfully"
    except Exception as err:
      print "Didn't save: %s" % (err)
    finally:
      if self.models:
        for i in self.models.keys():
          for ind, m in enumerate(self.models[i]):
            self.models[i][ind] = pickle.loads(m)

  def est_pos_change(self):

    self.sum_stats = {'full': [], 'grouped': [] }

    for i in range(len(self.models['flat'])):

      # full range model
      samples = self.models['flat'][i].resample(size=3000)
      # change decreasing values to 1
      samples = numpy.where(samples > 1, samples, 1)
      self.sum_stats['full'].append({'mean': numpy.mean(samples), 'median':numpy.median(samples)})

      # grouped by fare ranges
      samples = self.models['by_fare'][i].resample(size=3000)
      samples = samples[samples[:,0].argsort()]
      # change decreasing values to 1
      samples[:,1] = numpy.where(samples[:,1] > 1, samples[:,1], 1)
      grouped = numpy.array_split(samples, 5)
      group_bank = []
      for i in grouped:
        group_bank.append({'min_fare': i[:,0].min(),  'mean': numpy.mean(i[:,1]), 'median':numpy.median(i[:,1])})
      self.sum_stats['grouped'].append(group_bank)

  def show_graph(self,):

      pl.close('all')
      fig, axes = pl.subplots()
      fig.suptitle("%s" % (self.route))
      #fig.tight_layout()
      fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3)

      splits = len(self.data_bank)

      for index, p in enumerate(self.data_bank):

        scat_dat = numpy.asarray(p['scat'])

        hist = pl.subplot2grid((splits,2), (index,0), colspan=1)
        hist.set_xlabel('change in value')
        hist.set_ylabel('frequency')
        hist.set_title('proj_length: %s - %s' % (p['proj_length'][0], p['proj_length'][1]))
        hist.hist(scat_dat[:,1], len(p['bins'])-1, normed=True)

        # add a 'best fit' line
        hist.plot(p['bins'], p['norm_fit'], 'k--', linewidth=1.5)
        # mean line
        hist.axvline(x=p['mean'],color='k',ls='dashed')
        # median line
        hist.axvline(x=p['median'],color='g',)
        # kernel density function
        hist.plot(p['bins'], p['nonp_fit'], 'y-')
        """
        scat = pl.subplot2grid((splits,2), (index,1), colspan=1)
        samples = self.models[index].resample(size=2000)
        scat.hist(samples, len(p['bins'])-1, normed=True)
        scat.plot(p['bins'], p['nonp_fit'], 'y-')
        """

        scat = pl.subplot2grid((splits,2), (index,1), colspan=1)
        scat.set_xlabel('date completed')
        scat.set_ylabel('change in price')
        scat.set_title('proj_length: %s - %s' % (p['proj_length'][0], p['proj_length'][1]))
        scat.scatter(scat_dat[:,0], scat_dat[:,1])


      fig = pl.figure()

      for index, p in enumerate(self.data_bank):
        """
        abs_plot = numpy.asarray(p['change_by_fare_sum'][1])
        rel_plot = numpy.asarray(p['change_by_fare_sum'][0])

        sub = pl.subplot2grid((splits,2), (index,0), colspan=1)
        sub.fill_between(rel_plot[:,0], (numpy.amin(rel_plot[:,2])-0.1), rel_plot[:,1], facecolor="white", alpha=0)
        sub.fill_between(rel_plot[:,0], rel_plot[:,1], rel_plot[:,2], facecolor="#CC6666")
        sub.fill_between(rel_plot[:,0], rel_plot[:,2], rel_plot[:,3], facecolor="#1DACD6")
        sub.fill_between(rel_plot[:,0], rel_plot[:,3], rel_plot[:,4], facecolor="#6E5160")
        sub.fill_between(rel_plot[:,0], rel_plot[:,4], rel_plot[:,5])
        sub.yaxis.grid(True)

        sub = pl.subplot2grid((splits,2), (index,1), colspan=1)
        sub.set_xlim(numpy.amin(abs_plot[:,0])-5, numpy.amax(abs_plot[:,0])+5)
        sub.fill_between(abs_plot[:,0], (numpy.amin(abs_plot[:,2])-0.1), abs_plot[:,1], facecolor="white", alpha=0)
        sub.fill_between(abs_plot[:,0], abs_plot[:,1], abs_plot[:,2], facecolor="#CC6666")
        sub.fill_between(abs_plot[:,0], abs_plot[:,2], abs_plot[:,3], facecolor="#1DACD6")
        sub.fill_between(abs_plot[:,0], abs_plot[:,3], abs_plot[:,4], facecolor="#6E5160")
        sub.fill_between(abs_plot[:,0], abs_plot[:,4], abs_plot[:,5])
        sub.yaxis.grid(True)
        """
        scat = pl.subplot2grid((splits,2), (index,0), colspan=1)
        samples = self.models['by_fare'][index].resample(1500)

        scat.scatter(samples[:,0], samples[:,1])


        rel_plot = numpy.asarray(p['change_by_fare'])
        m1 = rel_plot[:,0]
        m2 = rel_plot[:,1]
        xmin = numpy.min(rel_plot[:,0])
        xmax = numpy.max(rel_plot[:,0])
        ymin = numpy.min(rel_plot[:,1])
        ymax = numpy.max(rel_plot[:,1])


        def forceAspect(ax,aspect=1):
          im = ax.get_images()
          extent =  im[0].get_extent()
          ax.set_aspect(abs((extent[1]-extent[0])/(extent[3]-extent[2]))/aspect)


        X, Y = numpy.mgrid[xmin:xmax:100j, ymin:ymax:100j]
        positions = numpy.vstack([X.ravel(), Y.ravel()]).T
        values = numpy.vstack([m1, m2]).T
        Z = numpy.reshape(numpy.exp(self.models['by_fare'][index].kde.score_samples(positions)).T, X.shape)

        ax = pl.subplot2grid((splits,2), (index,1), colspan=1)
        ax.imshow(numpy.rot90(Z), cmap=pl.cm.gist_earth_r, extent=[xmin, xmax, ymin, ymax])
        ax.plot(m1, m2, 'k.', markersize=2)
        forceAspect(ax,aspect=5)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])


      pl.show()

  def gen_dist(self, n_bins=50, models_only=False, grouped_kde_bandwidth=None):

    self.data_bank = []

    DB = db(db='steadyfa_temp_tables')

    avg_dep_len = int(math.ceil((self.depart_length[0] + self.depart_length[1]) / 2.0))
    max_lockin = (avg_dep_len - 14) if (avg_dep_len - 14) < 28 else 28
    splits = int(math.ceil(max_lockin/self.proj_interval))

    if self.dep_wkday or self.ret_wkday:
      where = {}
      if self.dep_wkday:
        where['day_tag_d'] = self.dep_wkday
      if self.ret_wkday:
        where['day_tag_r'] = self.ret_wkday
    else:
      where = None


    for p in range(splits):

      proj_length = [(p+1)*self.proj_interval-3,(p+1)*self.proj_interval+3]
      temp_data_bank = {'index': p, 'proj_length': proj_length}

      res = self.DB.sel_crit('all', '%s_price_change_source' % (self.route), ['abs_inc', 'rel_inc', 'date_completed', 'date_collected', 'beg_price', 'end_price'], where=where, greater={'proj_length': proj_length[0], 'depart_length': self.depart_length[0], 'date_completed': self.date_completed[0]}, less={'proj_length': proj_length[1], 'depart_length': self.depart_length[1], 'date_completed': self.date_completed[1]})


      vals = numpy.asarray([ [b[4], b[1], b[0]] for b in res])
      vals = vals[vals[:,0].argsort()]

      changes = vals[:,1]
      density = NonPModel(changes, single_d=True)
      self.models['flat'].append(density)

      if grouped_kde_bandwidth:
        self.models['by_fare'].append(NonPModel(vals[:,(0,1)], single_d=False, kde_bandwidth=grouped_kde_bandwidth))
      else:
        self.models['by_fare'].append(NonPModel(vals[:,(0,1)], single_d=False))

      if not models_only:

        temp_data_bank.update({'change_by_fare': vals.tolist() })

        split_inds = vals.shape[0] / n_bins
        vals = numpy.split(vals, numpy.arange(n_bins)*split_inds)

        abs_plot = []
        rel_plot = []
        for ind, r in enumerate(vals):
          try:
            abs_plot.append( [numpy.mean(r[:,0]), stats.scoreatpercentile(r[:,2], 0), stats.scoreatpercentile(r[:,2], 25), stats.scoreatpercentile(r[:,2], 50), stats.scoreatpercentile(r[:,2], 75), stats.scoreatpercentile(r[:,2], 100)] )
            rel_plot.append( [numpy.mean(r[:,0]), stats.scoreatpercentile(r[:,1], 0), stats.scoreatpercentile(r[:,1], 25), stats.scoreatpercentile(r[:,1], 50), stats.scoreatpercentile(r[:,1], 75), stats.scoreatpercentile(r[:,1], 100)] )
          except:
            pass

        temp_data_bank.update({'change_by_fare_sum': (rel_plot, abs_plot) })

        scat = numpy.asarray([ [ time.mktime(i[2].timetuple())*1000 + index , int(i[1]*1000)/1000.00 ] for index, i in enumerate(res)])
        scat = scat[scat[:,0].argsort()]
        temp_data_bank.update({'scat': scat.tolist()})

        beg = numpy.asarray([ [ time.mktime(i[3].timetuple())*1000 + index , int(i[4]*1000)/1000.00 ] for index, i in enumerate(res)])
        beg = beg[beg[:,0].argsort()]
        temp_data_bank.update({'beg': beg.tolist()})

        end = numpy.asarray([ [ time.mktime(i[2].timetuple())*1000 + index , int(i[5]*1000)/1000.00 ] for index, i in enumerate(res)])
        end = end[end[:,0].argsort()]
        temp_data_bank.update({'end': end.tolist()})



        n, bins, patches =  pl.hist(changes, n_bins, normed=True) # , histtype='stepfilled'
        mu, sigma = numpy.mean(changes), numpy.std(changes)
        median = numpy.median(changes)
        fit_line_ys = pl.normpdf( bins, mu, sigma)


        bins = [int(b*100)/100.0 for b in bins]
        fit_line_ys = [int(f*100)/100.0 for f in fit_line_ys]

        temp_data_bank.update({'bins': bins, 'freq': n.tolist(), 'norm_fit': fit_line_ys, 'nonp_fit': density.fill_values(bins), 'mean': mu, 'median': median})

        self.data_bank.append(temp_data_bank)


class Simulation(object):

  def __init__(self, start_date=datetime.date(2012,11,1), weeks=20, routes=['SFOLAX', 'SFOJFK', 'SFOLHR','SFOMAD'], depart_lengths=[[0,9],[10,19],[20,29],[30,39],[40,49]],
                proj_interval=7, look_back_length=8, test_weeks=1, grouped_kde_bandwidth=0.05):

    # save params to self
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    del values['self']
    del values['frame']
    self.__dict__.update(values)
    self.start_date = conv_date_to_datetime(self.start_date)

  def run(self,):

    mongo = mongo_connect()
    global_simulation = {'date_run': datetime.datetime.now(), 'simulation': []}
    global_simulation.update(self.__dict__)
    sim_id = mongo.simulation.practice.insert(global_simulation)


    #full_sim = []
    for r in self.routes:
      for d in self.depart_lengths:
        for i in range(self.weeks):

          print "route: %s  --  depart lengths: %s, %s  --  projection week: %s" % (r, d[0], d[1], i)

          proj_date = self.start_date + datetime.timedelta(weeks=i)
          example = FareMovement(route=r, depart_length=d, proj_interval=self.proj_interval, date_completed=[proj_date-datetime.timedelta(weeks=self.look_back_length), proj_date])
          example.gen_dist(models_only=True, grouped_kde_bandwidth=self.grouped_kde_bandwidth)
          example.est_pos_change()
          sim_res = example.test_model(grouped=True, test_offset=datetime.timedelta(weeks=1))
          sim_meta_data = {'proj_date': conv_date_to_datetime(proj_date), 'route': example.route, 'depart_length': int(math.ceil((example.depart_length[0] + example.depart_length[1])/2.0)), 'week_iter': i}
          #full_sim.append({'sim_meta_data': sim_meta_data, 'sim_results': sim_res})
          mongo.simulation.practice.update({'_id': sim_id}, {'$pushAll': {'simulation': [{'sim_meta_data': sim_meta_data, 'sim_results': sim_res}]}})
          # consider using "save" here


    mongo.disconnect()

  def summarize(self,):

    mongo = mongo_connect()
    query_res = mongo.simulation.practice.find(self.__dict__).sort('date_run', -1).limit(1)

    last_sim = None
    for i in query_res:
      last_sim_id = i['_id']


    bank = []
    curs = mongo.simulation.practice.find({"_id": last_sim_id}, {'simulation.sim_results.index': 1, 'simulation.sim_results.data.gain': 1, 'simulation.sim_meta_data.proj_date': 1,})
    for index, c in enumerate(curs):
      for s in c['simulation']:
        for r in s['sim_results']:
          for d in r['data']:
            bank.append(( pd.to_datetime(s['sim_meta_data']['proj_date'] + datetime.timedelta(days=r['index']*self.proj_interval) ) , d['gain']))
    samp_bank = pd.DataFrame(bank, columns=['exercise_date', 'gain'])

    sum_bank = []
    curs = mongo.simulation.practice.find({"_id": last_sim_id}, {'simulation.sim_results.summary': 1, 'simulation.sim_results.count': 1, 'simulation.sim_results.index': 1, 'simulation.sim_meta_data': 1})
    for index, c in enumerate(curs):
      for s in c['simulation']:
        for r in s['sim_results']:
          sum_bank.append(dict({'count': r['count'], 'index': r['index']}.items()  + r['summary'].items() + s['sim_meta_data'].items()))


    def find_weighted_avg(df):
      try:
        sums = df[['count', 'prod_count_gain', 'prod_count_change', 'prod_count_opt', 'prod_count_beg_price']].sum()
        weighted = sums[['prod_count_gain', 'prod_count_change', 'prod_count_opt', 'prod_count_beg_price']] / sums[['count']][0]
        return {'gain': weighted[0], 'change': weighted[1], 'option': weighted[2], 'beg_price': weighted[3], 'count': sums[['count']][0]}
      except:
        return {'gain': None, 'change': None, 'option': None, 'beg_price': None, 'count': None}

    df = pd.DataFrame(sum_bank)
    df['prod_count_gain'] = df['count'] * df['avg_gain']
    df['prod_count_change'] = df['count'] * df['avg_change']
    df['prod_count_opt'] = df['count'] * df['avg_opt']
    df['prod_count_beg_price'] = df['count'] * df['avg_beg_price']
    df['exercise_date'] = datetime.datetime(2000,1,1,0,0)

    groups = df.groupby(df['index']).groups
    for k, v in groups.iteritems():
      days = int(self.proj_interval * (k+1))
      df['exercise_date'][v] = df['proj_date'][v] + datetime.timedelta(days = days)

    sim_summary_bank = {}
    inds = df['index'].unique()


    # global performance
    global_summary = {'global': {}}
    for i in inds:
      global_summary['global'][(i+1)*self.proj_interval] = find_weighted_avg(df[df['index']==i])
    sim_summary_bank['global'] = global_summary


    # by depart lengths
    dep_lens = {}
    for i in self.depart_lengths:
      avg_dep_len = int(math.ceil((i[0] + i[1]) / 2.0))
      dep_lens[avg_dep_len] = {}
      for j in inds:
        dep_lens[avg_dep_len][(j+1)*self.proj_interval] = find_weighted_avg(df[(df['depart_length']==avg_dep_len) & (df['index']==j)])
    sim_summary_bank['depart_length'] = dep_lens


    # by routes
    routes = {}
    for i in self.routes:
      routes[i] = {}
      for j in inds:
        routes[i][(j+1)*self.proj_interval] = find_weighted_avg(df[(df['route']==i) & (df['index']==j)])
    sim_summary_bank['routes'] = routes


    # by proj_date
    groups = df.groupby(df['proj_date']).groups
    proj_dates = {}
    for k, v in groups.iteritems():
      proj_dates[k] = {}
      for j in inds:
        proj_dates[k][(j+1)*self.proj_interval] = find_weighted_avg(df.loc[v][df['index']==j])
    sim_summary_bank['projection_date'] = proj_dates


    # by exercise date
    groups = df.groupby(df['exercise_date']).groups
    ex_dates = {}
    for k, v in groups.iteritems():
      ex_dates[k] = {}
      for j in inds:
        ex_dates[k][(j+1)*self.proj_interval] = find_weighted_avg(df.loc[v][df['index']==j])
    sim_summary_bank['exercise_date'] = ex_dates


    # by exercise date by route
    groups = df.groupby(df['exercise_date']).groups
    ex_dates_r = {}
    for k, v in groups.iteritems():
      ex_dates_r[k] = {}
      for j in self.routes:
        ex_dates_r[k][j] = find_weighted_avg(df.loc[v][df['route']==j])
    sim_summary_bank['exercise_date_by_route'] = ex_dates_r


    # limit random samples to one month ranges in exp dates
    # assumes 28 days is max lockin length and therefore it is not possible to have options expiring more than 28 days apart at one time
    dates = pd.DataFrame([pd.to_datetime(d) for d in groups.keys()], columns=['date']).sort_index(by='date')['date']
    sort_dates = pd.DataFrame([d for d in dates], columns=['date'])['date']
    num_ex_dates = sort_dates.count()

    # find sales risk by volume
    quantity_risk = {}
    volumes = [10, 50, 100, 250, 1000]
    for v in volumes:
      avg_gain = []
      for i in range(500):
        start_ind = 0 if num_ex_dates < 5 else random.randrange(num_ex_dates-3)
        month_samps = samp_bank[ (samp_bank['exercise_date']>=sort_dates[start_ind]) & (samp_bank['exercise_date']<=sort_dates[start_ind] + pd.tseries.offsets.DateOffset(days=28))]
        samp_size = v if month_samps['gain'].count() >= v else month_samps['gain'].count()
        avg_gain.append(numpy.asarray(random.sample(month_samps['gain'], samp_size)).mean())

        # avg_gain.append(numpy.random.choice(bank,v).mean())
      quantity_risk[v] = {1: numpy.percentile(avg_gain,1), 25: numpy.percentile(avg_gain,25), 50: numpy.percentile(avg_gain,50), 75: numpy.percentile(avg_gain,75), 99: numpy.percentile(avg_gain,99)}
    sim_summary_bank['risk_by_volume'] = quantity_risk


    # plot by depart_length
    dep_len_plt = {}
    for k, v in sim_summary_bank['depart_length'].iteritems():
      dep_len_plt[k] = {}
      for k2, v2 in v.iteritems():
        dep_len_plt[k][k2] = v2['option']

    dfp = pd.DataFrame.from_dict(dep_len_plt, orient='index')
    dfp.plot(title='Option Price by Number of Days Before Departure').invert_xaxis()


    # plot by sale date
    ex_date_plt = {}
    for k, v in sim_summary_bank['projection_date'].iteritems():
      ex_date_plt[pd.to_datetime(k)] = {}
      for k2, v2 in v.iteritems():
        ex_date_plt[pd.to_datetime(k)][k2] = v2['gain']

    dfp = pd.DataFrame.from_dict(ex_date_plt, orient='index')
    dfp.plot(title='Average Gain per Option by Date of Sale')



    # plot by exercise date
    ex_date_plt = {}
    for k, v in sim_summary_bank['exercise_date'].iteritems():
      ex_date_plt[pd.to_datetime(k)] = {}
      for k2, v2 in v.iteritems():
        ex_date_plt[pd.to_datetime(k)][k2] = v2['gain']

    dfp = pd.DataFrame.from_dict(ex_date_plt, orient='index')
    dfp.plot(title='Average Gain per Option by Date of Exercise')


    # plot by exercise date by route
    ex_date_r_plt = {}
    for k, v in sim_summary_bank['exercise_date_by_route'].iteritems():
      ex_date_r_plt[pd.to_datetime(k)] = {}
      for k2, v2 in v.iteritems():
        ex_date_r_plt[pd.to_datetime(k)][k2] = v2['gain']

    dfp = pd.DataFrame.from_dict(ex_date_r_plt, orient='index')
    dfp.plot(title='Average Gain per Option by Date of Exercise by Route')


    # plot risk by sales volume
    dfp = pd.DataFrame.from_dict(sim_summary_bank['risk_by_volume'], orient='index')
    dfp.plot(title="Percentile Risk Per Option By Volume Sales")

    pl.show()

    """
    # print summary to csv
    bank = []
    for k, v in sim_summary_bank.iteritems():
      if k != 'risk_by_volume':
        for k2, v2 in v.iteritems():
          for k3, v3 in v2.iteritems():
            temp = {'group': k, 'series': k2, 'hold_per': k3}
            temp.update(v3)
            bank.append(temp)
    #pprint(bank)

    f = open('sim_sums.csv','wb')
    w = csv.DictWriter(f,bank[0].keys())
    w.writeheader()
    w.writerows(bank)
    f.close()
    """
    return sim_summary_bank




if __name__ == "__main__":
  """
  example = FareMovement(route='SFOLAX', depart_length=[20,30], proj_interval=7)
  example.gen_dist()
  example.est_pos_change()
  pprint(example.sum_stats['full'])
  #example.save()
  #example.load_saved_model()
  #example.show_graph()
  print example.test_model(grouped=True)
  """


  example = Simulation(weeks=20, routes=['SFOLAX', 'SFOJFK', 'SFOMAD'], depart_lengths=[[20,29], [30,39], [40,49], [50,59], [60,69], [70,79]])
  #example = Simulation(weeks=4, routes=['SFOLAX', 'SFOJFK'], depart_lengths=[[20,29],[30,39],])
  #example = Simulation(weeks=2, routes=['SFOLAX'], depart_lengths=[[20,29]])
  #example.run()
  example.summarize()

