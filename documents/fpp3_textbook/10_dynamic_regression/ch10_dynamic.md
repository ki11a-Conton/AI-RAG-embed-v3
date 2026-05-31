
# Forecasting: Principles and Practice(3rd ed)


# Chapter 10Dynamic regression models


The time series models in the previous two chapters allow for the inclusion of information from past observations of a series, but not for the inclusion of other information that may also be relevant. For example, the effects of holidays, competitor activity, changes in the law, the wider economy, or other external variables, may explain some of the historical variation and may lead to more accurate forecasts. On the other hand, the regression models in Chapter7allow for the inclusion of a lot of relevant information from predictor variables, but do not allow for the subtle time series dynamics that can be handled with ARIMA models. In this chapter, we consider how to extend ARIMA models in order to allow other information to be included in the models.


In Chapter7we considered regression models of the form\[
  y_t = \beta_0 + \beta_1 x_{1,t} + \dots + \beta_k x_{k,t} + \varepsilon_t,
\]where\(y_t\)is a linear function of the\(k\)predictor variables (\(x_{1,t},\dots,x_{k,t}\)), and\(\varepsilon_t\)is usually assumed to be an uncorrelated error term (i.e., it is white noise). We considered tests such as the Ljung-Box test for assessing whether the resulting residuals were significantly correlated.


In this chapter, we will allow the errors from a regression to contain autocorrelation. To emphasise this change in perspective, we will replace\(\varepsilon_t\)with\(\eta_t\)in the equation. The error series\(\eta_t\)is assumed to follow an ARIMA model. For example, if\(\eta_t\)follows an ARIMA(1,1,1) model, we can write\[\begin{align*}
  y_t &= \beta_0 + \beta_1 x_{1,t} + \dots + \beta_k x_{k,t} + \eta_t,\\
      & (1-\phi_1B)(1-B)\eta_t = (1+\theta_1B)\varepsilon_t,
\end{align*}\]where\(\varepsilon_t\)is a white noise series.


Notice that the model has two error terms here — the error from the regression model, which we denote by\(\eta_t\), and the error from the ARIMA model, which we denote by\(\varepsilon_t\). Only the ARIMA model errors are assumed to be white noise.
