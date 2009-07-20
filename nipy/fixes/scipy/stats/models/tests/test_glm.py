"""
Test functions for models.GLM
"""

import numpy as np
import numpy.random as R    
from numpy.testing import *

import models
from models.glm import GLMtwo as GLM
from models.functions import add_constant, xi
from scipy import stats
from rmodelwrap import RModel
from rpy import r
import nose

W = R.standard_normal

DECIMAL = 4

class check_model_results(object):
    '''
    res2 should be either the results from RModelWrap
    or the results as defined in model_results_data
    '''
    def test_params(self):
        assert_almost_equal(self.res1.params, self.res2.params, DECIMAL)
    
    def test_standard_errors(self):
        assert_almost_equal(self.res1.bse, self.res2.bse, DECIMAL)
    
    def test_residuals(self):
        if isinstance(self.res2, RModel):
           assert_almost_equal(self.res1.resid_dev, self.res2.resid_dev, 
                DECIMAL)
        else:
            resids = np.column_stack((self.res1.resid_pearson, 
            self.res1.resid_dev, self.res1.resid_working, 
            self.res1.resid_anscombe, self.res1.resid_response))
            self.check_resids(resids, self.res2.resids)
            
    def test_aic_R(self):
        # R includes the estimation of the scale as a lost dof
# ... sometimes only apparently ?!? Doesn't with Gamma...
        if self.res1.scale != 1:
            dof = 2
        else: dof = 0 
        self.check_aic_R(self.res1.information_criteria()['aic']+dof,
                self.res2.aic_R)

    def test_aic_Stata(self):
        if isinstance(self.res2, RModel):
            raise nose.SkipTest("Results are from RModel wrapper")
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
            raise nose.SkipTest("Results are from RModel wrapper")
        self.check_bic(self.res1.information_criteria()['bic'],
            self.res2.bic)

    def test_degrees(self):
        if not isinstance(self.res2, RModel):
            assert_almost_equal(self.res1.df_model,self.res2.df_model, DECIMAL)
        assert_almost_equal(self.res1.df_resid,self.res2.df_resid, DECIMAL) 

    def test_pearsonX2(self):
        if isinstance(self.res2, RModel):
            raise nose.SkipTest("Results are from RModel wrapper")
        self.check_pearsonX2(self.res1.pearsonX2, self.res2.pearsonX2)

class test_glm_gaussian(check_model_results):
    def __init__(self):
        '''
        Test Gaussian family with canonical identity link
        '''
        from models.datasets.longley.data import load
        data = load()
        data.exog = add_constant(data.exog)
        self.res1 = GLM(data.endog,data.exog, 
                        family=models.family.Gaussian()).fit()
        Gauss = r.gaussian
        self.res2 = RModel(data.endog, data.exog, r.glm, family=Gauss)
        self.res2.resids = np.array(self.res2.resid)[:,None]*np.ones((1,5))
        self.res2.null_deviance = 185008826 # taken from R.  
                                            # I think this is a bug in Rpy

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

    def test_log(self):
        nobs = 100
        x = np.arange(nobs)
        y = 1.0 + 2.0*x + x**2 + 0.1 * np.random.randn(nobs)
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

    def test_power(self):
        pass

class test_glm_binomial(check_model_results):
    def __init__(self):
        '''
        Test Binomial family with canonical logit link
        '''
        from models.datasets.star98.data import load
        from model_results import star98
        data = load()
        data.exog = add_constant(data.exog)
        trials = data.endog[:,:2].sum(axis=1)
        self.res1 = GLM(data.endog, data.exog, \
        family=models.family.Binomial()).fit(data_weights = trials)
        self.res2 = star98()
        self.KnownFailPrec = True # Stata rounds big residuals to zero decimals
                                  # So PearsonX2 fails
   
    @dec.knownfailureif(True, "Fails due to a rounding convention in Stata")
    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    def check_aic_Stata(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)
    
    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL-1) # precise up to 3 decimals

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL-2) # accurate to 1e-02

    @dec.knownfailureif(True, "This is a known failure due to a rounding \
in the Pearson residuals in Stata")
    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)
    
    def test_log(self):
        pass

    def test_logit(self):
        pass

    def test_probit(self):
        pass

    def test_cloglog(self):
        pass

    def test_power(self):
        pass

    def test_loglog(self):
        pass

    def test_logc(self):
        pass

class test_glm_bernoulli(check_model_results):
    def __init__(self):
        from model_results import lbw
        self.res2 = lbw() 
        self.res1 = GLM(self.res2.endog, self.res2.exog, 
                family=models.family.Binomial()).fit()

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
    
    def test_identity(self):
        pass

    def test_log(self):
        pass
    
    def test_probit(self):
        pass

    def test_cloglog(self):
        pass

    def test_power(self):
        pass

    def test_loglog(self):
        pass

    def test_logc(self):
        pass

