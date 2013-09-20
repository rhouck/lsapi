# levelskies objects
from functions import db as DB, weekday_pairs, mongo_connect, format_for_mongo_insert, format_from_binary
# general
import MySQLdb
import numpy
from itertools import cycle
import pylab as pl
import random
import pickle
import datetime
import pprint
import os
import time
import copy
from pprint import pprint
from scipy.stats import probplot
import pymongo

# pybrain dependencies
"""
from pybrain.datasets             import SupervisedDataSet, ClassificationDataSet
from pybrain.tools.shortcuts      import buildNetwork
from pybrain.supervised.trainers  import BackpropTrainer
from pybrain.structure            import FeedForwardNetwork, FullConnection, LinearLayer, SigmoidLayer
from pybrain.utilities            import percentError
from pybrain.structure.modules    import SoftmaxLayer
"""
# sklearn dependencies
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.svm import LinearSVC, SVC, SVR
from sklearn.decomposition import PCA, RandomizedPCA
#from sklearn.cluster import KMeans, MeanShift, DBSCAN
from sklearn import cross_validation
#from sklearn.manifold import Isomap
from sklearn.naive_bayes import GaussianNB
from sklearn import metrics
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, ExtraTreesRegressor, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.grid_search import GridSearchCV
from sklearn.feature_extraction import DictVectorizer
from sklearn.gaussian_process import GaussianProcess

def build_airfare_weekday_chart(example):
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday',]
    day_pairs = []
    for i in days:
      for j in days:
        day_pairs.append([i,j])

    levels = example.predict_on_fitted(day_pairs)[0]
    num_day_pairs = numpy.asarray([[days.index(i), days.index(j)] for i, j in day_pairs])
    num_day_pairs = numpy.vstack((num_day_pairs.T,levels.T)).T

    subplots = {}
    for i in num_day_pairs:
      if i[2] in subplots:
        subplots[i[2]].append([i[0],i[1]])
      else:
        subplots[i[2]] = []
        subplots[i[2]].append([i[0],i[1]])
    labels = subplots.keys()
    labels = ['xhigh','high', 'low','xlow',]
    fig, axes = pl.subplots()
    colors = cycle('rbgy')
    for c, l in zip(colors, labels):
      subplot = numpy.asarray(subplots[l])
      pl.scatter(subplot[:,0], subplot[:,1],c='%s' % (c), s=200, label='%s' % (l))
    pl.xticks([0,1,2,3,4,5,6], days)
    pl.yticks([0,1,2,3,4,5,6], days)
    pl.xlabel('Departing Week Day')
    pl.ylabel('Returning Week Day')
    pl.legend()
    pl.show()

