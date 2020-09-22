# Copyright 2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hyperopt
import lale.docstrings
import lale.helpers
import lale.operators
import pandas as pd
import sklearn.metrics
import sklearn.model_selection
import time
import warnings

try:
    import xgboost
    xgboost_installed=True
except ImportError:
    xgboost_installed=False
try:
    import lightgbm.sklearn
    lightgbm_installed=True
except ImportError:
    lightgbm_installed=False

def auto_prep(X):
    from lale.lib.lale import ConcatFeatures
    from lale.lib.lale import Project
    from lale.lib.lale import categorical
    from lale.lib.sklearn import OneHotEncoder
    from lale.lib.sklearn import SimpleImputer
    n_cols = X.shape[1]
    n_cats = len(categorical()(X))
    prep_num = SimpleImputer(strategy='mean')
    prep_cat = (SimpleImputer(strategy='most_frequent')
                >> OneHotEncoder(handle_unknown='ignore'))
    if n_cats == 0:
        result = prep_num
    elif n_cats == n_cols:
        result = prep_cat
    else:
        result = (
            (Project(columns={'type': 'number'}, drop_columns=categorical())
             >> prep_num)
            & (Project(columns=categorical()) >> prep_cat)
        ) >> ConcatFeatures
    return result

def auto_forest(prediction_type):
    if prediction_type == 'regression':
        if xgboost_installed:
            from lale.lib.xgboost import XGBRegressor
            return XGBRegressor
        elif lightgbm_installed:
            from lale.lib.lightgbm import LGBMRegressor
            return LGBMRegressor
        else:
            from lale.lib.sklearn import RandomForestRegressor
            return RandomForestRegressor
    else:
        assert prediction_type == 'classification'
        if xgboost_installed:
            from lale.lib.xgboost import XGBClassifier
            return XGBClassifier
        elif lightgbm_installed:
            from lale.lib.lightgbm import LGBMClassifier
            return LGBMClassifier
        else:
            from lale.lib.sklearn import RandomForestClassifier
            return RandomForestClassifier

