
# Forecasting: Principles and Practice(3rd ed)


## 8.7Forecasting with ETS models


Point forecasts can be obtained from the models by iterating the equations for\(t=T+1,\dots,T+h\)and setting all\(\varepsilon_t=0\)for\(t>T\).


For example, for model ETS(M,A,N),\(y_{T+1} = (\ell_T + b_T )(1+ \varepsilon_{T+1}).\)Therefore\(\hat{y}_{T+1|T}=\ell_{T}+b_{T}.\)Similarly,\[\begin{align*}
y_{T+2} &= (\ell_{T+1} + b_{T+1})(1 + \varepsilon_{T+2})\\
        &= \left[
              (\ell_T + b_T) (1+ \alpha\varepsilon_{T+1}) +
              b_T + \beta (\ell_T + b_T)\varepsilon_{T+1}
            \right]
   (1 + \varepsilon_{T+2}).
\end{align*}\]Therefore,\(\hat{y}_{T+2|T}= \ell_{T}+2b_{T},\)and so on. These forecasts are identical to the forecasts from Holt’s linear method, and also to those from model ETS(A,A,N). Thus, the point forecasts obtained from the method and from the two models that underlie the method are identical (assuming that the same parameter values are used). ETS point forecasts constructed in this way are equal to the means of the forecast distributions, except for the models with multiplicative seasonality(Hyndman et al., 2008).


To obtain forecasts from an ETS model, we use theforecast()function from thefablepackage. This function will always return the means of the forecast distribution, even when they differ from these traditional point forecasts.


```
fit |>
  forecast(h = 8) |>
  autoplot(aus_holidays)+
  labs(title="Australian domestic tourism",
       y="Overnight trips (millions)")
```


Figure 8.12: Forecasting Australian domestic overnight trips using an ETS(M,N,A) model.


### Prediction intervals


A big advantage of the statistical models is that prediction intervals can also be generated — something that cannot be done using the point forecasting methods alone. The prediction intervals will differ between models with additive and multiplicative methods.


For most ETS models, a prediction interval can be written as\[
  \hat{y}_{T+h|T} \pm c \sigma_h
\]where\(c\)depends on the coverage probability, and\(\sigma_h^2\)is the forecast variance. Values for\(c\)were given in Table5.1. For ETS models, formulas for\(\sigma_h^2\)can be complicated; the details are given in Chapter 6 ofHyndman et al. (2008). In Table8.8we give the formulas for the additive ETS models, which are the simplest.


For a few ETS models, there are no known formulas for prediction intervals. In these cases, theforecast()function uses simulated future sample paths and computes prediction intervals from the percentiles of these simulated future paths.


### Bibliography
