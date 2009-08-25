'''
The one parameter exponential family distributions used by GLM.
'''
#TODO: quasi, quasibinomial, quasipoisson
#see http://www.biostat.jhsph.edu/~qli/biostatistics_r_doc/library/stats/html/family.html
# for comparison to R, and McCullagh and Nelder

import numpy as np
from scipy import special
from scipy.stats import ss
import links as L
import varfuncs as V

class Family(object):

    """
    The parent class for one-parameter exponential families.

    Parameters
    ----------
    link : a link function instance
        Link is the linear transformation function.
        See the individual families for available links.
    variance : a variance function
        Measures the variance as a function of the mean probabilities.
        See the individual families for the default variance function.

    Methods
    -------
    deviance
        Returns the deviance function of a (Y,mu) pair for a model.
        Deviance is usually defined as twice the loglikelihood ratio of a 
        fitted model.
        Deviance = sum_i(2loglike(Y_i,Y_i) - 2loglike(Y_i,mu_i)) / scale
        Where loglike is defined for each family.
    devresid
        Returns the deviance residuals for a fitted model.
        `devresid` is defined for each family.
    fitted
        Returns the fitted values based on the linear predictor of the model.
        Calls the inverse of the link function.
    loglike
        The loglikelihood function.  `loglike` is defined for each family.
    predict
        The linear predictors based on a given `mu`.  Returns the link's call
        method.
    resid_anscombe
        The Anscombe residuals.  `resid_anscombe` is defined for each family.
        In general, the Anscombe residuals are defined as
        `resid_anscombe` = 
            (A(Y_i) - A(mu_hat_i))/(A'(mu_hat_i)*sqrt(V(mu_hat_i)))
            where A(.) = integral(dmu/V^(1/3)(mu)) and
            V is the variance function.  
    starting_mu
        The value of mu at the start of the IRLS algorithm.
    weights
        The weighting function used in the IRLS algorithm.
        `weights` = 1 / (link'(mu)**2 * variance(mu))
    """
#TODO: change these class attributes, use valid somewhere...
    valid = [-np.inf, np.inf]

    tol = 1.0e-05
    links = []

    def _setlink(self, link):
        """
        Helper method to set the link for a family.

        Raises a ValueError exception if the link is not available.  Note that
        the error message might not be that informative because it tells you
        that the link should be in the base class for the link function.

        See glm.GLM for a list of appropriate links for each family but note 
        that not all of these are currently available.
        """
#TODO: change deviance to use llf, so that scale is used accurately?
# note that I removed scale from deviance and dev_resids, since I'm not
# sure it was used consistently and I don't have a reference for its usage
# as such
# note that Hardin and Hilbe discusses 'deviance adjustment factors'

#TODO: change the links class attribute in the families to hold meaningful
# information instead of a list of links instances such as 
#[<scikits.statsmodels.family.links.Log object at 0x9a4240c>,
# <scikits.statsmodels.family.links.Power object at 0x9a423ec>,
# <scikits.statsmodels.family.links.Power object at 0x9a4236c>]
# for Poisson...
# for now the links class attributes will not be documented
        self._link = link
        if hasattr(self, "links"):
            if link not in self.links:
                raise ValueError, 'Invalid link for family, should be in %s'\
                    % `self.links`

    def _getlink(self):
        """
        Helper method to get the link for a family.
        """
        return self._link

    #link property for each family
    #pointer to link instance
    link = property(_getlink, _setlink)
    
    def __init__(self, link, variance):
        self.link = link()
        self.variance = variance

    def starting_mu(self, y):
        """
        Starting value for mu in the IRLS algorithm.
    
        Parameters
        ----------
        y : array
            The untransformed response variable.

        Returns
        -------
        mu_0 : array
            The first guess on the transformed response variable.
        
        Formulas
        --------
        mu_0 = (endog + mean(endog))/2.

        Notes
        -----
        Only the Binomial family takes a different initial value.
        """
        return (y + y.mean())/2.

    def weights(self, mu):
        """
        Weights for IRLS steps

        Parameters
        ----------
        mu : array-like
            The transformed mean response variable in the exponential family

        Returns
        -------
        w : array
            The weights for the IRLS steps
            
        Formulas
        ---------
        `w` = 1 / (link'(`mu`)**2 * variance(`mu`))
        """
        return 1. / (self.link.deriv(mu)**2 * self.variance(mu))

    def deviance(self, Y, mu, scale=1.):
        """
        Deviance of (Y,mu) pair.
        
        Deviance is usually defined as twice the loglikelihood ratio.

        Parameters
        ----------
        Y : array-like
            The endogenous response variable
        mu : array-like
            The inverse of the link function at the linear predicted values.
        scale : float, optional
            An optional scale argument.

        Returns
        -------
        DEV : array
            The value of deviance function defined below.

        Formulas
        ---------
        DEV = (sum_i(2*loglike(Y_i,Y_i) - 2*loglike(Y_i,mu_i)) / scale

        Notes
        -----
        The deviance functions are analytically defined for each family.
        """
        raise NotImplementedError