class AutoPipelineImpl:
    def __init__(self, prediction_type='classification',
                 max_opt_time=600.0, max_eval_time=120.0, max_evals=100,
                 verbose=False, scoring=None, best_score=0.0):
        self.prediction_type = prediction_type
        self.max_opt_time = max_opt_time
        self.max_eval_time = max_eval_time
        self.max_evals = max_evals
        self.verbose = verbose
        if scoring is None:
            scoring = 'r2' if prediction_type=='regression' else 'accuracy'
        self.scoring = scoring
        self._scorer = sklearn.metrics.get_scorer(scoring)
        self.best_score = best_score

    def _try_and_add(self, name, trainable, X, y):
        assert name not in self._pipelines
        if self._name_of_best is not None:
            if time.time() > self._start_fit + self.max_opt_time:
                return
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cv = sklearn.model_selection.check_cv(
                cv=5, classifier=(self.prediction_type!='regression'))
            cv_score, logloss, execution_time = lale.helpers.cross_val_score_track_trials(trainable, X, y, self.scoring, cv)
        loss = self.best_score - cv_score
        if (self._name_of_best is None or
            loss < self._summary.at[self._name_of_best, 'loss']):
            self._name_of_best = name
        record = {'name': name, 'loss': loss, 'time': execution_time,
                  'log_loss': logloss, 'status': hyperopt.STATUS_OK}
        singleton_summary = pd.DataFrame.from_records([record], index='name')
        if self._summary is None:
            self._summary = singleton_summary
        else:
            self._summary = pd.concat([self._summary, singleton_summary])
        if name == self._name_of_best:
            self._pipelines[name] = trainable.fit(X, y)
        else:
            self._pipelines[name] = trainable

    def _fit_baseline(self, X, y):
        from lale.lib.lale import BaselineRegressor
        from lale.lib.lale import BaselineClassifier
        if self.prediction_type == 'regression':
            trainable = BaselineRegressor()
        else:
            trainable = BaselineClassifier()
        self._try_and_add('baseline', trainable, X, y)

    def _fit_forest_num(self, X, y):
        from lale.lib.lale import Project
        from lale.lib.sklearn import SimpleImputer
        forest = auto_forest(self.prediction_type)
        trainable = (Project(columns={'type': 'number'})
                     >> SimpleImputer(strategy='mean')
                     >> forest())
        self._try_and_add('forest_num', trainable, X, y)

    def _fit_forest_all(self, X, y):
        prep = auto_prep(X)
        forest = auto_forest(self.prediction_type)
        trainable = prep >> forest()
        self._try_and_add('forest_all', trainable, X, y)

    def _fit_hyperopt(self, X, y):
        from lale.lib.lale import Hyperopt
        from lale.lib.lale import NoOp
        from lale.lib.sklearn import DecisionTreeClassifier
        from lale.lib.sklearn import DecisionTreeRegressor
        from lale.lib.sklearn import KNeighborsClassifier
        from lale.lib.sklearn import KNeighborsRegressor
        from lale.lib.sklearn import LinearRegression
        from lale.lib.sklearn import LogisticRegression
        from lale.lib.sklearn import MinMaxScaler
        from lale.lib.sklearn import PCA
        from lale.lib.sklearn import RobustScaler
        from lale.lib.sklearn import SelectKBest
        prep = auto_prep(X)
        scale = MinMaxScaler | RobustScaler | NoOp
        fsel = PCA | SelectKBest | NoOp
        forest = auto_forest(self.prediction_type)
        if self.prediction_type == 'regression':
            estimator = (forest | LinearRegression | KNeighborsRegressor
                         | DecisionTreeRegressor)
        else:
            estimator = (forest | LogisticRegression | KNeighborsClassifier
                         | DecisionTreeClassifier)
        planned = prep >> scale >> fsel >> estimator
        trainable = Hyperopt(
            estimator=planned,
            max_evals=self.max_evals - self._summary.shape[0],
            scoring=self.scoring,
            best_score=self.best_score,
            max_opt_time=self.max_opt_time - (time.time() - self._start_fit),
            max_eval_time=self.max_eval_time,
            verbose=self.verbose,
            show_progressbar=False)
        trained = trainable.fit(X, y)
        best_trial = trained._impl._trials.best_trial
        if 'loss' in best_trial['result']:
            if (best_trial['result']['loss']
                < self._summary.at[self._name_of_best, 'loss']):
                self._name_of_best = f'p{best_trial["tid"]}'
        summary = trained.summary()
        self._summary = pd.concat([self._summary, summary])
        for name in summary.index:
            assert name not in self._pipelines
            if summary.at[name, 'status'] == hyperopt.STATUS_OK:
                self._pipelines[name] = trained.get_pipeline(name)

    def fit(self, X, y):
        self._start_fit = time.time()
        self._name_of_best = None
        self._summary = None
        self._pipelines = {}
        self._fit_baseline(X, y)
        self._fit_forest_num(X, y)
        self._fit_forest_all(X, y)
        self._fit_hyperopt(X, y)
        return self

    def predict(self, X):
        best_pipeline = self._pipelines[self._name_of_best]
        result = best_pipeline.predict(X)
        return result

    def summary(self):
        """Table summarizing the trial results (name, tid, loss, time, log_loss, status).
Returns
-------
result : DataFrame"""
        self._summary.sort_values(by='loss', inplace=True)
        return self._summary

    def get_pipeline(self, pipeline_name=None, astype='lale'):
        """Retrieve one of the trials.
Parameters
----------
pipeline_name : union type, default None
    - string
        Key for table returned by summary(), return a trainable pipeline.
    - None
        When not specified, return the best trained pipeline found.
astype : 'lale' or 'sklearn', default 'lale'
    Type of resulting pipeline.
Returns
-------
result : Trained operator if best, trainable operator otherwise.
"""
        if pipeline_name is None:
            pipeline_name = self._name_of_best
        result = self._pipelines[pipeline_name]
        if result is None or astype == 'lale':
            return result
        assert astype == 'sklearn', astype
        return result.export_to_sklearn_pipeline()

