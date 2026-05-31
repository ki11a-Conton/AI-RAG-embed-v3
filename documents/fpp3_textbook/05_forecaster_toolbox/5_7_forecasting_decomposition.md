
# Forecasting: Principles and Practice(3rd ed)


## 5.7Forecasting with decomposition


Time series decomposition (discussed in Chapter3) can be a useful step in producing forecasts.


Assuming an additive decomposition, the decomposed time series can be written as\[
  y_t = \hat{S}_t + \hat{A}_t,
\]where\(\hat{A}_t = \hat{T}_t+\hat{R}_{t}\)is the seasonally adjusted component. Or, if a multiplicative decomposition has been used, we can write\[
  y_t = \hat{S}_t\hat{A}_t,
\]where\(\hat{A}_t = \hat{T}_t\hat{R}_{t}\).


To forecast a decomposed time series, we forecast the seasonal component,\(\hat{S}_t\), and the seasonally adjusted component\(\hat{A}_t\), separately. It is usually assumed that the seasonal component is unchanging, or changing extremely slowly, so it is forecast by simply taking the last year of the estimated component. In other words, a seasonal naïve method is used for the seasonal component.


To forecast the seasonally adjusted component, any non-seasonal forecasting method may be used. For example, the drift method, or Holt’s method (discussed in Chapter8), or a non-seasonal ARIMA model (discussed in Chapter9), may be used.


### Example: Employment in the US retail sector


```
us_retail_employment <- us_employment |>
  filter(year(Month) >= 1990, Title == "Retail Trade")
dcmp <- us_retail_employment |>
  model(STL(Employed ~ trend(window = 7), robust = TRUE)) |>
  components() |>
  select(-.model)
dcmp |>
  model(NAIVE(season_adjust)) |>
  forecast() |>
  autoplot(dcmp) +
  labs(y = "Number of people",
       title = "US retail employment")
```


Figure 5.18: Naïve forecasts of the seasonally adjusted data obtained from an STL decomposition of the total US retail employment.


Figure5.18shows naïve forecasts of the seasonally adjusted US retail employment data. These are then “reseasonalised” by adding in the seasonal naïve forecasts of the seasonal component.


This is made easy with thedecomposition_model()function, which allows you to compute forecasts via any additive decomposition, using other model functions to forecast each of the decomposition’s components. Seasonal components of the model will be forecast automatically usingSNAIVE()if a different model isn’t specified. The function will also do the reseasonalising for you, ensuring that the resulting forecasts of the original data are obtained. These are shown in Figure5.19.


```
fit_dcmp <- us_retail_employment |>
  model(stlf = decomposition_model(
    STL(Employed ~ trend(window = 7), robust = TRUE),
    NAIVE(season_adjust)
  ))
fit_dcmp |>
  forecast() |>
  autoplot(us_retail_employment)+
  labs(y = "Number of people",
       title = "US retail employment")
```


Figure 5.19: Forecasts of the total US retail employment data based on a naïve forecast of the seasonally adjusted data and a seasonal naïve forecast of the seasonal component, after an STL decomposition of the data.


The prediction intervals shown in this graph are constructed in the same way as the point forecasts. That is, the upper and lower limits of the prediction intervals on the seasonally adjusted data are “reseasonalised” by adding in the forecasts of the seasonal component.


The ACF of the residuals, shown in Figure5.20, displays significant autocorrelations. These are due to the naïve method not capturing the changing trend in the seasonally adjusted series.


```
fit_dcmp |> gg_tsresiduals()
```


Figure 5.20: Checking the residuals.


In subsequent chapters we study more suitable methods that can be used to forecast the seasonally adjusted component instead of the naïve method.