#        return np.power(self.devresid(Y, mu), 2).sum() / scale

    def devresid(self, Y, mu):
        """
        The deviance residuals

        Parameters
        ----------
        Y : array
            The endogenous response variable
        mu : array
            The inverse of the link function at the linear predicted values.

        Returns
        -------
        Deviance residuals.  
        
        Notes
        -----
        The deviance residuals are defined for each family.
        """
        raise NotImplementedError
#        return (Y - mu) * np.sqrt(self.weights(mu))

    def fitted(self, eta):
        """
        Fitted values based on linear predictors eta.

        Parameters
        -----------
        eta : array
            Values of the linear predictor of the model.  
            dot(X,beta) in a classical linear model.

        Returns
        --------
        mu : array
            The mean response variables given by the inverse of the link
            function.
        """
        return self.link.inverse(eta)

    def predict(self, mu):
        """
        Linear predictors based on given mu values.

        Parameters
        ----------
        mu : array
            The mean response variables

        Returns
        -------
        eta : array
            Linear predictors based on the mean response variables.  The value
            of the link function at the given mu.
        """
        return self.link(mu)

    def loglike(self, Y, mu, scale=1.):
        """
        The loglikelihood function.

        Parameters
        ----------
        `Y` : array
            Usually the endogenous response variable.
        `mu` : array
            Usually but not always the fitted mean response variable.

        Returns
        -------
        llf : float
            The value of the loglikelihood evaluated at (Y,mu).
        Notes
        -----
        This is defined for each family.  Y and mu are not restricted to
        `Y` and `mu` respectively.  For instance, the deviance function calls
        both loglike(Y,Y) and loglike(Y,mu) to get the likelihood ratio.
        """
        raise NotImplementedError

    def resid_anscombe(self, Y, mu):
        """
        The Anscome residuals.  
        
        See also
        --------
        statsmodesl.family.family.Family docstring and the `resid_anscombe` for
        the individual families for more information.
        """
        raise NotImplementedError

