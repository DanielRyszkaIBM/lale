
from sklearn.ensemble.forest import ExtraTreesRegressor as SKLModel
import lale.helpers
import lale.operators
from numpy import nan, inf

class ExtraTreesRegressorImpl():

    def __init__(self, n_estimators=10, criterion='mse', max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='auto', max_leaf_nodes=None, min_impurity_decrease=0.0, min_impurity_split=None, bootstrap=False, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False):
        self._hyperparams = {
            'n_estimators': n_estimators,
            'criterion': criterion,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'min_weight_fraction_leaf': min_weight_fraction_leaf,
            'max_features': max_features,
            'max_leaf_nodes': max_leaf_nodes,
            'min_impurity_decrease': min_impurity_decrease,
            'min_impurity_split': min_impurity_split,
            'bootstrap': bootstrap,
            'oob_score': oob_score,
            'n_jobs': n_jobs,
            'random_state': random_state,
            'verbose': verbose,
            'warm_start': warm_start}

    def fit(self, X, y=None):
        self._sklearn_model = SKLModel(**self._hyperparams)
        if (y is not None):
            self._sklearn_model.fit(X, y)
        else:
            self._sklearn_model.fit(X)
        return self

    def predict(self, X):
        return self._sklearn_model.predict(X)
_hyperparams_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'inherited docstring for ExtraTreesRegressor    An extra-trees regressor.',
    'allOf': [{
        'type': 'object',
        'relevantToOptimizer': ['n_estimators', 'criterion', 'max_depth', 'min_samples_split', 'min_samples_leaf', 'max_features', 'bootstrap'],
        'additionalProperties': False,
        'properties': {
            'n_estimators': {
                'type': 'integer',
                'minimumForOptimizer': 10,
                'maximumForOptimizer': 100,
                'distribution': 'uniform',
                'default': 10,
                'description': 'The number of trees in the forest.'},
            'criterion': {
                'enum': ['friedman_mse', 'mse'],
                'default': 'mse',
                'description': 'The function to measure the quality of a split. Supported criteria'},
            'max_depth': {
                'anyOf': [{
                    'type': 'integer',
                    'minimumForOptimizer': 3,
                    'maximumForOptimizer': 5,
                    'distribution': 'uniform'}, {
                    'enum': [None]}],
                'default': None,
                'description': 'The maximum depth of the tree. If None, then nodes are expanded until'},
            'min_samples_split': {
                'anyOf': [{
                    'type': 'integer',
                    'minimumForOptimizer': 2,
                    'maximumForOptimizer': 5,
                    'distribution': 'uniform'}, {
                    'type': 'number',
                    'forOptimizer': False}],
                'default': 2,
                'description': 'The minimum number of samples required to split an internal node:'},
            'min_samples_leaf': {
                'anyOf': [{
                    'type': 'integer',
                    'minimumForOptimizer': 1,
                    'maximumForOptimizer': 5,
                    'distribution': 'uniform'}, {
                    'type': 'number',
                    'forOptimizer': False}],
                'default': 1,
                'description': 'The minimum number of samples required to be at a leaf node.'},
            'min_weight_fraction_leaf': {
                'type': 'number',
                'default': 0.0,
                'description': 'The minimum weighted fraction of the sum total of weights (of all'},
            'max_features': {
                'anyOf': [{
                    'type': 'integer',
                    'forOptimizer': False}, {
                    'type': 'number',
                    'minimumForOptimizer': 0.01,
                    'maximumForOptimizer': 1.0,
                    'distribution': 'uniform'}, {
                    'type': 'string',
                    'forOptimizer': False}, {
                    'enum': [None]}],
                'default': 'auto',
                'description': 'The number of features to consider when looking for the best split:'},
            'max_leaf_nodes': {
                'anyOf': [{
                    'type': 'integer'}, {
                    'enum': [None]}],
                'default': None,
                'description': 'Grow trees with ``max_leaf_nodes`` in best-first fashion.'},
            'min_impurity_decrease': {
                'type': 'number',
                'default': 0.0,
                'description': 'A node will be split if this split induces a decrease of the impurity'},
            'min_impurity_split': {
                'anyOf': [{
                    'type': 'number'}, {
                    'enum': [None]}],
                'default': None,
                'description': 'Threshold for early stopping in tree growth. A node will split'},
            'bootstrap': {
                'type': 'boolean',
                'default': False,
                'description': 'Whether bootstrap samples are used when building trees. If False, the'},
            'oob_score': {
                'type': 'boolean',
                'default': False,
                'description': 'Whether to use out-of-bag samples to estimate the R^2 on unseen data.'},
            'n_jobs': {
                'anyOf': [{
                    'type': 'integer'}, {
                    'enum': [None]}],
                'default': None,
                'description': 'The number of jobs to run in parallel for both `fit` and `predict`.'},
            'random_state': {
                'anyOf': [{
                    'type': 'integer'}, {
                    'type': 'object'}, {
                    'enum': [None]}],
                'default': None,
                'description': 'If int, random_state is the seed used by the random number generator;'},
            'verbose': {
                'type': 'integer',
                'default': 0,
                'description': 'Controls the verbosity when fitting and predicting.'},
            'warm_start': {
                'type': 'boolean',
                'default': False,
                'description': 'When set to ``True``, reuse the solution of the previous call to fit'},
        }}, {
        'description': 'min_samples_leaf, XXX TODO XXX, only be considered if it leaves at least min_samples_leaf training samples in each of the left and right branches'}],
}
_input_fit_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Build a forest of trees from the training set (X, y).',
    'type': 'object',
    'properties': {
        'X': {
            'anyOf': [{
                'type': 'array',
                'items': {
                    'XXX TODO XXX': 'item type'},
                'XXX TODO XXX': 'array-like or sparse matrix of shape = [n_samples, n_features]'}, {
                'type': 'array',
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'number'},
                }}],
            'description': 'The training input samples. Internally, its dtype will be converted'},
        'y': {
            'anyOf': [{
                'type': 'array',
                'items': {
                    'type': 'number'},
            }, {
                'type': 'array',
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'number'},
                }}],
            'description': 'The target values (class labels in classification, real numbers in'},
        'sample_weight': {
            'anyOf': [{
                'type': 'array',
                'items': {
                    'type': 'number'},
            }, {
                'enum': [None]}],
            'description': 'Sample weights. If None, then samples are equally weighted. Splits'},
    },
}
_input_predict_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Predict regression target for X.',
    'type': 'object',
    'properties': {
        'X': {
            'anyOf': [{
                'type': 'array',
                'items': {
                    'XXX TODO XXX': 'item type'},
                'XXX TODO XXX': 'array-like or sparse matrix of shape = [n_samples, n_features]'}, {
                'type': 'array',
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'number'},
                }}],
            'description': 'The input samples. Internally, its dtype will be converted to'},
    },
}
_output_predict_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'The predicted values.',
    'anyOf': [{
        'type': 'array',
        'items': {
            'type': 'number'},
    }, {
        'type': 'array',
        'items': {
            'type': 'array',
            'items': {
                'type': 'number'},
        }}],
}
_combined_schemas = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Combined schema for expected data and hyperparameters.',
    'type': 'object',
    'tags': {
        'pre': [],
        'op': ['estimator'],
        'post': []},
    'properties': {
        'hyperparams': _hyperparams_schema,
        'input_fit': _input_fit_schema,
        'input_predict': _input_predict_schema,
        'output_predict': _output_predict_schema},
}
if (__name__ == '__main__'):
    lale.helpers.validate_is_schema(_combined_schemas)
ExtraTreesRegressor = lale.operators.make_operator(ExtraTreesRegressorImpl, _combined_schemas)