class MachineLearn(object):

  def __init__(self, source=None, supervised_model=GaussianNB, dim_reduc_model=PCA, clust_model=None):

    if isinstance(source, DataSet):
      self.source = source.source
      self.data = source
    else:
      self.source = source


    self.supervised_model = supervised_model
    self.dim_reduc_model = dim_reduc_model
    self.clust_model = clust_model

    self.sup_models =  {'classifier':  {'general': (GaussianNB, DecisionTreeClassifier, LogisticRegression, LinearSVC, SVC,),
                                         'ensemble':(RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier,)},
                        'regressor':    {'general':(LinearRegression, DecisionTreeRegressor, SVR, Ridge, GaussianProcess),
                                        'ensemble': (RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor,)}
                        }
    self.unsup_models = {'dim_reduction': (None),
                         'clustering': (None)
                        }
    """
    Supervised-
    GaussianNB: classification - simple, fast, go-to method and great with high-dimensionality

    Dimensionality reduction-
    PCA: n_components - PCA seeks orthogonal linear combinations of the features which show the greatest variance, and as such, can help give you a good idea of the structure of the data set.
                        A weakness of PCA is that it produces a linear dimensionality reduction: this may miss some interesting relationships in the data.
    RandomizedPCA: n_components - Faster for large N.
    Isomap: n_neighbors, n_components -  A concatenation of Isometric Mapping which is a manifold learning method based on graph theory.

    Clusering-
    KMeans: The simplest, yet effective clustering algorithm. Needs to be provided with the number of clusters in advance, and assumes that the data is normalized as input (but use a PCA model as preprocessor).
    MeanShift: Can find better looking clusters than KMeans but is not scalable to high number of samples.
    DBSCAN: Can detect irregularly shaped clusters based on density, i.e. sparse regions in the input space are likely to become inter-cluster boundaries. Can also detect outliers (samples that are not part of a cluster).
    """

  def find_fit_params(self, sel_sup_model):
          depth = numpy.arange(1,21)
          alpha = [.01, .1, 1, 10]
          C = [0.01, 0.1, 0.5, 1.0, 1.5, 2.0,]

          fit_params = {'None': (1,)}
          try:
            test = sel_sup_model(max_depth = 1)
            fit_params = {'max_depth': depth}
          except:
            pass
          try:
            test = sel_sup_model(alpha = 1)
            fit_params = {'alpha': alpha}
          except:
            pass
          try:
            test = sel_sup_model(C = 1)
            fit_params ={'C': C}
          except:
            pass
          print fit_params
          return fit_params

  def build_sup_model(self, sel_sup_model, hyper, fit_param):

    model_type = (None, None)
    for key_1 in self.sup_models.iterkeys():
      for key_2, val_2 in self.sup_models[key_1].iteritems():
        if sel_sup_model in val_2:
          model_type = (key_1, key_2)
          break

    model = None
    inps = {}

    if hyper:
      inps = dict(hyper.items())

    if fit_param.keys()[0] is not 'None':
      inps = dict(inps.items() + fit_param.items())

    try:
      model = sel_sup_model(**inps)
    except:
      model = sel_sup_model()

    return model, model_type

  def compute_error(self, X, y, model, model_type):

      def compute_reg_error(X, y, model):
        y_pred = model.predict(X)
        return (numpy.sqrt(numpy.mean((y - y_pred) ** 2)), y_pred)
      def compute_class_error(X, y, model):
        y_pred = model.predict(X)
        return (1 - metrics.f1_score(y, y_pred), y_pred)

      if model_type[0] == 'classifier':
        err, y_pred = compute_class_error(X, y, model)
      else:
        err, y_pred = compute_reg_error(X, y, model)
      return (err, y_pred)

  def log_loss(self, act, pred):
    try:
      epsilon = 1e-15
      pred = pl.maximum(epsilon, pred)
      pred = pl.minimum(1-epsilon, pred)
      ll = sum(act*pl.log(pred) + pl.subtract(1,act)*pl.log(pl.subtract(1,pred)))
      ll = ll * -1.0/len(act)
      return ll
    except:
      return "Did not successfully run log-loss function"

  def split_train_test(self, test_size_split, test_data_end):
    """
    @params: test_size_split: float - sets the percentage of full dataset to be allocated to test sample
    @params: test_data_end: boolean or ('column_name', datetime.timedelta) -
                              "True" uses test_size_split to only pull from top of data set, rather than randomly select
                              tuple format pulls test set from top of data set, accorign to a date column and timedelta from first row in data set
    """
    if test_data_end:
      try:
        #set to ('column_name', datetime.timedelta):
        ind = None
        if test_data_end[0] in self.data.columns:
          test_date = self.data.X[0][self.data.columns.index(test_data_end[0])] - test_data_end[1]
        else:
          first_date = datetime.date(int(self.data.X[0][self.data.columns.index('%s_year' % (test_data_end[0]))]), int(self.data.X[0][self.data.columns.index('%s_month' % (test_data_end[0]))]), int(self.data.X[0][self.data.columns.index('%s_day' % (test_data_end[0]))]))
          test_date = first_date - test_data_end[1]

        # this finds index if first item exceeding time delta limit
        for index, i in enumerate(self.data.X):
          #print "index: %s, test: %s - actual: %s" % (index, test_date, datetime.date(int(i[self.data.columns.index('%s_year' % (test_data_end[0]))]), int(i[self.data.columns.index('%s_month' % (test_data_end[0]))]), int(i[self.data.columns.index('%s_day' % (test_data_end[0]))])))
          if test_date >= datetime.date(int(i[self.data.columns.index('%s_year' % (test_data_end[0]))]), int(i[self.data.columns.index('%s_month' % (test_data_end[0]))]), int(i[self.data.columns.index('%s_day' % (test_data_end[0]))])):
            ind = index
            break
        X_test = self.data.X[:ind-1]
        y_test = self.data.y[:ind-1]
        X_train = self.data.X[ind:]
        y_train = self.data.y[ind:]

      except:
        # set to True if you want to test on most recent data, rather than randomly selected data from the full data set
        test_count = int(len(self.data.y) * test_size_split)
        X_test = self.data.X[:test_count]
        y_test = self.data.y[:test_count]
        X_train = self.data.X[test_count+1:]
        y_train = self.data.y[test_count+1:]

    else:
      X_train, X_test, y_train, y_test = cross_validation.train_test_split(self.data.X, self.data.y, test_size=test_size_split, random_state=random.randrange(50))

    return (X_train, X_test, y_train, y_test)

  def quick_fit(self, hyper, test_size_split = 0.25, test_data_end=False):

    X_train, X_test, y_train, y_test = self.split_train_test(test_size_split, test_data_end)
    self.final_sup_model, self.sup_model_type = self.build_sup_model(self.supervised_model, hyper['static'], fit_param={'None': [1,]})
    self.final_sup_model = self.final_sup_model.fit(X_train, y_train)
    errors = self.compute_error(X_test, y_test, self.final_sup_model, self.sup_model_type)
    y_pred_best = errors[1]

    if self.sup_model_type[0] == 'classifier':
      self.sup_metrics = {'classsification_report': metrics.classification_report(y_test, y_pred_best), # F score and preciscion/recall
                          'confusion_matrix': metrics.confusion_matrix(y_test, y_pred_best),
                          'log-loss': self.log_loss(y_test, y_pred_best) }     # confusion matrix - which labels are being interchanged in the classifcation errors
    else:
      self.sup_metrics = {'explained_variance_score': metrics.explained_variance_score(y_test, y_pred_best),
                          'mean_sqrd_err_reg_loss': metrics.mean_squared_error(y_test, y_pred_best),
                          'r_sqrd_reg_score': metrics.r2_score(y_test, y_pred_best),}
      try:
        self.sup_metrics['mean_abs_err_reg_loss'] = metrics.mean_absolute_error(y_test, y_pred_best)
      except:
        pass

    # prediction interval for gradient boosting algorithm
    try:
      alpha = [0.05, 0.16, 0.5, 0.84, 0.95]
      self.pred_int_models = {}
      temp_hyper = hyper
      temp_hyper['static']['loss'] = 'quantile'
      for i in alpha:
        hyper['static']['alpha'] = i
        temp_model, temp_model_type = self.build_sup_model(self.supervised_model, temp_hyper['static'], fit_param={'None': [1,]})
        self.pred_int_models['%s' % (i)] = temp_model.fit(X_train, y_train)
    except:
      pass

  def run_supervised(self, test_size_split = 0.25, hyper = None, folds = 10, test_data_end=False):

      #try:

      X_train, X_test, y_train, y_test = self.split_train_test(test_size_split, test_data_end)

      if hyper:
        fit_params = hyper['iter'] if 'iter' in hyper else {'None': (1,)}
        static_hyper = hyper['static'] if 'static' in hyper else None
      else:
        fit_params = self.find_fit_params(self.supervised_model,)
        static_hyper = None


      # graph train and cross validation error over regularization or model complexity
      train_err = numpy.zeros(len(fit_params.values()[0]))
      crossval_err = numpy.zeros(len(fit_params.values()[0]))
      degree_best_ind = 0
      y_pred_best = None

      for ind, i in enumerate(fit_params.values()[0]):

        temp_model, model_type = self.build_sup_model(self.supervised_model, static_hyper, fit_param={fit_params.keys()[0]: i})
        self.sup_model_type = model_type
        if model_type[1] == "general":
          train_bank, cv_bank = [], []
          for f in range(folds):
            X_cv_train, X_cv_test, y_cv_train, y_cv_test = cross_validation.train_test_split(X_train, y_train, test_size=test_size_split, random_state=random.randrange(50))
            temp_model.fit(X_cv_train, y_cv_train)
            cv_bank.append(self.compute_error(X_cv_test, y_cv_test, temp_model, model_type)[0])
            train_bank.append(self.compute_error(X_cv_train, y_cv_train, temp_model, model_type)[0])

          crossval_err[ind] = sum(cv_bank)/len(cv_bank)
          train_err[ind] = sum(train_bank)/len(train_bank)
          temp_model.fit(X_train, y_train)

        else:
          # ensemble methods do not need to be explicitly looped through cross val process
          temp_model.fit(X_train, y_train)
          crossval_err[ind] = self.compute_error(X_test, y_test, temp_model, model_type)[0]
          train_err[ind] = self.compute_error(X_train, y_train, temp_model, model_type)[0]

        if crossval_err[ind] <= crossval_err[degree_best_ind]:
            degree_best_ind = ind
            degree_best = fit_params.values()[0][degree_best_ind]
            errors = self.compute_error(X_test, y_test, temp_model, model_type)
            y_pred_best = errors[1]

      chart_inputs = {}
      chart_inputs['hyperparam_iteration'] = {'cross_val': (fit_params.values()[0], crossval_err), 'train': (fit_params.values()[0], train_err)}
      chart_inputs['general'] = {'y_test': y_test, 'pred': y_pred_best, 'degree_best': degree_best}


      # learning curve plot
      max_size = X_train.shape[0] if model_type[1] == "general" else int(X_train.shape[0]*(1-test_size_split))
      sizes = numpy.linspace(10, X_train.shape[0], 50).astype(int)
      train_err = numpy.zeros(sizes.shape)
      crossval_err = numpy.zeros(sizes.shape)
      temp_model, model_type = self.build_sup_model(self.supervised_model, static_hyper, fit_param={fit_params.keys()[0]: degree_best})

      for i, size in enumerate(sizes):
          # Train on only the first `size` points
          try:
            if model_type[1] == "general":

              train_bank, cv_bank = [], []
              for f in range(folds):
                X_cv_train, X_cv_test, y_cv_train, y_cv_test = cross_validation.train_test_split(X_train, y_train, test_size=test_size_split, random_state=random.randrange(50))
                temp_model = temp_model.fit(X_cv_train[:size], y_cv_train[:size])
                cv_bank.append(self.compute_error(X_cv_test, y_cv_test, temp_model, model_type)[0])
                train_bank.append(self.compute_error(X_cv_train[:size], y_cv_train[:size], temp_model, model_type)[0])

              crossval_err[i] = sum(cv_bank)/len(cv_bank)
              train_err[i] = sum(train_bank)/len(train_bank)
            else:

              # ensemble methods do not need to be explicityly looped to cross validate
              temp_model = temp_model.fit(X_train[:size], y_train[:size])
              crossval_err[i] = self.compute_error(X_test, y_test, temp_model, model_type)[0]
              train_err[i] = self.compute_error(X_train[:size], y_train[:size], temp_model, model_type)[0]

          except:
            pass

      chart_inputs['learning_curve'] = {'sizes': sizes, 'crossval_err': crossval_err, 'train_err': train_err, 'X_train_shape': X_train.shape}



      """
      try:
        # grid search
        temp_model = self.build_sup_model(sel_sup_model, static_hyper, fit_param=len(fit_params.values()[0]))
        grid = GridSearchCV(temp_model, param_grid=dict(max_depth=fit_params.values()[0]))
        grid.fit(X_train, y_train)
        temp_model = self.build_sup_model(sel_sup_model, static_hyper, max_depth=grid.best_params_['max_depth'])
        temp_model.fit(X_train, y_train)
        grid_y_pred = self.compute_error(X_test, y_test, temp_model, X_test.shape[0], classification)[2]


        sub_pred = pl.subplot2grid((2,2), (1,1), colspan=1)
        sub_pred.scatter(y_test, grid_y_pred)
        sub_pred.plot([0, max(y_test)], [0, max(y_test)], '--k')
        sub_pred.axis('tight')
        sub_pred.grid(True)
        sub_pred.set_xlabel('Target')
        sub_pred.set_ylabel('Predicted')
        sub_pred.set_title("Degree %s - Grid Search - Accuracy" % (grid.best_params_['max_depth']))
      except:
        pass
      """




      self.final_sup_model, final_sup_model_type = self.build_sup_model(self.supervised_model, static_hyper, fit_param={fit_params.keys()[0]: degree_best})
      self.final_sup_model = self.final_sup_model.fit(X_train, y_train)

      # compute test set deviance for gradient boosting
      try:
        test_score = numpy.zeros(self.final_sup_model.n_estimators, dtype=numpy.float64)
        for i, y_pred in enumerate(self.final_sup_model.staged_decision_function(X_test)):
            test_score[i] = self.final_sup_model.loss_(y_test, y_pred)
        chart_inputs['deviance'] = {'n_estimators': self.final_sup_model.n_estimators, 'train_score': self.final_sup_model.train_score_, 'test_score': test_score, 'feature_importance': self.final_sup_model.feature_importances_}
      except:
        pass

      self.sup_graph = chart_inputs

      if self.sup_model_type[0] == 'classifier':
        self.sup_metrics = {'classsification_report': metrics.classification_report(y_test, y_pred_best), # F score and preciscion/recall
                            'confusion_matrix': metrics.confusion_matrix(y_test, y_pred_best),
                            'log-loss': self.log_loss(y_test, y_pred_best) }     # confusion matrix - which labels are being interchanged in the classifcation errors
      else:
        self.sup_metrics = {'explained_variance_score': metrics.explained_variance_score(y_test, y_pred_best),
                            'mean_sqrd_err_reg_loss': metrics.mean_squared_error(y_test, y_pred_best),
                            'r_sqrd_reg_score': metrics.r2_score(y_test, y_pred_best),}
        try:
          self.sup_metrics['mean_abs_err_reg_loss'] = metrics.mean_absolute_error(y_test, y_pred_best)
        except:
          pass



      #except Exception as err:
      #  print "Could not run supervised model: %s" % err

  def run_unsupervised(self, num_clusters=2, cluster_on_dim_reduc=False):

    try:
      # dimensionality reduction
      dim_model = self.dim_reduc_model(n_components=2, whiten=True)
      dim_model.fit(self.data.X)
      projected = dim_model.transform(self.data.X)

      self.unsup_dim_reduc_metrics = {'components': dim_model.components_,
                                      'exp_var_ratio': dim_model.explained_variance_ratio_,
                                      'exp_var_ratio_sum': dim_model.explained_variance_ratio_.sum(),
                                      'projected_mean': numpy.round(projected.mean(axis=0), decimals=5),
                                      'projected_std': numpy.round(projected.std(axis=0), decimals=5),
                                      'correl_coef': numpy.corrcoef(projected.T),}

      self.final_dim_model = dim_model

      # clustering algorithm
      try:
        rng = numpy.random.RandomState(random.randrange(50))
        model = self.clust_model(n_clusters=num_clusters, random_state=rng)
      except:
        model = self.clust_model()

      model.fit(projected if cluster_on_dim_reduc else self.data.X)



      self.unsup_cluster_metrics = {'centers': numpy.round(model.cluster_centers_, decimals=2),
                                    'labels': model.labels_}
      self.final_clust_model = model

      fig, axes = pl.subplots()
      fig.suptitle("'%s' data source" % (self.source))
      #fig.tight_layout()
      fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3)

      def plot_PCA_2D(data, target, target_names, chart_num, title):
        colors = cycle('rgbcmykw')
        target_ids = range(len(target_names))
        for i, c, label in zip(target_ids, colors, target_names):
            pl.scatter(data[target == i, 0], data[target == i, 1],
                      c=c, label=label)
        pl.legend()
        pl.title('%s' % (title))


      # display dimensionality reduction
      pl.subplot2grid((2,1), (0,0), colspan=1)
      plot_PCA_2D(projected, self.data.y, self.data.y_names, 1, 'True labels')
      # display clustering
      cluster_labels = []
      for i in range(len(numpy.unique(model.labels_))):
        cluster_labels.append("clust_%s" % (i))
      pl.subplot2grid((2,1), (1,0), colspan=1)
      plot_PCA_2D(projected if cluster_on_dim_reduc else self.data.X, model.labels_, cluster_labels, 2, 'Clustering algorithm labels')

      self.unsup_graph = pl

    except:
      print "Could not run unsupervised model"

  def show_graph(self,):
    try:
      fig, axes = pl.subplots()
      fig.suptitle("'%s' data source" % (self.source))
      #fig.tight_layout()
      fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3)
      columns = 3 if 'deviance' in self.sup_graph else 2

      sub_deg = pl.subplot2grid((2,columns), (0,0), colspan=1)
      sub_deg.plot(self.sup_graph['hyperparam_iteration']['cross_val'][0], self.sup_graph['hyperparam_iteration']['cross_val'][1], lw=2, label = 'validation set')
      sub_deg.plot(self.sup_graph['hyperparam_iteration']['train'][0], self.sup_graph['hyperparam_iteration']['train'][1], lw=2, label = 'training set')
      sub_deg.legend(loc=0)
      sub_deg.set_xlabel('degree of fit')
      sub_deg.set_ylabel('1 - f1 score') if self.sup_model_type[0] == 'classifier' else sub_deg.set_ylabel('rms error')
      sub_deg.set_title('Model fit by degree')


      # best prediction on actual
      sub_pred = pl.subplot2grid((2,columns), (1,0), colspan=1)
      sub_pred.scatter(self.sup_graph['general']['y_test'], self.sup_graph['general']['pred'])
      sub_pred.plot([min(self.sup_graph['general']['y_test']), max(self.sup_graph['general']['y_test'])], [min(self.sup_graph['general']['y_test']), max(self.sup_graph['general']['y_test'])], '--k')
      sub_pred.axis('tight')
      sub_pred.grid(True)
      sub_pred.set_xlabel('Target')
      sub_pred.set_ylabel('Predicted')
      sub_pred.set_title("Degree %s - Prediction Accuracy" % (self.sup_graph['general']['degree_best']))


    except Exception as err:
      print "Could not produce graphs: %s" % (err)


    # q-q plot for best prediction/actual
    if self.sup_model_type[0] == 'regressor':
      sub_qq = pl.subplot2grid((2,columns), (1,1), colspan=1)
      try:
        pred_over_act = self.sup_graph['general']['pred']/self.sup_graph['general']['y_test']
      except:
        # models loaded from DB need to be converted to numpy arrays
        pred_over_act = numpy.asarray(self.sup_graph['general']['pred']) / numpy.asarray(self.sup_graph['general']['y_test'])
      qq_plot_data = probplot(pred_over_act)
      sub_qq.scatter(qq_plot_data[0][0], qq_plot_data[0][1])
      fit = pl.polyfit(qq_plot_data[0][0],qq_plot_data[0][1],1)
      fit_fn = pl.poly1d(fit)
      sub_qq.plot(qq_plot_data[0][0], fit_fn(qq_plot_data[0][0]), '--k')
      sub_qq.axis('tight')
      sub_qq.grid(True)
      sub_qq.set_xlabel('Theoretical Quantile')
      sub_qq.set_ylabel('Predicted / Actual')
      sub_qq.set_title("Q-Q Plot on best fit")

    sub_learn = pl.subplot2grid((2,columns), (0,1), colspan=1)
    sub_learn.set_ylabel('1 - f1 score') if self.sup_model_type[0] == 'classifier' else sub_learn.set_ylabel('rms error')
    sub_learn.set_xlabel('traning set size')
    sub_learn.plot(self.sup_graph['learning_curve']['sizes'], self.sup_graph['learning_curve']['crossval_err'], lw=2, label='validation set')
    sub_learn.plot(self.sup_graph['learning_curve']['sizes'], self.sup_graph['learning_curve']['train_err'], lw=2, label='training set')
    sub_learn.legend(loc=0)
    sub_learn.set_xlim(2, self.sup_graph['learning_curve']['X_train_shape'][0])
    #sub_learn.set_ylim(0, 0.5)
    sub_learn.set_title('Learning Curve')

    if 'deviance' in self.sup_graph:
      sub_dev = pl.subplot2grid((2,columns), (0,2), colspan=1)
      sub_dev.set_title('Deviance')
      sub_dev.plot(numpy.arange(self.sup_graph['deviance']['n_estimators']) + 1, self.sup_graph['deviance']['train_score'], 'b-',
              label='Training Set Deviance')
      sub_dev.plot(numpy.arange(self.sup_graph['deviance']['n_estimators']) + 1, self.sup_graph['deviance']['test_score'], 'r-',
              label='Test Set Deviance')
      sub_dev.legend(loc='upper right')
      sub_dev.set_xlabel('Boosting Iterations')
      sub_dev.set_ylabel('Deviance')


      # Plot feature importance
      feature_importance = self.sup_graph['deviance']['feature_importance']
      # make importances relative to max importance
      feature_importance = 100.0 * (feature_importance / feature_importance.max())
      sorted_idx = numpy.argsort(feature_importance)


      feature_limit = 15
      short_sorted_idx = sorted_idx[-feature_limit:]
      sorted_idx = copy.deepcopy(short_sorted_idx)

      pos = numpy.arange(sorted_idx.shape[0]) + 0.5

      sub_feat = pl.subplot2grid((2,columns), (1,2), colspan=1)
      sub_feat.barh(pos, feature_importance[sorted_idx], align='center')
      cats = numpy.asarray([x.upper() for x in self.data.columns[:-1]])[sorted_idx]
      sub_feat.set_yticks(pos)
      sub_feat.set_yticklabels(cats, size='xx-small')
      sub_feat.set_xlabel('Relative Importance')
      sub_feat.set_title('Variable Importance')


    pl.show()

  def predict_on_fitted(self, X,):

    inp_data = DataSet(X, csv=True, expand_dates=self.data.expand_dates, normalize=self.data.normalize, category=self.data.category)
    X = inp_data.X
    y_pred = numpy.asarray(self.final_sup_model.predict(X))

    if inp_data.target_classes:
      labeled_ys= []
      for i in y_pred:
        labeled_ys.append(inp_data.target_classes[int(i)])
      y_pred = numpy.asarray(labeled_ys)
    results = {'standard': y_pred}


    try:
      intervals = self.pred_int_models.keys()
      intervals.sort()
      for index, i in enumerate(intervals):
        y_pred = numpy.asarray(self.pred_int_models[i].predict(X))
        if index == 0:
          pred_int_res = numpy.asarray(y_pred)
        else:
          pred_int_res = numpy.vstack([pred_int_res, y_pred])
      results['prediction_probability_intervals'] = (intervals, pred_int_res.T)
    except:
      pass


    try:
      y_pred_prob = self.final_sup_model.predict_proba(X)
      results['prediction_probabilities'] = y_pred_prob
    except:
      pass

    return results

  def neural_net(self, data_source):

    data = data_source
    split = 0.25
    iters = 10
    epochs = 1
    h_layers = 1
    h_nodes = None
    graph = True

    momentum=0.01
    weightdecay=0.01

    ds = ClassificationDataSet(numpy.shape(data['rows'])[1] - 1, 1, nb_classes=len(data['classes']), class_labels=data['classes'])
    ds.setField('input', data['rows'][:,:-1])
    ds.setField('target', data['rows'][:,-1:])
    tstdata, trndata = ds.splitWithProportion( split )
    ds = {"train": trndata, "test": tstdata}
    ds['train']._convertToOneOfMany(bounds=[0, 1])
    ds['test']._convertToOneOfMany(bounds=[0, 1])


    print "Number of training patterns: ", len(ds['train'])
    print "Input and output dimensions: ", ds['train'].indim, ds['train'].outdim
    print "First sample (input, target, class):"
    print ds['train']['input'][1], ds['train']['target'][1], ds['train']['class'][1]


    if not h_nodes:
      h_nodes = ds['train'].indim

    if h_layers == 1:
      n = buildNetwork( ds['train'].indim, h_nodes, ds['train'].outdim, outclass=SoftmaxLayer )
    if h_layers == 2:
      n = buildNetwork( ds['train'].indim, h_nodes, h_nodes, ds['train'].outdim, outclass=SoftmaxLayer )
    if h_layers >= 3:
      n = buildNetwork( ds['train'].indim, h_nodes, h_nodes, h_nodes, ds['train'].outdim, outclass=SoftmaxLayer )

    trainer = BackpropTrainer( n, dataset=ds['train'], momentum=momentum, verbose=False, weightdecay=weightdecay)

    if graph:
      train_error_bank = []
      test_error_bank = []
      iters_bank = []

    for i in range(iters):
      trainer.trainEpochs( epochs ) # what are epochs?
      trnresult = percentError( trainer.testOnClassData(), ds['train']['class'] )
      tstresult = percentError(trainer.testOnClassData(dataset=ds['test'] ), ds['test']['class'] )

      print "epoch: %4d" % trainer.totalepochs, \
            "  train error: %5.2f%%" % trnresult, \
            "  test error: %5.2f%%" % tstresult
      if graph:
        iters_bank.append(i)
        train_error_bank.append(trnresult)
        test_error_bank.append(tstresult)

    if graph:
      pl.figure(1)
      #pl.subplot(211)
      pl.plot(iters_bank, train_error_bank, iters_bank, test_error_bank, linewidth=2.0)
      pl.grid(True)
      pl.legend(('Train', 'Test'),'upper right')
      pl.xlabel('Number of Iterations')
      pl.ylabel('Error')
      pl.title('Change in Error Across Iterations')
      pl.show()

    """
    n = FeedForwardNetwork()
    # layers or alphas         where do you build in a bias?
    inLayer = LinearLayer(4)
    hiddenLayer = SigmoidLayer(5)
    outLayer = SoftmaxLayer(1) #SigmoidLayer(2)
    n.addInputModule(inLayer)
    n.addModule(hiddenLayer)
    n.addOutputModule(outLayer)
    # conecctions or thetas
    in_to_hidden = FullConnection(inLayer, hiddenLayer)
    hidden_to_out = FullConnection(hiddenLayer, outLayer)
    n.addConnection(in_to_hidden)
    n.addConnection(hidden_to_out)
    n.sortModules()
    """

  def save_model(self, note=None, collection='practice', save_training_data=False):

    data = {}
    try:
      data['supervised_model'] = {'model': self.final_sup_model, 'model_name': self.supervised_model().__class__.__name__, 'metrics': self.sup_metrics, 'model_type': self.sup_model_type}
    except:
      pass
    try:
      data['supervised_model']['graph'] = self.sup_graph
    except:
      pass
    try:
      data['supervised_model']['prediction_interval_models'] = self.pred_int_models
    except:
      pass
    try:
      data['unsupervised_model'] = {'dimension_model': self.final_dim_model, 'dimension_model_name': self.dim_reduc_model().__class__.__name__, 'dimension_model_metrics': self.unsup_dim_reduc_metrics,
                                    'cluster_model': self.final_clust_model, 'cluster_model_name': self.clust_model().__class__.__name__, 'cluster_model_metrics': self.unsup_cluster_metrics,
                                    } # 'graph': self.unsup_graph
    except:
      pass

    if data:
      if not save_training_data:
        X_hold = copy.deepcopy(self.data.X)
        y_hold = copy.deepcopy(self.data.y)
        rows_hold = copy.deepcopy(self.data.rows)
        self.data.X = None
        self.data.y = None
        self.data.rows = None
      data['data'] = self.data


    if self.data.source and data:
      model_methods = []
      if 'supervised_model' in data:
        model_methods.append(self.supervised_model().__class__.__name__)
      if 'unsupervised_model' in data:
        model_methods.append(self.clust_model().__class__.__name__)
        model_methods.append(self.dim_reduc_model().__class__.__name__)
      model_methods = '_'.join(model_methods)

      """
      file_name = "%s_%s_%s_%s" % (self.data.source, model_methods, datetime.datetime.now().date(), note)
      file_object = open("%s\model_sessions\%s" % (os.getcwd(),file_name),'w')
      pickle.dump(data, file_object)
      file_object.close()
      """

      data['source'] = self.data.source
      data['model_methods'] = model_methods
      data['note'] = note
      data['date'] = datetime.datetime.now()
      data = format_for_mongo_insert(data)
      mongo = mongo_connect()
      mongo.models['%s' % (collection)].insert(data)
      mongo.disconnect()

      print "Saved model"

    else:
      print "No training data loaded or model created. Nothing to save."

    if data:
      if not save_training_data:
        self.data.X = copy.deepcopy(X_hold)
        self.data.y = copy.deepcopy(y_hold)
        self.data.rows = copy.deepcopy(rows_hold)
        X_hold = None
        y_hold = None
        rows_hold = None


  def load_saved_model(self, source, model_methods, collection='practice', latest=True):

    try:
      """
      file_object = open("%s\model_sessions\%s" % (os.getcwd(),file_name),'r')
      loaded_data = pickle.load(file_object)
      """

      mongo = mongo_connect()
      if latest:
        res = mongo.models['%s' % (collection)].find({'source': source, 'model_methods': model_methods}).sort('date',-1).limit(1)
      else:
        pass
      mongo.disconnect()

      for i in res:
        loaded_data = i

      loaded_data = format_from_binary(loaded_data)

      self.data = loaded_data['data']

      if 'supervised_model' in loaded_data:
        self.supervised_model = loaded_data['supervised_model']['model_name']
        self.final_sup_model =  loaded_data['supervised_model']['model']
        self.sup_metrics = loaded_data['supervised_model']['metrics']
        self.sup_model_type = loaded_data['supervised_model']['model_type']
        try:
          self.sup_graph = loaded_data['supervised_model']['graph']
        except:
          pass
        try:
          self.pred_int_models = loaded_data['supervised_model']['prediction_interval_models']
        except:
          pass
      else:
        self.supervised_model = None

      if 'unsupervised_model' in loaded_data:
        self.clust_model = loaded_data['unsupervised_model']['cluster_model_name']
        self.dim_reduc_model = loaded_data['unsupervised_model']['dimension_model_name']
        self.final_dim_model = loaded_data['unsupervised_model']['dimension_model']
        self.final_clust_model = loaded_data['unsupervised_model']['cluster_model']
        self.unsup_dim_reduc_metrics = loaded_data['unsupervised_model']['dimension_model_metrics']
        self.unsup_cluster_metrics = loaded_data['unsupervised_model']['cluster_model_metrics']
        #self.unsup_graph = loaded_data['unsupervised_model']['graph']
      else:
        self.clust_model = None
        self.dim_reduc_model = None

    except Exception as err:
      print "Error loading saved model: %s" % (err)


