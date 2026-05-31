
# Forecasting: Principles and Practice(3rd ed)


## 9.6Estimation and order selection


### Maximum likelihood estimation


Once the model order has been identified (i.e., the values of\(p\),\(d\)and\(q\)), we need to estimate the parameters\(c\),\(\phi_1,\dots,\phi_p\),\(\theta_1,\dots,\theta_q\). Whenfableestimates the ARIMA model, it usesmaximum likelihood estimation(MLE). This technique finds the values of the parameters which maximise the probability of obtaining the data that we have observed. For ARIMA models, MLE is similar to theleast squaresestimates that would be obtained by minimising\[
  \sum_{t=1}^T\varepsilon_t^2.
\](For the regression models considered in Chapter7, MLE gives exactly the same parameter estimates as least squares estimation.) Note that ARIMA models are much more complicated to estimate than regression models, and different software will give slightly different answers as they use different methods of estimation, and different optimisation algorithms.


In practice, thefablepackage will report the value of thelog likelihoodof the data; that is, the logarithm of the probability of the observed data coming from the estimated model. For given values of\(p\),\(d\)and\(q\),ARIMA()will try to maximise the log likelihood when finding parameter estimates.


### Information Criteria


Akaike’s Information Criterion (AIC), which was useful in selecting predictors for regression (see Section7.5), is also useful for determining the order of an ARIMA model. It can be written as\[
  \text{AIC} = -2 \log(L) + 2(p+q+k+1),
\]where\(L\)is the likelihood of the data,\(k=1\)if\(c\ne0\)and\(k=0\)if\(c=0\). Note that the last term in parentheses is the number of parameters in the model (including\(\sigma^2\), the variance of the residuals).


For ARIMA models, the corrected AIC can be written as\[
  \text{AICc} = \text{AIC} + \frac{2(p+q+k+1)(p+q+k+2)}{T-p-q-k-2},
\]and the Bayesian Information Criterion can be written as\[
  \text{BIC} = \text{AIC} + [\log(T)-2](p+q+k+1).
\]Good models are obtained by minimising the AIC, AICc or BIC. Our preference is to use the AICc.


It is important to note that these information criteria tend not to be good guides to selecting the appropriate order of differencing (\(d\)) of a model, but only for selecting the values of\(p\)and\(q\). This is because the differencing changes the data on which the likelihood is computed, making the AIC values between models with different orders of differencing not comparable. So we need to use some other approach to choose\(d\), and then we can use the AICc to select\(p\)and\(q\).
