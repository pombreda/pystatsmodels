"""
Statistical tools for time series analysis
"""

import numpy as np
from scipy import stats, signal
import scikits.statsmodels as sm
from scikits.statsmodels.sandbox.tsa.varma_tools import lagmat
#from scikits.statsmodels.sandbox.rls import RLS

#taken from econpy until we have large set of critical values
adf_cv1 = '''
One-sided test of H0: Unit root vs. H1: Stationary
Approximate asymptotic critical values (t-ratio):
------------------------------------------------------------
  1%      5%      10%      Model
------------------------------------------------------------
-2.56   -1.94   -1.62     Simple ADF (no constant or trend)
-3.43   -2.86   -2.57     ADF with constant (no trend)
-3.96   -3.41   -3.13     ADF with constant & trend
------------------------------------------------------------'''      

def unitroot_adf(x, maxlag=None, trendorder=0, autolag='AIC', store=False):
    '''Augmented Dickey-Fuller unit root test
    
    Parameters
    ----------
    x : array_like, 1d
        data series
    maxlag : int
        maximum lag which is included in test, default 12*(nobs/100)^{1/4}
    trendorder : int 
        constant and trend order to include in regression
        * -1: no constant no trend
        *  0: constant only
        * p>0 : trend polynomial of order p
    autolag : {'AIC', 'BIC', None}
        * if None, then maxlag lags are used
        * if 'AIC' or 'BIC', then the number of lags is chosen to minimize the
          corresponding information criterium
        * TODO: t-statistic based choice of maxlag
    store : {False, True}
        If true, then a result instance is returned additionally to
        the adf statistic
        
    Returns
    -------
    adf : float
        test statistic
    pvalue : NOT YET IMPLEMENTED
    resstore : (optional) instance of ResultStore
        an instance of a dummy class with results attached as attributes
    
    Notes
    -----
    The pvalues are (will be) interpolated from the table of critical
    values. NOT YET DONE
    
    still requires pvalues and maybe some cleanup
    
    ''Verification''
    
    Looks correctly sized in Monte Carlo studies.
    Differs from R tseries results in second decimal, based on a few examples
    
    Examples
    --------
    see example script
    
    References
    ----------
    Greene
    Wikipedia
    
    Critical Values (Canonical reference)
    Fuller, W.A. 1996. `Introduction to Statistical Time Series.` 2nd ed.
        New York: Wiley.

    P-Values (regression surface approximation)
    MacKinnon, J.G. 1994.  "Approximate asymptotic distribution functions for 
        unit-root and cointegration tests.  `Journal of Business and Economic
        Statistics` 12, 167-76.

    '''
    x = np.asarray(x)
    nobs = x.shape[0]
    if maxlag is None:
        #from Greene referencing Schwert 1989
        maxlag = 12. * np.power(nobs/100., 1/4.)


    xdiff = np.diff(x)
    #
    xdall = lagmat(xdiff[:,None], maxlag, trim='both')
    nobs = xdall.shape[0]
    trend = np.vander(np.arange(nobs), trendorder+1)
    xdall[:,0] = x[-nobs-1:-1] # replace 0 xdiff with level of x
    #xdshort = xdiff[-nobs:]
    xdshort = x[-nobs:]

    if store: resstore = ResultsStore()

    if autolag:
        #search for lag length with highest information criteria
        #Note: I use the same number of observations to have comparable IC
        results = {}
        for mlag in range(1,maxlag):
            results[mlag] = sm.OLS(xdshort, np.column_stack([xdall[:,:mlag],trend])).fit()

        if autolag.lower() == 'aic':                    
            bestic, icbestlag = max((v.aic,k) for k,v in results.iteritems())
        elif autolag.lower() == 'bic':                    
            icbest, icbestlag = max((v.bic,k) for k,v in results.iteritems())
        else:
            raise ValueError("autolag can only be None, 'AIC' or 'BIC'")

        #rerun ols with best ic  
        xdall = lagmat(xdiff[:,None], icbestlag, trim='forward')
        nobs = xdall.shape[0]
        trend = np.vander(np.arange(nobs), trendorder+1)
        xdall[:,0] = x[-nobs-1:-1] # replace 0 xdiff with level of x
        #xdshort = xdiff[-nobs:]
        xdshort = x[-nobs:]
        usedlag = icbestlag
    else:
        usedlag = maxlag
        
    resols = sm.OLS(xdshort, np.column_stack([xdall[:,:usedlag],trend])).fit()
    adfstat = resols.t(0)
    adfstat = (resols.params[0]-1.0)/resols.bse[0]
    if store:
        resstore.resols = resols
        resstore.usedlag = usedlag
        return adfstat, resstore
    else:
        return adfstat


