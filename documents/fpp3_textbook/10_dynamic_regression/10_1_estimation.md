
# Forecasting: Principles and Practice(3rd ed)


## 10.1Estimation


When we estimate the parameters from the model, we need to minimise the sum of squared\(\varepsilon_t\)values. If we minimise the sum of squared\(\eta_t\)values instead (which is what would happen if we estimated the regression model ignoring the autocorrelations in the errors), then several problems arise.

- The estimated coefficients\(\hat{\beta}_0,\dots,\hat{\beta}_k\)are no longer the best estimates, as some information has been ignored in the calculation;
- Any statistical tests associated with the model (e.g., t-tests on the coefficients) will be incorrect.
- The AICc values of the fitted models are no longer a good guide as to which is the best model for forecasting.
- In most cases, the\(p\)-values associated with the coefficients will be too small, and so some predictor variables will appear to be important when they are not. This is known as “spurious regression”.

Minimising the sum of squared\(\varepsilon_t\)values avoids these problems. Alternatively, maximum likelihood estimation can be used; this will give similar estimates of the coefficients.


An important consideration when estimating a regression with ARMA errors is that all of the variables in the model must first be stationary. Thus, we first have to check that\(y_t\)and all of the predictors\((x_{1,t},\dots,x_{k,t})\)appear to be stationary. If we estimate the model when any of these are non-stationary, the estimated coefficients will not be consistent estimates (and therefore may not be meaningful). One exception to this is the case where non-stationary variables are co-integrated. If there exists a linear combination of the non-stationary\(y_t\)and the predictors that is stationary, then the estimated coefficients will be consistent.21


We therefore first difference the non-stationary variables in the model. It is often desirable to maintain the form of the relationship between\(y_t\)and the predictors, and consequently it is common to difference all of the variables if any of them need differencing. The resulting model is then called a “model in differences”, as distinct from a “model in levels”, which is what is obtained when the original data are used without differencing.


If all of the variables in the model are stationary, then we only need to consider an ARMA process for the errors. It is easy to see that a regression model with ARIMA errors is equivalent to a regression model in differences with ARMA errors. For example, if the above regression model with ARIMA(1,1,1) errors is differenced we obtain the model\[\begin{align*}
  y'_t &= \beta_1 x'_{1,t} + \dots + \beta_k x'_{k,t} + \eta'_t,\\
       & (1-\phi_1B)\eta'_t = (1+\theta_1B)\varepsilon_t,
\end{align*}\]where\(y'_t=y_t-y_{t-1}\),\(x'_{t,i}=x_{t,i}-x_{t-1,i}\)and\(\eta'_t=\eta_t-\eta_{t-1}\), which is a regression model in differences with ARMA errors.


### Bibliography

- Forecasting with cointegrated models is discussed byHarris & Sollis (2003).↩︎

Forecasting with cointegrated models is discussed byHarris & Sollis (2003).↩︎
