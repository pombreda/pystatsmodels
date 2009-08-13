"""
Test functions for models.GLM
"""

import numpy as np
import numpy.random as R    
from numpy.testing import *

import models
from models.glm import GLM
from models.tools import add_constant, xi
from scipy import stats
from rmodelwrap import RModel
from nose import SkipTest
from check_for_rpy import skip_rpy

W = R.standard_normal

DECIMAL = 4
DECIMAL_less = 3
DECIMAL_lesser = 2
DECIMAL_least = 1
DECIMAL_none = 0
skipR = skip_rpy()
if not skipR:
    from rpy import r
    
class check_model_results(object):
    '''
    res2 should be either the results from RModelWrap
    or the results as defined in model_results_data
    '''
    def test_params(self):
        self.check_params(self.res1.params, self.res2.params)
    
    def test_standard_errors(self):
        assert_almost_equal(self.res1.bse, self.res2.bse, DECIMAL)
    
    def test_residuals(self):
        if isinstance(self.res2, RModel) and not hasattr(self.res2, 'resids'):
           assert_almost_equal(self.res1.resid_dev, self.res2.resid_dev, 
                DECIMAL)
        else:
            resids = np.column_stack((self.res1.resid_pearson, 
            self.res1.resid_dev, self.res1.resid_working, 
            self.res1.resid_anscombe, self.res1.resid_response))
            self.check_resids(resids, self.res2.resids)
            
    def test_aic_R(self):
        # R includes the estimation of the scale as a lost dof
        # Doesn't with Gamma though
        if self.res1.scale != 1:
            dof = 2
        else: dof = 0 
        self.check_aic_R(self.res1.information_criteria()['aic']+dof,
                self.res2.aic_R)

    def test_aic_Stata(self):
        if isinstance(self.res2, RModel):
            raise SkipTest("Results are from RModel wrapper")
        aic = self.res1.information_criteria()['aic']/self.res1.nobs
        self.check_aic_Stata(aic, self.res2.aic_Stata)
            
    def test_deviance(self):
        assert_almost_equal(self.res1.deviance, self.res2.deviance, DECIMAL)

    def test_scale(self):
        assert_almost_equal(self.res1.scale, self.res2.scale, DECIMAL)

    def test_loglike(self):
        self.check_loglike(self.res1.llf, self.res2.llf)

    def test_null_deviance(self):
        assert_almost_equal(self.res1.null_deviance, self.res2.null_deviance,
                    DECIMAL)
    
    def test_bic(self):
        if isinstance(self.res2, RModel):
            raise SkipTest("Results are from RModel wrapper")
        self.check_bic(self.res1.information_criteria()['bic'],
            self.res2.bic)

    def test_degrees(self):
        if not isinstance(self.res2, RModel):
            assert_almost_equal(self.res1.df_model,self.res2.df_model, DECIMAL)
        assert_almost_equal(self.res1.df_resid,self.res2.df_resid, DECIMAL) 

    def test_pearsonX2(self):
        if isinstance(self.res2, RModel):
            raise SkipTest("Results are from RModel wrapper")
        self.check_pearsonX2(self.res1.pearsonX2, self.res2.pearsonX2)

class test_glm_gaussian(check_model_results):
    def __init__(self):
        '''
        Test Gaussian family with canonical identity link
        '''
        from models.datasets.longley.data import load
        self.data = load()
        self.data.exog = add_constant(self.data.exog)
        self.res1 = GLM(self.data.endog, self.data.exog, 
                        family=models.family.Gaussian()).fit()
        Gauss = r.gaussian
        self.res2 = RModel(self.data.endog, self.data.exog, r.glm, family=Gauss)
        self.res2.resids = np.array(self.res2.resid)[:,None]*np.ones((1,5))
        self.res2.null_deviance = 185008826 # taken from R.  
                                            # I think this is a bug in Rpy

    def setup(self):
        if skipR:
            raise SkipTest, "Rpy not installed."

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)
    
    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_aic_Stata(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL)

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL)

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)

class test_gaussian_log(check_model_results):
    def __init__(self):
        nobs = 100
        x = np.arange(nobs)
        np.random.seed(54321)
#        y = 1.0 - .02*x - .001*x**2 + 0.001 * np.random.randn(nobs)
        X = np.c_[np.ones((nobs,1)),x,x**2]
        lny = np.exp(-(-1.0 + 0.02*x + 0.0001*x**2)) +\
                        0.001 * np.random.randn(nobs)

        GaussLog_Model = GLM(lny, X, \
                family=models.family.Gaussian(models.family.links.log))
        GaussLog_Res = GaussLog_Model.fit()
        GaussLogLink = r.gaussian(link = "log")
        GaussLog_Res_R = RModel(lny, X, r.glm, family=GaussLogLink)
        self.res1 = GaussLog_Res
        self.res2 = GaussLog_Res_R

    def setup(self):
        if skipR:
            raise SkipTest, "Rpy not installed"

    def test_null_deviance(self):
        assert_almost_equal(self.res1.null_deviance, self.res2.null_deviance,
                    DECIMAL_least)

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)
    
    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL_none)
    
    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL_none)
