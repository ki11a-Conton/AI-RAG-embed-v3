
# Forecasting: Principles and Practice(3rd ed)


## 10.4Stochastic and deterministic trends


There are two different ways of modelling a linear trend. Adeterministic trendis obtained using the regression model\[
  y_t = \beta_0 + \beta_1 t + \eta_t,
\]where\(\eta_t\)is an ARMA process. Astochastic trendis obtained using the model\[
  y_t = \beta_0 + \beta_1 t + \eta_t,
\]where\(\eta_t\)is an ARIMA process with\(d=1\). In the latter case, we can difference both sides so that\(y_t' = \beta_1 + \eta_t'\), where\(\eta_t'\)is an ARMA process. In other words,\[
  y_t = y_{t-1} + \beta_1 + \eta_t'.
\]This is similar to a random walk with drift (introduced in Section9.1), but here the error term is an ARMA process rather than simply white noise.


Although these models appear quite similar (they only differ in the number of differences that need to be applied to\(\eta_t\)), their forecasting characteristics are quite different.


### Example: Air transport passengers Australia


```
aus_airpassengers |>
  autoplot(Passengers) +
  labs(y = "Passengers (millions)",
       title = "Total annual air passengers")
```


Figure 10.9: Total annual passengers (in millions) for Australian air carriers, 1970–2016.


Figure10.9shows the total number of passengers for Australian air carriers each year from 1970 to 2016. We will fit both a deterministic and a stochastic trend model to these data.


The deterministic trend model is obtained as follows:


```
fit_deterministic <- aus_airpassengers |>
  model(deterministic = ARIMA(Passengers ~ 1 + trend() +
                                pdq(d = 0)))
report(fit_deterministic)
#> Series: Passengers 
#> Model: LM w/ ARIMA(1,0,0) errors 
#> 
#> Coefficients:
#>          ar1  trend()  intercept
#>       0.9564   1.4151     0.9014
#> s.e.  0.0362   0.1972     7.0751
#> 
#> sigma^2 estimated as 4.343:  log likelihood=-100.88
#> AIC=209.77   AICc=210.72   BIC=217.17
```


This model can be written as\[\begin{align*}
  y_t &= 0.901 + 1.415 t + \eta_t \\
  \eta_t &= 0.956 \eta_{t-1}  + \varepsilon_t\\
  \varepsilon_t &\sim \text{NID}(0,4.343).
\end{align*}\]


The estimated growth in visitor numbers is 1.42 million people per year.


Alternatively, the stochastic trend model can be estimated.


```
fit_stochastic <- aus_airpassengers |>
  model(stochastic = ARIMA(Passengers ~ pdq(d = 1)))
report(fit_stochastic)
#> Series: Passengers 
#> Model: ARIMA(0,1,0) w/ drift 
#> 
#> Coefficients:
#>       constant
#>         1.4191
#> s.e.    0.3014
#> 
#> sigma^2 estimated as 4.271:  log likelihood=-98.16
#> AIC=200.31   AICc=200.59   BIC=203.97
```


This model can be written as\(y_t-y_{t-1} = 1.419 + \varepsilon_t\), or equivalently\[\begin{align*}
  y_t &= y_0 + 1.419 t + \eta_t \\
  \eta_t &= \eta_{t-1} + \varepsilon_{t}\\
  \varepsilon_t &\sim \text{NID}(0,4.271).
\end{align*}\]


In this case, the estimated growth in visitor numbers is also 1.42 million people per year. Although the growth estimates are similar, the prediction intervals are not, as Figure10.10shows. In particular, stochastic trends have much wider prediction intervals because the errors are non-stationary.


```
aus_airpassengers |>
  autoplot(Passengers) +
  autolayer(fit_stochastic |> forecast(h = 20),
    colour = "#0072B2", level = 95) +
  autolayer(fit_deterministic |> forecast(h = 20),
    colour = "#D55E00", alpha = 0.65, level = 95) +
  labs(y = "Air passengers (millions)",
       title = "Forecasts from trend models")
```


Figure 10.10: Forecasts of annual passengers for Australian air carriers using a deterministic trend model (orange) and a stochastic trend model (blue).


There is an implicit assumption with deterministic trends that the slope of the trend is not going to change over time. On the other hand, stochastic trends can change, and the estimated growth is only assumed to be the average growth over the historical period, not necessarily the rate of growth that will be observed into the future. Consequently, it is safer to forecast with stochastic trends, especially for longer forecast horizons, as the prediction intervals allow for greater uncertainty in future growth.