class Poisson(Family):
    """
    Poisson exponential family.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Poisson family is the log link.
        Available links are log, identity, and sqrt.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    link : a link instance
        The link function of the Poisson instance.
    variance : varfuncs instance
        `variance` is an instance of statsmodels.family.varfuncs.mu
    valid (class attribute) : list
        A list contained the domain for the Poisson family.

    Methods
    -------
    devresid
        Returns the deviance residuals for the Poisson family.
    deviance
        Returns the value of the deviance function for the Poisson family.
    loglike
        Returns the value of the loglikelihood function for the Poisson family.
    resid_anscombe
        Returns the Anscombe residuals for the Poisson family.

    See also
    --------
    statsmodels.family.family.Family
    """

    links = [L.log, L.identity, L.sqrt]
    variance = V.mu
    valid = [0, np.inf]

    def __init__(self, link=L.log):
        self.variance = Poisson.variance
        self.link = link

    def devresid(self, Y, mu):
        """Gaussian deviance residual

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------

        Poisson deviance residuals

        Parameters
        -----------
Gaussian deviance residual

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------
        resid_dev = sign(Y-mu)*sqrt(2*Y*log(Y/mu)-2*(Y-mu))
        """
        return np.sign(Y-mu) * np.sqrt(2*Y*np.log(Y/mu)-2*(Y-mu))
    
    def deviance(self, Y, mu):
        '''
        Poisson deviance function
        
        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        deviance : float
            The deviance function at (Y,mu) as defined below.
        
        Formulas
        --------
        If a constant term is included it is defined as 

        `deviance` = 2*sum_i(Y*log(Y/mu))
        '''
        return 2*np.sum(Y*np.log(Y/mu))

    def loglike(self, Y, mu, scale=1.):
        """
        Loglikelihood function for Poisson exponential family distribution.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at (Y,mu,scale) 
            as defined below.

        Formulas
        --------
        llf = scale * sum(-mu + Y*log(mu) - gammaln(Y+1))
        where gammaln is the log gamma function
        """
        return scale * np.sum(-mu + Y*np.log(mu)-special.gammaln(Y+1))

    def resid_anscombe(self, Y, mu):
        """
        Anscombe residuals for the Poisson exponential family distribution

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscome residuals for the Poisson family defined below

        Formulas
        --------
        `resid_anscombe` = (3/2.)*(`Y`**(2/3.) - `mu`**(2/3.))/`mu`**(1/6.)
        """
        return (3/2.)*(Y**(2/3.)-mu**(2/3.))/mu**(1/6.)

class Gaussian(Family):

    """
    Gaussian exponential family distribution.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Gaussian family is the identity link.
        Available links are log, identity, and inverse.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    link : a link instance
        The link function of the Gaussian instance
    variance : varfunc instance
        `variance` is an instance of statsmodels.family.varfuncs.constant
    
    Methods
    -------
    devresid
        Returns the deviance residuals for the Gaussian family.
    deviance
        Returns the value of the deviance function for the Gaussian family.
    loglike
        Returns the value of the loglikelihood function for the Gaussian family.
    resid_anscombe
        Returns the Anscombe residuals for the Gaussian family.

    See also
    --------
    statsmodels.family.family.Family
    """

    links = [L.log, L.identity, L.inverse]
    variance = V.constant

    def __init__(self, link=L.identity):
        self.variance = Gaussian.variance
        self.link = link

    def devresid(self, Y, mu):
        """
        Gaussian deviance residuals

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------
        `resid_dev` = (`Y` - `mu`)/sqrt(variance(`mu`))
        """

        return (Y - mu) / np.sqrt(self.variance(mu))
    
    def deviance(self, Y, mu):
        """
        Gaussian deviance function
        
        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        deviance : float
            The deviance function at (Y,mu) as defined below.
        
        Formulas
        --------
        `deviance` = sum((Y-mu)**2)
        """
        return np.sum((Y-mu)**2)

    def loglike(self, Y, mu, scale=1.):
        """
        Loglikelihood function for Gaussian exponential family distribution.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            Scales the loglikelihood function. The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at (Y,mu,scale) 
            as defined below.

        Formulas
        --------
        If the link is the identity link function then the 
        loglikelihood function is the same as the classical OLS model.
        llf = -(nobs/2)*(log(SSR) + (1 + log(2*pi/nobs)))
        where SSR = sum((Y-link^(-1)(mu))**2)

        If the links is not the identity link then the loglikelihood
        function is defined as 
        llf = sum((`Y`*`mu`-`mu`**2/2)/`scale` - `Y`**2/(2*`scale`) - \
            (1/2.)*log(2*pi*`scale`))
        """
        if isinstance(self.link, L.Power) and self.link.power == 1:
        # This is just the loglikelihood for classical OLS
            nobs2 = Y.shape[0]/2.
            SSR = ss(Y-self.fitted(mu))
            llf = -np.log(SSR) * nobs2
            llf -= (1+np.log(np.pi/nobs2))*nobs2
            return llf
        else:
        # Return the loglikelihood for Gaussian GLM
            return np.sum((Y*mu-mu**2/2)/scale-Y**2/(2*scale)-\
                    .5*np.log(2*np.pi*scale))

    def resid_anscombe(self, Y, mu):
        """
        The Anscombe residuals for the Gaussian exponential family distribution

        Parameters
        ----------
        Y : array
            Endogenous response variable
        mu : array
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals for the Gaussian family defined below

        Formulas
        --------
        `resid_anscombe` = `Y` - `mu`
        """
        return Y-mu

