'''
Created on Jun 25, 2018

@author: agutierrez
'''
import logging
import  math

import numpy
from scipy import linalg, stats

from madmex.lcc.bitemporal import BaseBiChange


logger = logging.getLogger(__name__)

class IMAD(object):
    def __init__(self, max_iterations=25, min_delta=0.02):
        self.max_iterations = max_iterations
        self.min_delta = min_delta
    
    def fit(self, X, Y):
        self.X = X
        self.Y = Y
        self.bands, self.rows, self.columns = self.X.shape
    
    def transform(self, X, Y):
        image_bands_flattened = numpy.zeros((2 * self.bands, self.columns * self.rows))
        for k in range(self.bands):
            image_bands_flattened[k, :] = numpy.ravel(self.X[k, :, :])
            image_bands_flattened[self.bands + k, :] = numpy.ravel(self.Y[k, :, :])
        NO_DATA = 0
        no_data_X = image_bands_flattened[0, :] == NO_DATA
        no_data_Y = image_bands_flattened[self.bands, :] == NO_DATA
        data_mask = (no_data_X | no_data_Y) == False
        self.image_bands_flattened = image_bands_flattened[:, data_mask]
        data_mask_sum = numpy.sum(data_mask)
        self.weights = numpy.ones(int(data_mask_sum)) # we start with weights defined as ones.
        self.outcorrlist = []
        i = 0
        logger.info('Starting iMAD iterations.')  
        old_rho = numpy.zeros(self.bands)
        delta = 1.0
        flag = True
        while (delta > self.min_delta) and (i < self.max_iterations) and flag:
            try:
                logger.info('iMAD iteration: %d', i)
                weighted_sum = numpy.sum(self.weights)
                means = numpy.average(self.image_bands_flattened, axis=1, weights=self.weights)
                dmc = self.image_bands_flattened - means[:, numpy.newaxis]
                dmc = numpy.multiply(dmc, numpy.sqrt(self.weights))
                sigma = numpy.dot(dmc, dmc.T) / weighted_sum
                s11 = sigma[0:self.bands, 0:self.bands]
                s22 = sigma[self.bands:, self.bands:]
                s12 = sigma[0:self.bands, self.bands:]
                s21 = sigma[self.bands:, 0:self.bands]
                aux_1 = linalg.solve(s22, s21)
                lamda_a, a = linalg.eig(numpy.dot(s12, aux_1), s11)
                aux_2 = linalg.solve(s11, s12)
                lamda_b, b = linalg.eig(numpy.dot(s21, aux_2), s22)
                # sort a
                sorted_indexes = numpy.argsort(lamda_a)
                a = a[:, sorted_indexes]
                # sort b        
                sorted_indexes = numpy.argsort(lamda_b)
                b = b[:, sorted_indexes]          
                # canonical correlations        
                rho = numpy.sqrt(numpy.real(lamda_b[sorted_indexes])) 
                self.delta = numpy.sum(numpy.abs(rho - old_rho))
                if(not math.isnan(self.delta)):
                    self.outcorrlist.append(rho)
                    # normalize dispersions  
                    tmp1 = numpy.dot(numpy.dot(a.T, s11), a)
                    tmp2 = 1. / numpy.sqrt(numpy.diag(tmp1))
                    tmp3 = numpy.tile(tmp2, (self.bands, 1))
                    a = numpy.multiply(a, tmp3)
                    b = numpy.mat(b)
                    tmp1 = numpy.dot(numpy.dot(b.T, s22), b)
                    tmp2 = 1. / numpy.sqrt(numpy.diag(tmp1))
                    tmp3 = numpy.tile(tmp2, (self.bands, 1))
                    b = numpy.multiply(b, tmp3)
                    # assure positive correlation
                    tmp = numpy.diag(numpy.dot(numpy.dot(a.T, s12), b))
                    b = numpy.dot(b, numpy.diag(tmp / numpy.abs(tmp)))
                    # canonical and MAD variates
                    U = numpy.dot(a.T, (self.image_bands_flattened[0:self.bands, :] - means[0:self.bands, numpy.newaxis]))    
                    V = numpy.dot(b.T, (self.image_bands_flattened[self.bands:, :] - means[self.bands:, numpy.newaxis]))          
                    T = U - V  # TODO: is this operation stable?
                    # new weights        
                    var_mad = numpy.tile(numpy.mat(2 * (1 - rho)).T, (1, data_mask_sum))    
                    chi_squared = numpy.sum(numpy.multiply(T, T) / var_mad, 0)
                    self.weights = numpy.squeeze(1 - numpy.array(stats.chi2._cdf(chi_squared, self.bands))) 
                    old_rho = rho
                    logger.info('Processing of iteration %d finished [%f] ...', i, numpy.max(self.delta))
                    i = i + 1
                else:
                    flag = False
                    logger.warning('Some error happened.')
            except Exception as error:
                flag = False
                logger.error('iMAD transform failed with error: %s', str(repr(error))) 
                logger.error('Processing in iteration %d produced error. Taking last MAD of iteration %d' % (i, i - 1))
        output_flat = numpy.zeros((self.bands, self.columns * self.rows))
        output_flat[0:self.bands, data_mask] = T
        output = numpy.zeros((self.bands, self.rows, self.columns))
        for b in range(self.bands):
            output[b, :, :] = (numpy.resize(output_flat[b, :], (self.rows, self.columns)))
        return output, chi_squared

    def fit_transform(self, X, Y):
        self.fit(X, Y)
        return self.transform(X, Y)

class BiChange(BaseBiChange):
    '''
    Process to detect land cover change using the iteratively reweighted
    Multivariate Alteration Detection algorithm and then postprocesing
    the output using the Maximum Autocorrelation Factor.
    '''


    def __init__(self,  array, affine, crs):
        '''
        Constructor
        '''
        super.__init__(array=array, affine=affine, crs=crs)
    
    def _run(self, arr0, arr1):
        pass