_hyperparams_schema = {
    'allOf': [
    {   'type': 'object',
        'required': [
            'prediction_type', 'scoring',
            'max_evals', 'max_opt_time', 'max_eval_time'],
        'relevantToOptimizer': [],
        'additionalProperties': False,
        'properties': {
            'prediction_type': {
                'description': 'The kind of learning problem.',
                'enum': [
                    'binary', 'multiclass', 'classification', 'regression'],
                'default': 'classification'},
            'max_opt_time': {
                'description': 'Maximum time in seconds for the optimization.',
                'anyOf': [
                {   'type': 'number',
                    'minimum': 0.0, 'exclusiveMinimum': True},
                {   'description': 'No runtime bound.',
                    'enum': [None]}],
                'default': 600.0},
            'max_eval_time': {
                'description': 'Maximum time in seconds for each evaluation.',
                'anyOf': [
                {   'type': 'number',
                    'minimum': 0.0, 'exclusiveMinimum': True},
                {   'description': 'No runtime bound.',
                    'enum': [None]}],
                'default': 120.0},
            'max_evals': {
                'description': 'Number of trials of Hyperopt search.',
                'type': 'integer',
                'minimum': 1,
                'default': 100},
            'verbose':{
                'description':"""Whether to print errors from each of the trials if any. 
This is also logged using logger.warning in Hyperopt.""",
                'type':'boolean',
                'default':False},
            'scoring': {
                'description': 'Scorer object or known scorer named by string.',
                'anyOf': [
                {    'description': 'If None, use accuracy for classification and r2 for regression.',
                     'enum': [None]},                     
                {    'description': """Custom scorer object created with `make_scorer`_.

The argument to make_scorer can be one of scikit-learn's metrics_,
or it can be a user-written Python function to create a completely
custom scorer object, following the `model_evaluation`_ example.
The metric has to return a scalar value. Note that scikit-learns's
scorer object always returns values such that higher score is
better.

.. _`make_scorer`: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.make_scorer.html#sklearn.metrics.make_scorer.
.. _metrics: https://scikit-learn.org/stable/modules/classes.html#module-sklearn.metrics
.. _`model_evaluation`: https://scikit-learn.org/stable/modules/model_evaluation.html
""",
                     'not': {'type': ['string', 'null']}},
                {   'description': 'Known scorer for classification task.',
                    'enum': [
                        'accuracy', 'explained_variance', 'max_error',
                        'roc_auc', 'roc_auc_ovr', 'roc_auc_ovo',
                        'roc_auc_ovr_weighted', 'roc_auc_ovo_weighted',
                        'balanced_accuracy', 'average_precision',
                        'neg_log_loss', 'neg_brier_score']},
                {   'description': 'Known scorer for regression task.',
                    'enum': [
                        'r2', 'neg_mean_squared_error',
                        'neg_mean_absolute_error',
                        'neg_root_mean_squared_error',
                        'neg_mean_squared_log_error',
                        'neg_median_absolute_error']}],
                'default': None},
            'best_score': {
                'description': """The best score for the specified scorer.

This allows us to return a loss that is >=0,
where zero is the best loss.""",
                'type': 'number',
                'default': 0.0}}}]}

_input_fit_schema = {
    'type': 'object',
    'required': ['X', 'y'],
    'properties': {
        'X': {
            'type': 'array',
            'items': {
                'type': 'array',
                'items': {'laleType': 'Any'}}},
        'y': {
            'anyOf': [
            {   'type': 'array', 'items': {'type': 'number'}},
            {   'type': 'array', 'items': {'type': 'string'}},
            {   'type': 'array', 'items': {'type': 'boolean'}}]}}}

_input_predict_schema = {
    'type': 'object',
    'required': ['X'],
    'properties': {
        'X': {
            'type': 'array',
            'items': {
                'type': 'array',
                'items': {'laleType': 'Any'}}}}}

_output_predict_schema = {
    'anyOf': [
    {   'type': 'array', 'items': {'type': 'number'}},
    {   'type': 'array', 'items': {'type': 'string'}},
    {   'type': 'array', 'items': {'type': 'boolean'}}]}

_combined_schemas = {
    'description': """Automatically find a pipeline for a dataset.

This is a high-level entry point to get an initial trained pipeline
without having to specify your own planned pipeline first. It is
designed to be simple at the expense of not offering much control.
For an example, see `demo_auto_pipeline.ipynb`_.

.. _`demo_auto_pipeline.ipynb`: https://nbviewer.jupyter.org/github/IBM/lale/blob/master/examples/demo_auto_pipeline.ipynb
""",
    'documentation_url': 'https://lale.readthedocs.io/en/latest/modules/lale.lib.lale.auto_pipelines.html',
    'import_from': 'lale.lib.lale',
    'type': 'object',
    'tags': {
        'pre': [],
        'op': ['estimator'],
        'post': []},
    'properties': {
        'hyperparams': _hyperparams_schema,
        'input_fit': _input_fit_schema,
        'input_predict': _input_predict_schema,
        'output_predict': _output_predict_schema}}

lale.docstrings.set_docstrings(AutoPipelineImpl, _combined_schemas)

AutoPipeline = lale.operators.make_operator(AutoPipelineImpl, _combined_schemas)