class Gamma(Family):

    """
    Gamma exponential family distribution.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Gamma family is the inverse link.
        Available links are log, identity, and inverse.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    link : a link instance
        The link function of the Gamma instance
    variance : varfunc instance
        `variance` is an instance of statsmodels.family.varfuncs.mu_squared
    
    Methods
    -------
    devresid
        Returns the deviance residuals for the Gamma family.
    deviance
        Returns the value of the deviance function for the Gamma family.
    loglike
        Returns the value of the loglikelihood function for the Gamma family.
    resid_anscombe
        Returns the Anscombe residuals for the Gamma family.

    See also
    --------
    statsmodels.family.family.Family
    """

    links = [L.log, L.identity, L.inverse]
    variance = V.mu_squared

    def __init__(self, link=L.inverse):
        self.variance = Gamma.variance
        self.link = link

#TODO: note the note
    def _clean(self, x):
        """
        Helper function to trim the data so that is in (0,inf)

        Notes
        -----
        The need for this function was discovered through usage and its
        possible that other families might need a check for validity of the
        domain.
        """
        return np.clip(x, 1.0e-10, np.inf)

    def deviance(self, Y, mu):
        """
        Gamma deviance function

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        deviance : float
            Deviance function as defined below

        Formulas
        --------
        `deviance` = 2*sum((Y - mu)/mu - log(Y/mu))
        """
        Y_mu = self._clean(Y/mu)
        return 2 * np.sum((Y - mu)/mu - np.log(Y_mu))

    def devresid(self, Y, mu):
        """
        Gamma deviance residuals

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------
        `resid_dev` = sign(Y - mu) * sqrt(-2*(-(Y-mu)/mu + log(Y/mu)))
        """
        Y_mu = self._clean(Y/mu)
        return np.sign(Y-mu) * np.sqrt(-2*(-(Y-mu)/mu + np.log(Y_mu)))

    def loglike(self, Y, mu, scale=1.):
        """
        Loglikelihood function for Gamma exponential family distribution.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at (Y,mu,scale) 
            as defined below.

        Formulas
        --------
        llf = -1/scale * sum(Y/mu + log(mu) + (scale-1)*log(Y) + log(scale) +\
            scale*gammaln(1/scale))
        where gammaln is the log gamma function.
        """
        return - 1/scale * np.sum(Y/mu+np.log(mu)+(scale-1)*np.log(Y)\
                +np.log(scale)+scale*special.gammaln(1/scale))
# in Stata scale is set to equal 1 for reporting llf
# in R it's the dispersion, though there is a loss of precision vs. our
# results due to an assumed difference in implementation

    def resid_anscombe(self, Y, mu):
        """
        The Anscombe residuals for Gamma exponential family distribution

        Parameters
        ----------
        Y : array
            Endogenous response variable
        mu : array
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals for the Gamma family defined below

        Formulas
        --------
        resid_anscombe = 3*(Y**(1/3.)-mu**(1/3.))/mu**(1/3.)
        """
        return 3*(Y**(1/3.)-mu**(1/3.))/mu**(1/3.)