#TODO: is this a full test?

class test_gaussian_inverse(check_model_results):
    def __init__(self):
        nobs = 100
        x = np.arange(nobs)
        np.random.seed(54321)
        y = 1.0 + 2.0 * x + x**2 + 0.1 * np.random.randn(nobs)
        X = np.c_[np.ones((nobs,1)),x,x**2]
        y_inv = (1. + .02*x + .001*x**2)**-1 + .001 * np.random.randn(nobs)
        InverseLink_Model = GLM(y_inv, X, 
                family=models.family.Gaussian(models.family.links.inverse))
        InverseLink_Res = InverseLink_Model.fit()
        InverseLink = r.gaussian(link = "inverse")
        InverseLink_Res_R = RModel(y_inv, X, r.glm, family=InverseLink)
        self.res1 = InverseLink_Res
        self.res2 = InverseLink_Res_R

    def setup(self):
        if skipR:
            raise SkipTest, "Rpy not installed."

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL_least)

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL_least)
#TODO: is this a full test?

    @dec.knownfailureif(True, "This is a bug in Rpy")
    def test_null_deviance(self):
        assert_almost_equal(self.res1.null_deviance, self.res2.null_deviance,
                    DECIMAL_least)

class test_glm_binomial(check_model_results):
    def __init__(self):
        '''
        Test Binomial family with canonical logit link
        '''
        from models.datasets.star98.data import load
        from model_results import star98
        self.data = load()
        self.data.exog = add_constant(self.data.exog)
        trials = self.data.endog[:,:2].sum(axis=1)
        self.res1 = GLM(self.data.endog, self.data.exog, \
        family=models.family.Binomial()).fit(data_weights = trials)
        self.res2 = star98()

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)

    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL_least)
        # rounding difference vs. stata

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_aic_Stata(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)
    
    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL_less) 
        # precise up to 3 decimals

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL_lesser) 
        # accurate to 1e-02

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL_lesser)
        # Pearson's X2 sums residuals that are rounded differently in Stata
#TODO:
#Non-Canonical Links for the Binomial family require the algorithm to be
#slightly changed
#class test_glm_binomial_log(check_model_results):
#    pass

#class test_glm_binomial_logit(check_model_results):
#    pass

#class test_glm_binomial_probit(check_model_results):
#    pass

#class test_glm_binomial_cloglog(check_model_results):
#    pass

#class test_glm_binomial_power(check_model_results):
#    pass

#class test_glm_binomial_loglog(check_model_results):
#    pass

#class test_glm_binomial_logc(check_model_results):
#TODO: need include logc link
#    pass

class test_glm_bernoulli(check_model_results):
    def __init__(self):
        from model_results import lbw
        self.res2 = lbw() 
        self.res1 = GLM(self.res2.endog, self.res2.exog, 
                family=models.family.Binomial()).fit()

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)    
        
    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_aic_Stata(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL)

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL)

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)

#class test_glm_bernoulli_identity(check_model_results):
#    pass

#class test_glm_bernoulli_log(check_model_results):
#    pass

#class test_glm_bernoulli_probit(check_model_results):
#    pass
    
#class test_glm_bernoulli_cloglog(check_model_results):
#    pass

#class test_glm_bernoulli_power(check_model_results):
#    pass

#class test_glm_bernoulli_loglog(check_model_results):
#    pass

#class test_glm_bernoulli_logc(check_model_results):
#    pass

class test_glm_gamma(check_model_results):
      
    def __init__(self):
        '''
        Tests Gamma family with canonical inverse link (power -1)
        '''
        from models.datasets.scotland.data import load
        from model_results import scotvote
        self.data = load()
        self.data.exog = add_constant(self.data.exog)
        self.res1 = GLM(self.data.endog, self.data.exog, \
                    family=models.family.Gamma()).fit()
        self.res2 = scotvote()
        self.KnownFailPrec = True   # precision issue in AIC_R
        self.SkipDef = True # different loglike definition used
                            # so LLF and AIC fail
    
    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)    
    
    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL_lesser)

    def check_aic_R(self, aic1, aic2):
        assert_approx_equal(aic1-2, aic2, DECIMAL_less)  
        # R includes another degree of freedom in calculation of AIC, but not with
        # gamma for some reason
        # There is also a precision issue due to a different implementation

    def check_aic_Stata(self, aic1, aic2):
        llf1 = self.res1.model.family.logL(self.res1.model.y, 
                self.res1.mu, scale=1)
        aic1 = 2 *(self.res1.df_model + 1 - llf1)/self.res1.nobs
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        llf1 = self.res1.model.family.logL(self.res1.model.y, 
                self.res1.mu, scale=1)
        assert_almost_equal(llf1, llf2, DECIMAL)

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL)

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)