def dfuller(X, nlags=1, noconstant=False, trend=False):
    """
    Augmented Dickey-Fuller test for a time series X.

    Parameters
    ----------
    X - array-like
        The time series that might contain a unit root.
    nlags - int
        nlags should be >= 0.
        TODO: Allow string 'AIC' and 'BIC'
    noconstant - bool
        Include a constant or not.  Default is false, so that a constant
        term is estimated.
    trend : bool
        Include a linear time trend or not.  Default is false for no
        time trend.

    Notes
    -----
    The ADF test statistic is not returned.  Refer to a ADF table for
    inference.  Is nlags = 0, dfuller returns the classic Dickey-Fuller
    statistic.

    """
    if nlags < 0:
        raise ValueError, "nlags should be >= 0"
    X = np.asarray(X).squeeze()
    nobs = float(len(X))
    xdiff = np.diff(X)
    xlag1 = X[:-1]
    xdiffp = lagmat(xdiff,nlags,trim='both')[:,1:]
    t = np.arange(1,nobs-nlags)
    RHS = np.column_stack((xlag1[nlags:],xdiffp))
    if trend:
        t = np.arange(1,nobs-nlags)
        RHS = np.column_stack((t,RHS))
    if not noconstant:
        RHS = sm.add_constant(RHS,prepend=True)
    results = sm.OLS(xdiff[nlags:],RHS).fit()
    return results.t()[-(nlags+1)]

def acorr(X,nlags=40, level=95):
    """
    Autocorrelation function

    Parameters
    ----------
    X : array-like
        The time series
    nlags : int
        The number of lags to estimate the autocorrelation function for.
        Default is 40.
    level : int
        The level of the confidence intervals.  Defaults is 95 % confidence
        intervals.

    Returns
    -------
    acf : array
        The values of the autocorrelation function
    conf_int(acf) : array
        The confidence interval of acf at level
    """
    X = np.asarray(X).squeeze()
    nobs = float(len(X))
    if nlags > nobs:
        raise ValueError, "X does not have %s observations" % nlags
    Xbar = np.mean(X)
    acf = np.zeros(nlags)
    acov0 = np.var(X)
    for i in range(1,nlags+1):
        acf[i-1] = np.dot(X[i:] - Xbar,X[:-i] - Xbar)
    acf = 1/nobs*acf/acov0
    varacf = np.ones(nlags)/nobs
    varacf[1:] *= 1 + 2*np.cumsum(acf[1:]**2)
    confint = np.array(zip(acf - stats.norm.ppf(1-(100 - level)/\
            200.)*np.sqrt(varacf), acf+stats.norm.ppf(1-(100-level)/200.)\
            *np.sqrt(varacf)))
    return acf,confint

def pacorr(X,nlags=40, method="ols"):
    """
    Partial autocorrelation function
    """
    X = np.asarray(X).squeeze()
    nobs = float(len(X))
    if nlags > nobs:
        raise ValueError, "X does not have %s observations" % nlags
    pacf = np.zeros(nlags)
    for i in range(1,nlags+1):
        pacf[i-1] = sm.OLS(X[i:],sm.add_constant(lagmat(X, i, 
            trim="both")[:,1:], prepend=True)).fit().params[-1]
    return pacf
        
def pergram(X, kernel='bartlett', log=True):
    """
    Returns the (log) periodogram for the natural frequency of X

    Parameters
    ----------
    X
    M : int
        Should this be hardcoded?
    kernel : str, optional
    Notes
    -----
    The autocovariances are normalized by len(X).
    The frequencies are calculated as 
    If len(X) is odd M = (len(X) - 1)/2 else M = len(X)/2. Either way
        freq[i] = 2*[i+1]/T and len(freq) == M


    Reference
    ----------
    Based on Lutkepohl; Hamilton.

    Notes
    -----
    Doesn't look right yet.
    """
    X = np.asarray(X).squeeze()
    nobs = len(X)
    M = np.floor(nobs/2.)
    acov = np.zeros(M+1)
    acov[0] = np.var(X)
    Xbar = X.mean()
    for i in range(1,int(M+1)):
        acov[i] = np.dot(X[i:] - Xbar,X[:-i] - Xbar)
    acov /= nobs
    #    #TODO: make a list to check window
#    ell = np.r_[1,np.arange(1,M+1)*np.pi/nobs]
    if kernel == "bartlett":
        w = 1 - np.arange(M+1)/M

#    weights = exec('signal.'+window+'(M='str(M)')')
    j = np.arange(1,M+1)
    ell = np.linspace(0,np.pi,M)
    pergr = np.zeros_like(ell)
    for i,L in enumerate(ell):
        pergr[i] = 1/(2*np.pi)*acov[0] + 2 * np.sum(w[1:]*acov[1:]*np.cos(L*j))
    return pergr



if __name__=="__main__":
    data = sm.datasets.macrodata.Load().data
    adf = dfuller(data['realgdp'],4)
    acf,ci = acorr(data['realgdp'])
    pacf = pacorr(data['realgdp'])