class Binomial(Family):

    """
    Binomial exponential family distribution.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Binomial family is the logit link.
        Available links are logit, probit, cauchy, log, and cloglog.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    link : a link instance
        The link function of the Binomial instance
    variance : varfunc instance
        `variance` is an instance of statsmodels.family.varfuncs.binary
    
    Methods
    -------
    devresid
        Returns the deviance residuals for the Binomial family.
    deviance
        Returns the value of the deviance function for the Binomial family.
    initialize
        This function is specific to the Binomial family.  It initializes
        the data given by endog.  See Binomial.initialize for more information.
    loglike
        Returns the value of the loglikelihood function for the Binomial 
        family.
    resid_anscombe
        Returns the Anscombe residuals for the Binomial family.

    See also
    --------
    statsmodels.family.family.Family

    Notes
    -----
    endog for Binomial can be specified in one of three ways.
    """

    links = [L.logit, L.probit, L.cauchy, L.log, L.cloglog]
    variance = V.binary # this is not used below in an effort to include n

    def __init__(self, link=L.logit):  #, n=1.):
#TODO: it *should* work for a constant n>1 actually, if data_weights is
# equal to n
        self.n = 1 # overwritten by initialize if needed but
                   # always used to initialize variance
                   # since Y is assumed/forced to be (0,1)
        self.variance = V.Binomial(n=self.n)
        self.link = link

    def starting_mu(self, y):
        """
        The starting values for the IRLS algorithm for the Binomial family.

        A good choice for the binomial family is

        starting_mu = (y + .5)/2
        """
        return (y + .5)/2

    def initialize(self, Y):
        '''
        Initialize the response variable.

        Parameters
        ----------
        Y : array
            Endogenous response variable

        Returns
        --------
        If `Y` is binary, returns `Y`

        If `Y` is a 2d array, then the input is assumed to be in the format
        (successes, failures) and 
        successes/(success + failures) is returned.  And n is set to
        successes + failures.
        '''
        if (Y.ndim > 1 and Y.shape[1] > 1):
            y = Y[:,0]
            self.n = Y.sum(1) # overwrite self.n for deviance below
            return y/self.n
        else:
            return Y

    def deviance(self, Y, mu):
        '''
        Deviance function for either Bernoulli or Binomial data.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable (already transformed to a probability 
            if appropriate).
        mu : array
            Fitted mean response variable

        Returns
        --------
        deviance : float
            The deviance function as defined below

        Formulas
        --------
        If the endogenous variable is binary:

        `deviance` = -2*sum(I_one * log(mu) + (I_zero)*log(1-mu))

        where I_one is an indicator function that evalueates to 1 if Y_i == 1.
        and I_zero is an indicator function that evaluates to 1 if Y_i == 0.

        If the model is ninomial:

        `deviance` = 2*sum(log(Y/mu) + (n-Y)*log((n-Y)/(n-mu)))
        where Y and n are as defined in Binomial.initialize.
        '''
        if np.shape(self.n) == () and self.n == 1:
            one = np.equal(Y,1)
            return -2 * np.sum(one * np.log(mu) + (1-one) * np.log(1-mu))

        else:
            return 2*np.sum(self.n*(Y*np.log(Y/mu)+(1-Y)*np.log((1-Y)/(1-mu))))

    def devresid(self, Y, mu):
        """
        Binomial deviance residuals

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------
        If `Y` is binary:

        resid_dev = sign(Y-mu)*sqrt(-2*log(I_one*mu + I_zero*(1-mu)))
        
        where I_one is an indicator function that evaluates as 1 if Y == 1
        and I_zero is an indicator function that evaluates as 1 if Y == 0.

        If `Y` is binomial:

        resid_dev = sign(Y-mu)*sqrt(2*n*(Y*log(Y/mu)+(1-Y)*log((1-Y)/(1-mu))))

        where Y and n are as defined in Binomial.initialize.
        """

        mu = self.link._clean(mu)
        if np.shape(self.n) == () and self.n == 1:
            one = np.equal(Y,1)
            return np.sign(Y-mu)*np.sqrt(-2*np.log(one*mu+(1-one)*(1-mu)))
        else:
            return np.sign(Y-mu) * np.sqrt(2*self.n*(Y*np.log(Y/mu)+(1-Y)*\
                        np.log((1-Y)/(1-mu))))

    def loglike(self, Y, mu, scale=1.):
        """
        Loglikelihood function for Binomial exponential family distribution.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at (Y,mu,scale) 
            as defined below.

        Formulas
        --------
        If `Y` is binary:
        `llf` = scale*sum(Y*log(mu/(1-mu))+log(1-mu))

        If `Y` is binomial:
        `llf` = scale*sum(gammaln(n+1) - gammaln(y+1) - gammaln(n-y+1) +\
                y*log(mu/(1-mu)) + n*log(1-mu)

        where gammaln is the log gamma function and y = Y*n with Y and n
        as defined in Binomial initialize.  This simply makes y the original
        number of successes.
        """

        if np.shape(self.n) == () and self.n == 1:
            return scale*np.sum(Y*np.log(mu/(1-mu))+np.log(1-mu))
        else:
            y=Y*self.n  #convert back to successes
            return scale * np.sum(special.gammaln(self.n+1)-\
                special.gammaln(y+1)-special.gammaln(self.n-y+1)\
                +y*np.log(mu/(1-mu))+self.n*np.log(1-mu))

    def resid_anscombe(self, Y, mu):
        '''
        The Anscombe residuals 

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
            
        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals as defined below.

        Formulas
        ---------
        sqrt(n)*(cox_snell(Y)-cox_snell(mu))/(mu**(1/6.)*(1-mu)**(1/6.))

        where cox_snell is defined as 
        cox_snell(x) = betainc(2/3., 2/3., x)*betainc(2/3.,2/3.)
        where betainc is the incomplete beta function

        Notes
        -----
        The name 'cox_snell' is highly idiosyncratic and is simply used for
        convenience following the approach suggested in Cox and Snell (1968).
        Further note that 
        cox_snell(x) = x**(2/3.)/(2/3.)*hyp2f1(2/3.,1/3.,5/3.,x)
        where hyp2f1 is the hypergeometric 2f1 function.  The Anscombe
        residuals are sometimes defined in the literature using the
        hyp2f1 formulation.  Both betainc and hyp2f1 can be found in scipy.

        References
        ----------
        Anscombe, FJ. (1953) "Contribution to the discussion of H. Hotelling's
            paper." Journal of the Royal Statistical Society B. 15, 229-30.
    
        Cox, DR and Snell, EJ. (1968) "A General Definition of Residuals."  
            Journal of the Royal Statistical Society B. 30, 248-75.

        '''
        cox_snell = lambda x: special.betainc(2/3., 2/3., x)\
                            *special.beta(2/3.,2/3.)
        return np.sqrt(self.n)*(cox_snell(Y)-cox_snell(mu))/\
                        (mu**(1/6.)*(1-mu)**(1/6.))

