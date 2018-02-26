'''
Created on Nov 24, 2016

@author: agutierrez
'''

import abc
import logging
import pickle

import numpy
from sklearn import metrics

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "madmex.settings")
import django
django.setup()
from madmex.models import Model
from madmex.settings import SERIALIZED_OBJECTS_DIR
from madmex.util import randomword

LOGGER = logging.getLogger(__name__)

class BaseModel(object):
    '''
    This class works as a wrapper to have a single interface to several
    models and machine learning packages. This will hide the complexity
    of the different ways in which the algorithms are used. This is inteded
    to be used with the xarray package.
    '''
    __metaclass__ = abc.ABCMeta
    def __init__(self, params):
        '''
        Constructor
        '''

    def fit(self, X, y):
        '''
        This method will train the classifier with given data.
        '''
        raise NotImplementedError('subclasses of BaseModel must provide a fit() method')

    def predict(self, X):
        '''
        When the model is created, this method lets the user predict on unseen data.
        '''
        raise NotImplementedError('subclasses of BaseModel must provide a predict() method')

    def save(self, filepath):
        '''
        Write model to file
        '''
        with open(filepath, 'wb') as dst:
            pickle.dump(self.model, dst)

    def load(self, filepath):
        '''
        Read model from file
        '''
        with open(filepath) as src:
            mod = pickle.load(src)
        self.model = mod

    @classmethod
    def from_db(cls, name):
        inst = cls()
        model_row = Model.objects.get(name=name)
        filepath = model_row.path
        inst.load(filepath)
        return inst

    def to_db(self, name, recipe=None, training_set=None):
        """Write a model to the database

        In reality the model is written to file after being serialized and a reference
        to that file is written to the database.

        Args:
            name (str): Name/unique identifier to give to the model
            recipe (str): Name of the recipe used to fit the model (more like name of
                the product)
            training_set (str): Name of the training set used to fit the model
        """
        # Save to file
        filename = '%s_%s.pkl' % (name, randomword)
        filepath = os.path.join(SERIALIZED_OBJECTS_DIR, filename)
        self.save(filepath)
        # Create database entry
        m = Model(name=name, path=filepath, training_set=training_set,
                   recipe=recipe)
        m.save()

    def score(self, filepath):
        '''
        Lets the user load a previously trained model to predict with it. 
        '''
        raise NotImplementedError('subclasses of BaseModel must provide a score() method')

    def create_report(self, expected, predicted, filepath='report.txt'):
        '''
        Creates a report in the given filepath, it includes the confusion
        matrix, and information about the score. It contrasts expected and
        predicted outcomes.
        '''
        with open(filepath,'w') as report:
            report.write('Classification report for classifier:\n%s\n' % metrics.classification_report(expected, predicted))
            report.write('Confusion matrix:\n%s\n' % metrics.confusion_matrix(expected, predicted, labels=numpy.unique(expected)))