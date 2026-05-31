
# Forecasting: Principles and Practice(3rd ed)


## 9.10ARIMA vs ETS


It is a commonly held myth that ARIMA models are more general than exponential smoothing. While linear exponential smoothing models are all special cases of ARIMA models, the non-linear exponential smoothing models have no equivalent ARIMA counterparts. On the other hand, there are also many ARIMA models that have no exponential smoothing counterparts. In particular, all ETS models are non-stationary, while some ARIMA models are stationary. Figure9.27shows the overlap between the two model classes.


Figure 9.27: The ETS and ARIMA model classes overlap with the additive ETS models having equivalent ARIMA forms.


The ETS models with seasonality or non-damped trend or both have two unit roots (i.e., they need two levels of differencing to make them stationary). All other ETS models have one unit root (they need one level of differencing to make them stationary).


Table9.4gives the equivalence relationships for the two classes of models. For the seasonal models, the ARIMA parameters have a large number of restrictions.


The AICc is useful for selecting between models in the same class. For example, we can use it to select an ARIMA model between candidate ARIMA models20or an ETS model between candidate ETS models. However, it cannot be used to compare between ETS and ARIMA models because they are in different model classes, and the likelihood is computed in different ways. The examples below demonstrate selecting between these classes of models.


### ComparingARIMA()andETS()on non-seasonal data


We can use time series cross-validation to compare ARIMA and ETS models. Let’s consider the Australian population from theglobal_economydataset, as introduced in Section8.2.


```
aus_economy <- global_economy |>
  filter(Code == "AUS") |>
  mutate(Population = Population/1e6)

aus_economy |>
  slice(-n()) |>
  stretch_tsibble(.init = 10) |>
  model(
    ETS(Population),
    ARIMA(Population)
  ) |>
  forecast(h = 1) |>
  accuracy(aus_economy) |>
  select(.model, RMSE:MAPE)
#> # A tibble: 2 × 5
#>   .model              RMSE    MAE   MPE  MAPE
#>   <chr>              <dbl>  <dbl> <dbl> <dbl>
#> 1 ARIMA(Population) 0.194  0.0789 0.277 0.509
#> 2 ETS(Population)   0.0774 0.0543 0.112 0.327
```


In this case the ETS model has higher accuracy on the cross-validated performance measures. Below we generate and plot forecasts for the next 5 years generated from an ETS model.


```
aus_economy |>
  model(ETS(Population)) |>
  forecast(h = "5 years") |>
  autoplot(aus_economy |> filter(Year >= 2000)) +
  labs(title = "Australian population",
       y = "People (millions)")
```


Figure 9.28: Forecasts from an ETS model fitted to the Australian population.


### ComparingARIMA()andETS()on seasonal data


In this case we want to compare seasonal ARIMA and ETS models applied to the quarterly cement production data (fromaus_production). Because the series is relatively long, we can afford to use a training and a test set rather than time series cross-validation. The advantage is that this is much faster. We create a training set from the beginning of 1988 to the end of 2007 and select an ARIMA and an ETS model using theARIMA()andETS()functions.


```
cement <- aus_production |>
  select(Cement) |>
  filter_index("1988 Q1" ~ .)
train <- cement |> filter_index(. ~ "2007 Q4")
```


The output below shows the model selected and estimated byARIMA(). The ARIMA model does well in capturing all the dynamics in the data as the residuals seem to be white noise.


```
fit_arima <- train |> model(ARIMA(Cement))
report(fit_arima)
#> Series: Cement 
#> Model: ARIMA(1,0,1)(2,1,1)[4] w/ drift 
#> 
#> Coefficients:
#>          ar1      ma1   sar1     sar2     sma1  constant
#>       0.8886  -0.2366  0.081  -0.2345  -0.8979     5.388
#> s.e.  0.0842   0.1334  0.157   0.1392   0.1780     1.484
#> 
#> sigma^2 estimated as 11456:  log likelihood=-463.5
#> AIC=941   AICc=942.7   BIC=957.4
fit_arima |> gg_tsresiduals(lag_max = 16)
```


Figure 9.29: Residual diagnostic plots for the ARIMA model fitted to the quarterly cement production training data.


```
augment(fit_arima) |>
  features(.innov, ljung_box, lag = 8, dof = 5)
#> # A tibble: 1 × 3
#>   .model        lb_stat lb_pvalue
#>   <chr>           <dbl>     <dbl>
#> 1 ARIMA(Cement)   0.783     0.853
```


The output below also shows the ETS model selected and estimated byETS(). This model also does well in capturing all the dynamics in the data, as the residuals similarly appear to be white noise.


```
fit_ets <- train |> model(ETS(Cement))
report(fit_ets)
#> Series: Cement 
#> Model: ETS(M,N,M) 
#>   Smoothing parameters:
#>     alpha = 0.7534 
#>     gamma = 1e-04 
#> 
#>   Initial states:
#>  l[0]  s[0] s[-1] s[-2]  s[-3]
#>  1695 1.031 1.045 1.011 0.9122
#> 
#>   sigma^2:  0.0034
#> 
#>  AIC AICc  BIC 
#> 1104 1106 1121
fit_ets |>
  gg_tsresiduals(lag_max = 16)
```


Figure 9.30: Residual diagnostic plots for the ETS model fitted to the quarterly cement production training data.


```
augment(fit_ets) |>
  features(.innov, ljung_box, lag = 8)
#> # A tibble: 1 × 3
#>   .model      lb_stat lb_pvalue
#>   <chr>         <dbl>     <dbl>
#> 1 ETS(Cement)    5.49     0.704
```


The output below evaluates the forecasting performance of the two competing models over the test set. In this case the ARIMA model seems to be the slightly more accurate model based on the test set RMSE, MAPE and MASE.


```
# Generate forecasts and compare accuracy over the test set
bind_rows(
    fit_arima |> accuracy(),
    fit_ets |> accuracy(),
    fit_arima |> forecast(h = 10) |> accuracy(cement),
    fit_ets |> forecast(h = 10) |> accuracy(cement)
  ) |>
  select(-ME, -MPE, -ACF1)
#> # A tibble: 4 × 7
#>   .model        .type     RMSE   MAE  MAPE  MASE RMSSE
#>   <chr>         <chr>    <dbl> <dbl> <dbl> <dbl> <dbl>
#> 1 ARIMA(Cement) Training  100.  79.9  4.37 0.546 0.582
#> 2 ETS(Cement)   Training  103.  80.0  4.41 0.547 0.596
#> 3 ARIMA(Cement) Test      216. 186.   8.68 1.27  1.26 
#> 4 ETS(Cement)   Test      222. 191.   8.85 1.30  1.29
```


Below we generate and plot forecasts from the ARIMA model for the next 3 years.


```
cement |>
  model(ARIMA(Cement)) |>
  forecast(h="3 years") |>
  autoplot(cement) +
  labs(title = "Cement production in Australia",
       y = "Tonnes ('000)")
```


Figure 9.31: Forecasts from an ARIMA model fitted to all of the available quarterly cement production data since 1988.

- As already noted, comparing information criteria is only valid for ARIMA models of the same orders of differencing.↩︎

As already noted, comparing information criteria is only valid for ARIMA models of the same orders of differencing.↩︎