class InverseGaussian(Family):

    """
    InverseGaussian exponential family.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the inverse Gaussian family is the 
        inverse squared link.
        Available links are inverse_squared, inverse, log, and identity.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    link : a link instance
        The link function of the inverse Gaussian instance
    variance : varfunc instance
        `variance` is an instance of statsmodels.family.varfuncs.mu_cubed
    
    Methods
    -------
    devresid
        Returns the deviance residuals for the inverse Gaussian family.
    deviance
        Returns the value of the deviance function for the inverse 
        Gaussian family.
    loglike
        Returns the value of the loglikelihood function for the
        inverse Gaussian family.
    resid_anscombe
        Returns the Anscombe residuals for the inverse Gaussian family.

    See also
    --------
    statsmodels.family.family.Family

    Notes
    -----
    The inverse Guassian distribution is sometimes referred to in the
    literature as the wald distribution.
    """

    links = [L.inverse_squared, L.inverse, L.identity, L.log]
    variance = V.mu_cubed

    def __init__(self, link=L.inverse_squared):
        self.variance = InverseGaussian.variance
        self.link = link
    
    def devresid(self, Y, mu):
        """
        Returns the deviance residuals for the inverse Gaussian family.

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        Formulas
        --------
        `dev_resid` = sign(Y-mu)*sqrt((Y-mu)**2/(Y*mu**2))
        """
        return np.sign(Y-mu) * np.sqrt((Y-mu)**2/(Y*mu**2))

    def deviance(self, Y, mu):
        """
        Inverse Gaussian deviance function

        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        deviance : float
            Deviance function as defined below

        Formulas
        --------
        `deviance` = sum((Y=mu)**2/(Y*mu**2))
        """
        return np.sum((Y-mu)**2/(Y*mu**2))

    def loglike(self, Y, mu, scale=1.):
        """
        Loglikelihood function for inverse Gaussian distribution.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at (Y,mu,scale) 
            as defined below.

        Formulas
        --------
        `llf` = -(1/2.)*sum((Y-mu)**2/(Y*mu**2*scale) + log(scale*Y**3)\
                 + log(2*pi))
        """
        return -.5 * np.sum((Y-mu)**2/(Y*mu**2*scale)\
                + np.log(scale*Y**3) + np.log(2*np.pi))

    def resid_anscombe(self, Y, mu):
        """
        The Anscombe residuals for the inverse Gaussian distribution

        Parameters
        ----------
        Y : array
            Endogenous response variable
        mu : array
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals for the inverse Gaussian distribution  as 
            defined below

        Formulas
        --------
        `resid_anscombe` =  log(Y/mu)/sqrt(mu)
        """
        return np.log(Y/mu)/np.sqrt(mu)