class test_glm_gamma(check_model_results):
      
    def __init__(self):
        '''
        Tests Gamma family with canonical inverse link (power -1)
        '''
        from models.datasets.scotland.data import load
        from model_results import scotvote
        data = load()
        data.exog = add_constant(data.exog)
        self.res1 = GLM(data.endog, data.exog, \
                    family=models.family.Gamma()).fit()
        self.res2 = scotvote()
        self.KnownFailPrec = True   # precision issue in AIC_R
        self.SkipDef = True # different loglike definition used
                            # so LLF and AIC fail
        
    @dec.knownfailureif(True, "This fails because Stata rounds large residuals \
to some determined significant digits")
    def check_resids(self, resids1, resids2):
        assert_almost_equal(resids1, resids2, DECIMAL)

    @dec.knownfailureif(True, "This test fails due to R's implementation being \
different, but ours is mathematically correct.")
    def check_aic_R(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    @dec.knownfailureif(True, "Failure due to definitional difference of \
loglikelihood in Gamma family vs. Stata")
    def check_aic_Stata(self, aic1, aic2):
        assert_almost_equal(aic1, aic2, DECIMAL)

    @dec.knownfailureif(True, "Failure due to definitional difference of \
loglikelihood in Gamma family vs. Stata")
    def check_loglike(self, llf1, llf2):
        assert_almost_equal(llf1, llf2, DECIMAL)

    def check_bic(self, bic1, bic2):
        assert_almost_equal(bic1, bic2, DECIMAL)

    def check_pearsonX2(self, pearsonX21, pearsonX22):
        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL)

    def test_log(self):
        pass

    def test_power(self):
        pass

class test_glm_poisson(check_model_results):
    def __init__(self):
        '''
        Tests Poisson family with canonical log link.

        Test results were obtained by R.
        '''
        from model_results import cpunish
        from models.datasets.cpunish.data import load
        data = load()
        data.exog[:,3] = np.log(data.exog[:,3])
        data.exog = add_constant(data.exog)
        self.res1 = GLM(data.endog, data.exog, 
                    family=models.family.Poisson()).fit()
        self.res2 = cpunish()

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

    def test_identity(self):
        pass

    def test_power(self):
        pass

#class test_glm_invgauss(check_model_results):
#    @dec.slow
#    def __init__(self):
#        '''
#        Tests the Inverse Gaussian family in GLM.
#
#        Notes
#        -----
#        Used the rndivgx.ado file provided by Hardin and Hilbe to
#        generate the data.
#        '''
#        from model_results import inv_gauss
#        self.res2 = inv_gauss()
#        self.res1 = GLM(self.res2.endog, self.res2.exog, \
#                family=models.family.InverseGaussian()).fit()
#
#    def check_resids(self, resids1, resids2):
#        assert_almost_equal(resids1, resids2, DECIMAL)
#
#    @dec.knownfailureif(True, "Precision issue due to implementation difference.")
#    def check_aic_R(self, aic1, aic2):
#        assert_almost_equal(aic1, aic2, DECIMAL)
#    
#    @dec.knownfailureif(True, "From definitional difference with loglikelihood")
#    def check_aic_Stata(self, aic1, aic2):
#        assert_almost_equal(aic1, aic2, DECIMAL)

#    @dec.knownfailureif(True, "Definitional difference with Stata")
#    def check_loglike(self, llf1, llf2):
#        assert_almost_equal(llf1, llf2, DECIMAL)

#    def check_bic(self, bic1, bic2):
#        assert_almost_equal(bic1, bic2, DECIMAL-2)  # precision in STATA

#    def check_pearsonX2(self, pearsonX21, pearsonX22):
#        assert_almost_equal(pearsonX21, pearsonX22, DECIMAL-1)  # summed resids

#    def test_log(self):
#        pass

#    def test_power(self):
#        pass

class test_glm_negbinomial(check_model_results):
    def __init__(self):
        '''
        Test Negative Binomial family with canonical log link
        '''       
        from models.datasets.committee.data import load
        data = load()
        data.exog[:,2] = np.log(data.exog[:,2])
        interaction = data.exog[:,2]*data.exog[:,1]
        data.exog = np.column_stack((data.exog,interaction))
        data.exog = add_constant(data.exog)
        results = GLM(data.endog, data.exog, 
                family=models.family.NegativeBinomial()).fit()
        self.res1 = results
#        r.library('MASS')  # this doesn't work when done in rmodelwrap?
        self.res2 = RModel(data.endog, data.exog, r.glm, 
                family=r.negative_binomial(1))

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

    def test_log(self):
        pass

    def test_power(self):
        pass

    def test_nbinom(self):
        pass

if __name__=="__main__":
    run_module_suite()