#TODO: add cancer.dta from stata for gamma tests
#class test_glm_gamma_log(check_model_results):
#    pass


#class test_glm_gamma_identity(check_model_results):
#    pass

class test_glm_poisson(check_model_results):
    def __init__(self):
        '''
        Tests Poisson family with canonical log link.

        Test results were obtained by R.
        '''
        from model_results import cpunish
        from models.datasets.cpunish.data import load
        self.data = load()
        self.data.exog[:,3] = np.log(self.data.exog[:,3])
        self.data.exog = add_constant(self.data.exog)
        self.res1 = GLM(self.data.endog, self.data.exog, 
                    family=models.family.Poisson()).fit()
        self.res2 = cpunish()

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)

    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_aic_Stata(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL)

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL)

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)

#class test_glm_poisson_identity(check_model_results):
#    pass

#class test_glm_poisson_power(check_model_results):
#    pass

#FIXME: remove comment when finished
#@dec.slow
class test_glm_invgauss(check_model_results):
    def __init__(self):
        '''
        Tests the Inverse Gaussian family in GLM.

        Notes
        -----
        Used the rndivgx.ado file provided by Hardin and Hilbe to
        generate the data.
        '''
        from model_results import inv_gauss
        self.res2 = inv_gauss()
        self.res1 = GLM(self.res2.endog, self.res2.exog, \
                family=models.family.InverseGaussian()).fit()

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL)

    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    def check_aic_R(self, aic1, aic2):
        assert_approx_equal(aic1, aic2, DECIMAL)
        # Off by 2e-1 due to implementation difference

    def check_aic_Stata(self, aic1, aic2):
        llf1 = self.res1.model.family.logL(self.res1.model.y, self.res1.mu,
                scale=1)
        aic1 = 2 * (self.res1.df_model + 1 - llf1)/self.res1.nobs
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        llf1 = self.res1.model.family.logL(self.res1.model.y, self.res1.mu,
                scale=1)    # Stata assumes scale = 1 in calc, 
                            # which shouldn't be right
        assert_almost_equal(llf1, llf2, DECIMAL_less)

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL-2)  # precision in STATA

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL-1)  # summed resids

#TODO: get madpar data for noncanonical links, H&H 110
#class test_glm_invgauss_log(check_model_results):
#    pass

#class test_glm_invgauss_identity(check_model_results):
#    pass

class test_glm_negbinomial(check_model_results):
#TODO: Include all residuals from Stata
# Implement Anscombe residuals for negative binomial
    def __init__(self):
        '''
        Test Negative Binomial family with canonical log link
        '''
        from models.datasets.committee.data import load
        self.data = load()
        self.data.exog[:,2] = np.log(self.data.exog[:,2])
        interaction = self.data.exog[:,2]*self.data.exog[:,1]
        self.data.exog = np.column_stack((self.data.exog,interaction))
        self.data.exog = add_constant(self.data.exog)
        results = GLM(self.data.endog, self.data.exog, 
                family=models.family.NegativeBinomial()).fit()
        self.res1 = results
        r.library('MASS')  # this doesn't work when done in rmodelwrap?
        self.res2 = RModel(self.data.endog, self.data.exog, r.glm, 
                family=r.negative_binomial(1))
        self.res2.null_deviance = 27.8110469364343
        # Rpy does not return the same null deviance as R for some reason

    def setup(self):
        if skipR:
            raise SkipTest, "Rpy not installed"

    def check_params(self, params1, params2):
        assert_almost_equal(params1, params2, DECIMAL-1)    # precision issue

    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1-2, aic2, DECIMAL)
        # note that R subtracts an extra degree of freedom for estimating
        # the scale

    def check_aic_Stata(self, aic1, aic2):
        aic1 = aci1/self.res1.nobs
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL)
    
    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL)

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)

#class test_glm_negbinomial_log(check_model_results):
#    pass

#class test_glm_negbinomial_power(check_model_results):
#    pass

#class test_glm_negbinomial_nbinom(check_model_results):
#    pass

if __name__=="__main__":
    run_module_suite()