class NegativeBinomial(Family):
    """
    Negative Binomial exponential family.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the negative binomial family is the log link.
        Available links are log, cloglog, identity, nbinom and power.
        See statsmodels.family.links for more information.
    alpha : float, optional
        The ancillary parameter for the negative binomial distribution.
        For now `alpha` is assumed to be nonstochastic.  The default value
        is 1.  Permissible values are usually assumed to be between .01 and 2.
        

    Attributes
    ----------
    link : a link instance
        The link function of the negative binomial instance
    variance : varfunc instance
        `variance` is an instance of statsmodels.family.varfuncs.nbinom
    
    Methods
    -------
    devresid
        Returns the deviance residuals for the megative binomial family.
    deviance
        Returns the value of the deviance function for the negative binomial
        family.
    loglike
        Returns the value of the loglikelihood function for the negative 
        binomial family.
    resid_anscombe
        Returns the Anscombe residuals for the negative binomial family.

    See also
    --------
    statsmodels.family.family.Family

    Notes
    -----
    Support for Power link functions is not yet supported.
    """
    links = [L.log, L.cloglog, L.identity, L.nbinom, L.Power]
#TODO: add the ability to use the power links with an if test
# similar to below
    variance = V.nbinom

    def __init__(self, link=L.log, alpha=1.):
        self.alpha = alpha
        self.variance = V.NegativeBinomial(alpha=self.alpha)
        if isinstance(link, L.NegativeBinomial):
            self.link = link(alpha=self.alpha)
        else:
            self.link = link

    def deviance(self, Y, mu):
        """
        Parameters
        -----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        deviance : float
            Deviance function as defined below

        Formulas
        --------
        `deviance` = sum(piecewise)

        where piecewise is defined as 
        if Y_i == 0:
            piecewise_i = 2*log(1+alpha*mu)/alpha
        if Y_i == 0:
            piecewise_i = 2*Y*log(Y/mu)-2/alpha*(1+alpha*Y)*\
                    log((1+alpha*Y)/(1+alpha*mu))
        """
        iszero = np.equal(Y,0)
        notzero = 1 - iszero
        tmp = np.zeros(len(Y))
        tmp = iszero*2*np.log(1+self.alpha*mu)/self.alpha
        tmp += notzero*(2*Y*np.log(Y/mu)-2/self.alpha*(1+self.alpha*Y)*\
                np.log((1+self.alpha*Y)/(1+self.alpha*mu)))
        return np.sum(tmp)

    def devresid(self, Y, mu):
        '''
        Negative Binomial Deviance Residual

        Parameters
        ----------
        Y : array-like
            `Y` is the response variable
        mu : array-like
            `mu` is the fitted value of the model

        Returns
        --------
        resid_dev : array
            The array of deviance residuals

        Formula
        --------
        `resid_dev` = sign(Y-mu) * sqrt(piecewise)

        where piecewise is defined as 
        if Y_i == 0:
            piecewise_i = 2*log(1+alpha*mu)/alpha
        if Y_i == 0:
            piecewise_i = 2*Y*log(Y/mu)-2/alpha*(1+alpha*Y)*\
                    log((1+alpha*Y)/(1+alpha*mu))
        '''
        iszero = np.equal(Y,0)
        notzero = 1 - iszero
        tmp=np.zeros(len(Y))
        tmp = iszero*2*np.log(1+self.alpha*mu)/self.alpha
        tmp += notzero*(2*Y*np.log(Y/mu)-2/self.alpha*(1+self.alpha*Y)*\
                np.log((1+self.alpha*Y)/(1+self.alpha*mu)))
        return np.sign(Y-mu)*np.sqrt(tmp)

    def loglike(self, Y, fittedvalues=None):
        """
        The loglikelihood function for the negative binomial family.

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        fittedvalues : array-like
            The linear fitted values of the model.  This is dot(exog,params).

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at (Y,mu,scale) 
            as defined below.

        Formulas
        --------
        sum(Y*log(alpha*exp(fittedvalues)/(1+alpha*exp(fittedvalues))) -\
                log(1+alpha*exp(fittedvalues))/alpha + constant)

        where constant is defined as
        constant = gammaln(Y + 1/alpha) - gammaln(Y + 1) - gammaln(1/alpha)
        """
        # don't need to specify mu
        if fittedvalues is None:
            raise AttributeError, '''The loglikelihood for the negative binomial requires that the fitted values be provided via the `fittedvalues` keyword argument.'''
        constant = special.gammaln(Y + 1/self.alpha) - special.gammaln(Y+1)\
                    -special.gammaln(1/self.alpha)
        return np.sum(Y*np.log(self.alpha*np.exp(fittedvalues)/\
            (1 + self.alpha*np.exp(fittedvalues))) - \
            np.log(1+self.alpha*np.exp(fittedvalues))/self.alpha\
            + constant)

    def resid_anscombe(self, Y, mu):
        """
        The Anscombe residuals for the negative binomial family 

        Parameters
        ----------
        Y : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
            
        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals as defined below.

        Formulas
        ---------
        `resid_anscombe` = (hyp2f1(-alpha*Y)-hyp2f1(-alpha*mu)+\
                1.5*(Y**(2/3.)-mu**(2/3.)))/(mu+alpha*mu**2)**(1/6.)

        where hyp2f1 is the hypergeometric 2f1 function paramterized as 
        hyp2f1(x) = hyp2f1(2/3.,1/3.,5/3.,x)
        """

        hyp2f1 = lambda x : special.hyp2f1(2/3.,1/3.,5/3.,x)
        return (hyp2f1(-self.alpha*Y)-hyp2f1(-self.alpha*mu)+1.5*(Y**(2/3.)-\
                mu**(2/3.)))/(mu+self.alpha*mu**2)**(1/6.)
