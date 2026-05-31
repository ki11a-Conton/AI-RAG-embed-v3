
## 12.2 Prophet model

A recent proposal is the Prophet model, available via the `fable.prophet` package. This model was introduced by Facebook ([S. J. Taylor & Letham, 2018](https://otexts.com/fpp3/prophet.html#ref-prophet)), originally for forecasting daily data with weekly and yearly seasonality, plus holiday effects. It was later extended to cover more types of seasonal data. It works best with time series that have strong seasonality and several seasons of historical data.

Prophet can be considered a nonlinear regression model (Chapter [7](https://otexts.com/fpp3/regression.html#regression)), of the form $${y}_{t}=g(t)+s(t)+h(t)+{\epsilon}_{t},$$ where g(t)g(t) describes a piecewise-linear trend (or "growth term"), s(t)s(t) describes the various seasonal patterns, h(t)h(t) captures the holiday effects, and ${\epsilon}_{t}$ is a white noise error term.

- The knots (or changepoints) for the piecewise-linear trend are automatically selected if not explicitly specified. Optionally, a logistic function can be used to set an upper bound on the trend.

- The seasonal component consists of Fourier terms of the relevant periods. By default, order 10 is used for annual seasonality and order 3 is used for weekly seasonality.

- Holiday effects are added as simple dummy variables.

- The model is estimated using a Bayesian approach to allow for automatic selection of the changepoints and other model characteristics.

We illustrate the approach using two data sets: a simple quarterly example, and then the electricity demand data described in the previous section.

### Example: Quarterly cement production

For the simple quarterly example, we will repeat the analysis from Section [9.10](https://otexts.com/fpp3/arima-ets.html#arima-ets) in which we compared an ARIMA and ETS model, but we will add in a prophet model for comparison.

```
library(fable.prophet) cement <- aus_production |>   filter(year(Quarter) >= 1988) train <- cement |>   filter(year(Quarter) <= 2007) fit <- train |>   model(     arima = ARIMA(Cement),     ets = ETS(Cement),     prophet = prophet(Cement ~ season(period = 4, order = 2,                                     type = "multiplicative"))  )
```
Note that the seasonal term must have the `period` fully specified for quarterly and monthly data, as the default values assume the data are observed at least daily.

```
fc <- fit |> forecast(h = "2 years 6 months") fc |> autoplot(cement)
```

In this example, the Prophet forecasts are worse than either the ETS or ARIMA forecasts.

```
fc |> accuracy(cement) #> # A tibble: 3 x 10 #> .model .type ME RMSE MAE MPE MAPE MASE RMSSE ACF1 #> <chr> <chr> <dbl> <dbl> <dbl> <dbl> <dbl> <dbl> <dbl> <dbl> #> 1 arima Test -161. 216. 186. -7.71 8.68 1.27 1.26 0.387 #> 2 ets Test -171. 222. 191. -8.07 8.85 1.30 1.29 0.579 #> 3 prophet Test -176. 248. 215. -8.36 9.89 1.47 1.44 0.698
```

### Example: Half-hourly electricity demand

We will fit a similar model to the dynamic harmonic regression (DHR) model from the previous section, but this time using a Prophet model. For daily and sub-daily data, the default periods are correctly specified, so that we can simply specify the period using a character string as follows.

```
fit <- elec |>   model(     prophet(Demand ~ Temperature + Cooling + Working_Day +             season(period = "day", order = 10) +             season(period = "week", order = 5) +             season(period = "year", order = 3))  ) fit |>   components() |>   autoplot()
```

Figure [12.10](https://otexts.com/fpp3/prophet.html#fig:prophetelec) shows the trend and seasonal components of the fitted model.

The model specification is very similar to the DHR model in the previous section, although the result is different in several important ways. The Prophet model adds a piecewise linear time trend which is not really appropriate here as we don't expect the long term forecasts to continue to follow the downward linear trend at the end of the series.

There is also substantial remaining autocorrelation in the residuals,

```
fit |> gg_tsresiduals()
```

The prediction intervals would be narrower if the autocorrelations were taken into account.

```
fc <- fit |>   forecast(new_data = elec_newdata)
```
```
fc |>   autoplot(elec |> tail(10 * 48)) +   labs(x = "Date", y = "Demand (MWh)")
```

Prophet has the advantage of being much faster to estimate than the DHR models we have considered previously, and it is completely automated. However, it rarely gives better forecast accuracy than the alternative approaches, as these two examples have illustrated.

### Bibliography

Taylor, S. J., & Letham, B. (2018). Forecasting at scale. *The American Statistician*, *72*(1), 37-45.
