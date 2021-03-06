#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

This module implements the toy setting of two Gaussian random vectors x and y.
The vectors have the same length and are generally statistically dependent.

The main function is ''gaussian_example'' that generates data from x and y, and
computes the exact mutual information (MI) between them.

Example 1
---------

Generate 500 samples from two 10 dimensional random vectors x and y:

data_x, data_y, MI, gen_params = gaussian_example(dim=10, nsamples=500)

data_x and data_y are 10x500 ndarrays, MI is the mutual information, and gen_params is a
dictionary with the model parameters used to generate the data.

Example 2
---------

To control the value of the mutual information you can set the optional argument rhoz_lims.
Default is rhoz_lims=(0,1), to generate random variables with larger MI, set the lower limit closer to one, e.g.
rhoz_lims = (0.8, 1) or, for a larger value of MI: rhoz_lims = (0.9, 1):

data_x, data_y, MI, gen_params = gaussian_example(dim=10, nsamples=500, rhoz_lims=(0.8, 0.9))

See the docstring of ''gaussian_example'' for further information.

"""

import numpy as np
from scipy import linalg


class Gaussian():
    
    def __init__(self, seed):
        self.seed = np.random.seed(seed)

        
    
    def generate_example(self, dim=10, n_samples=500, rhoz_lims=(0, 1), cond=(10, 10)):
            
    	"""	
        Sampling from a multivariate Gaussian distribution and calculates the true mutual information value.
    
    	Parameters
    	----------
    	dim         : int
    	              dimension of x and y (should be equivalent)
    	n_samples   : int
    	              number of samples to generate
    	rhoz_lims   : tuple
    	              interval (a,b) on which to sample the absolute value of the correlation coefficients
    	              0<a<b<1. Setting a and b close to 1 generates data with large mutual information.
    	cond        : tuple
    	              target conditioning numbers for the covariance matrices of x and y
    
    	Returns
    	-------
    	data_x      : array, shape=(n,dim)
    	              generated data set for x 
    	data_y      : array, shape=(n,dim)
    	              generated data set for y 
    	MI          : float
    	              the true mutual information value between x and y
    	gen_params  : dict
    	              dictionary of sigma_xx, sigma_yy, rhoz
    
    	"""
                   
    	# sample correlation coefficients between zx and zy
    	rhoz = np.random.uniform(low=rhoz_lims[0], high=rhoz_lims[1], size=dim)
    	rhoz = rhoz*((np.random.uniform(size=dim) < 0.5)-0.5)*2
    
    	# compute mutual information
    	MI = -0.5*np.sum(np.log(1-rhoz**2))
    
    	# generate data
    	zx = np.random.normal(loc=0, scale=1, size=(dim, n_samples))
    	zy = rhoz.T*zx.T+np.sqrt(1-rhoz.T**2)*np.random.normal(loc=0, scale=1, size=(n_samples, dim))
    	zy = zy.T
    
    	sigma_xx, spectrum_xx, eigenvectors_xx = self.sample_cov_matrix(dim, cond[0])
    	data_x = eigenvectors_xx @ np.diag(np.sqrt(spectrum_xx)) @ zx
    
    	sigma_yy, spectrum_yy, eigenvectors_yy = self.sample_cov_matrix(dim, cond[1])
    	data_y = eigenvectors_yy @ np.diag(np.sqrt(spectrum_yy)) @ zy
    
    	# return
    	gen_params = {"sigma_xx": sigma_xx, "sigma_yy": sigma_yy, "rhoz": rhoz}
    	return data_x, data_y, MI, gen_params
    
    
    def sample_cov_matrix(self, dim, cond):
    
    	""" generate a covariance matrix of size dim x dim
    
    	Parameters
    	----------
    	dim: int
    	    dimension of the covariance matrix
    	cond_number: float
    	    target conditioning number
    
    	Returns
    	-------
    	cov_matrix: ndarray (dim,dim)
    	    the covariance matrix
    	spectrum: ndarray (dim,)
    	    its eigenvalues
    	eigenvectors: ndarray (dim,dim)
    	    its eigenvectors (in the columns of the matrix)
    
    	"""
        
    	# generate spectrum (so that covariance matrix has approximately the target conditioning number)
    	spectrum = np.random.uniform(low=1, high=cond, size=(dim,))
    	spectrum = -np.sort(-spectrum)
    
    	# generate rotation matrix
    	mini = -1
    	eigenvectors = np.eye(dim)
    	while mini < 0:
    		M = np.random.normal(loc=0, scale=1, size=(dim, dim))
    		M = M @ M.T
    		dummy_spectrum, eigenvectors = linalg.eigh(M)
    		mini = dummy_spectrum.min()
    
    	# generate covariance matrix
    	cov_matrix = eigenvectors @ np.diag(spectrum) @ eigenvectors.T
    
    	return cov_matrix, spectrum, eigenvectors
    
    
    def compute_gaussian_mi(self, cov_matrix, dim):
    
    	""" computes the value of the mutual information between random variables (x,y) from their covariance matrix
    
    	The mutual information (MI) is computed from the formula
    	MI = -0.5 \log \det (I-Bxy*Byx)
    	Bxy = sigma_xx^{-1}*sigma_xy
    	Byx = sigma_yy^{-1}*sigma_yx  where sigma_yx = sigma_xy.T
    	I == identity matrix of size dim(x)
    
    	Parameters
    	----------
    	cov_matrix: ndarray
    	    covariance matrix of (x,y), assumed to be structured as [sigma_xx sigma_xy; sigma_yx sigma_yy]
    	dim: int
    	    dimension of x
    
    	Returns
    	-------
    	MI: int
    	    the value of the mutual information
    
    	"""
    
    	sigma_xx = cov_matrix[:dim, :dim]
    	sigma_xy = cov_matrix[:dim, dim:]
    	sigma_yy = cov_matrix[dim:, dim:]
    
    	Bxy = linalg.inv(sigma_xx)@sigma_xy
    	Byx = linalg.inv(sigma_yy)@sigma_xy.T
    	MI = -0.5*np.log(linalg.det(np.eye(dim) - Bxy@Byx))
    
    	return MI
    
    
    def estimate_mvn_mi(self, data):
    
    	""" Computes the mutual information from data (x,y) that are assumed to be Gaussian distributed.
    
    	The estimation is done naively by estimating the covariance matrix from the provided data.
    
    	Parameters
    	----------
    	data: ndarray (dimx+dimy, nsamples)
    	    the data matrix, we assume that the dimension of x, dimx, is the same as the dimension of y, dimy.
    
    	Returns
    	-------
    	MI: float
    	    the value of the mutual information
    
    	"""
    
    	Chat = np.cov(data)  # covariance matrix
    	dim = int(Chat.shape[0]/2)
    
    	MIhat = self.compute_gaussian_mi(Chat, dim)
    
    	return MIhat
    
    
    
    
    
    
    