class DataSet(object):

  def __init__(self, source, db_name='machine', ignore=None, target_index=None, thin_data=False, expand_dates=True, normalize=False, category=None, remove_nans=True):

    if db_name:
      db = DB(db=db_name)
      table = db.import_table("%s" % (source))
      columns = numpy.asarray(db.get_cols(source))
      table = numpy.asarray(table)
      db.db_disconnect()
    else:
      if isinstance(source[1], numpy.ndarray):
        raw_data = source[1]
      else:
        raw_data = numpy.genfromtxt(open('data/%s.csv' % (source[1]),'r'), delimiter=',', dtype="|S3") # , dtype='f8'
      source = source[0]
      columns = raw_data[0,:]
      table = raw_data[1:,:]


    if isinstance(target_index, (int,str)):
      try:
        raw_data
      except:
        raw_data = numpy.vstack((columns,table))

      try:
        tar = raw_data[:,target_index]
      except:

        target_index = numpy.where(raw_data[0,:]==target_index)[0][0]
        tar = raw_data[:,target_index]

      raw_data_less_tar = numpy.delete(raw_data,target_index,1)
      sorted_raw_data = numpy.vstack((raw_data_less_tar.T,tar.T)).T
      columns = sorted_raw_data[0].tolist()
      table = sorted_raw_data[1:]
    else:
      columns = columns.tolist()


    if thin_data:
      short_index = int(table.shape[0]*thin_data)
      choice = random.sample(range(table.shape[0]), short_index)
      choice.sort()
      table = table[choice]


    if ignore:
      ignore_ind_bank = []
      for ind, i in enumerate(ignore):
        ignore_ind_bank.append(columns.index(i))

      ignore_ind_bank.sort()
      for ind, i in enumerate(ignore_ind_bank):
        table = numpy.delete(table, i-ind, 1)
        del columns[i-ind]

    self.source = source
    self.unexpanded_columns = copy.deepcopy(columns)
    self.category = category
    self.normalize = normalize
    self.ignore = ignore
    self.expand_dates = copy.deepcopy(expand_dates)
    self.expand_dates_cats(table, columns, expand_dates=expand_dates, normalize=normalize, category=category, remove_nans=remove_nans)


  def expand_dates_cats(self, table, columns, expand_dates=True, normalize=False, category=None, remove_nans=True):

    if expand_dates:
      column_bank = []
      date_collections = numpy.asarray([])
      for index, i in enumerate(table[0][:]):

        if isinstance(i, datetime.date):

          expanded = [[x.year, x.month, x.day] for x in table[:,index-len(column_bank)]]
          expanded = numpy.asarray(expanded)
          if date_collections.size == 0:
            date_collections = expanded
          else:
            date_collections = numpy.hstack([date_collections,expanded])
          table = numpy.delete(table, index-len(column_bank), 1)
          column_bank.append(columns[index-len(column_bank)])
          del columns[index-len(column_bank)+1]

      date_exp_labels = ['year', 'month', 'day']
      tar_name = columns.pop(-1)
      for i in column_bank:
        for j in date_exp_labels:
          columns.append('%s_%s' % (i,j))
      columns.append(tar_name)

      if date_collections.size > 0:
        table = numpy.vstack([table[:,:-1].T, date_collections.T, table[:,-1].T]).T


    # expands categorical data into a series of binary columns
    if category:
      cat_bank = []
      cat_ind_bank = []
      temp_array = numpy.asarray([])
      for ind, i in enumerate(category):
        cat_ind = columns.index(i)
        cat_bank.append(i)
        cat_ind_bank.append(cat_ind)
        if ind > 0:
          temp_array = numpy.vstack([temp_array,table[:,cat_ind]])
        else:
          temp_array = table[:,cat_ind]
      temp_array = temp_array.T
      if len(temp_array.shape) == 1:
        temp_array = numpy.reshape(temp_array,(temp_array.shape[0],1))

      temp_array_str = numpy.asarray(temp_array, dtype="|S3")
      temp_dicts = [dict(zip(cat_bank, x)) for x in temp_array_str]

      vec = DictVectorizer()
      temp_exp_array = vec.fit_transform(temp_dicts).toarray()

      cat_ind_bank.sort()
      self.category_input_indexes = cat_ind_bank

      for ind, i in enumerate(cat_ind_bank):
        table = numpy.delete(table, i-ind, 1)
        del columns[i-ind]

      table = numpy.vstack([table[:,:-1].T, temp_exp_array.T, table[:,-1].T]).T
      final_columns = columns[:-1] + vec.get_feature_names() + [columns[-1]]

    else:
      self.category_input_indexes = None
      final_columns = columns


    # converts text and date-based predictors to integers
    classes_set = dict()
    for index in range(table.shape[1]):
      row = 0
      marker = None
      while marker is None:
        #print final_columns[index]
        #print "%s : %s : %s" % (index, row, marker)
        marker = table[row][index]
        row += 1
      #print "%s - %s" % (index, marker)
      try:
        float(marker)
      except:
        classes = numpy.unique(table[:,index])
        for j in classes:
          numpy.putmask(table[:,index], table[:,index]==j, numpy.where(classes==j))
        classes_set[index] = classes.tolist()

    # would you ever want to convert number-based targets to class form?
    #if (table.shape[1] - 1) not in classes_set:
    #  classes_set[(table.shape[1] - 1)] = numpy.unique(table[:,-1]).tolist()

    table = numpy.asarray(table, dtype='float')


    # normalizes data by converting to z-scores
    if normalize:
      # converts values to z-scores
      if category:
        last_ind = len(columns) - 1 - len(category)
      else:
        last_ind = -1
      preds_table = table[:,:last_ind]
      preds_mean = preds_table.mean(axis=0)
      preds_std = preds_table.std(axis=0)
      norm_preds = (preds_table - preds_mean) / preds_std
      table[:,:last_ind] = norm_preds
    else:
      preds_mean, preds_std = None, None

    if remove_nans:
      table = table[~numpy.isnan(table).any(axis=1)]

    self.rows = table
    self.columns = final_columns
    self.predictor_stats = (preds_mean, preds_std)
    self.X = self.rows[:,:-1]
    y_arrays = numpy.asarray(self.rows[:,-1:])
    self.y = numpy.dstack(y_arrays)[0][0]
    if (table.shape[1] - 1) in classes_set:
      self.target_classes = classes_set[table.shape[1] - 1]
      del classes_set[table.shape[1] - 1]
    else:
      self.target_classes = None
    self.predictor_classes = classes_set


if __name__ == "__main__":

  start = time.time()

  #data = DataSet('cement', db_name='machine')
  data = DataSet('sfojfk_price_change_source', db_name='steadyfa_temp_tables', ignore=['end_price','date_collected','depart_date','return_date','rel_inc','date_completed'], target_index='abs_inc', thin_data=0.025,)
  print data.X

  example = MachineLearn(data, supervised_model=GradientBoostingRegressor)
  hyper = {'iter': {'alpha': [0.01, 0.1, 0.5, 0.9] } }
  example.run_supervised(hyper=hyper)
  pprint(example.sup_metrics)
  example.show_graph()


  print "end of script in %s seconds" % (time.time()-start)
