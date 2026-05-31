
# Forecasting: Principles and Practice(3rd ed)


## 13.1Weekly, daily and sub-daily data


Weekly, daily and sub-daily data can be challenging for forecasting, although for different reasons.


### Weekly data


Weekly data is difficult to work with because the seasonal period (the number of weeks in a year) is both large and non-integer. The average number of weeks in a year is 52.18. Most of the methods we have considered require the seasonal period to be an integer. Even if we approximate it by 52, most of the methods will not handle such a large seasonal period efficiently.


The simplest approach is to use an STL decomposition along with a non-seasonal method applied to the seasonally adjusted data (as discussed in Chapter3). Here is an example using weekly data on US finished motor gasoline products supplied (in millions of barrels per day) from February 1991 to May 2005.


```
my_dcmp_spec <- decomposition_model(
  STL(Barrels),
  ETS(season_adjust ~ season("N"))
)
us_gasoline |>
  model(stl_ets = my_dcmp_spec) |>
  forecast(h = "2 years") |>
  autoplot(us_gasoline) +
  labs(y = "Millions of barrels per day",
       title = "Weekly US gasoline production")
```


Figure 13.1: Forecasts for weekly US gasoline production using an STL decomposition with an ETS model for the seasonally adjusted data.


An alternative approach is to use a dynamic harmonic regression model, as discussed in Section10.5. In the following example, the number of Fourier terms was selected by minimising the AICc. The order of the ARIMA model is also selected by minimising the AICc, although that is done within theARIMA()function. We usePDQ(0,0,0)to preventARIMA()trying to handle the seasonality using seasonal ARIMA components.


```
gas_dhr <- us_gasoline |>
  model(dhr = ARIMA(Barrels ~ PDQ(0, 0, 0) + fourier(K = 6)))
```


```
gas_dhr |>
  forecast(h = "2 years") |>
  autoplot(us_gasoline) +
  labs(y = "Millions of barrels per day",
       title = "Weekly US gasoline production")
```


Figure 13.2: Forecasts for weekly US gasoline production using a dynamic harmonic regression model.


The fitted model has 6 pairs of Fourier terms and can be written as\[
  y_t = bt + \sum_{j=1}^{6}
    \left[
      \alpha_j\sin\left(\frac{2\pi j t}{52.18}\right) +
      \beta_j\cos\left(\frac{2\pi j t}{52.18}\right)
    \right] +
    \eta_t
\]where\(\eta_t\)is an ARIMA(0,1,1) process. Because\(\eta_t\)is non-stationary, the model is actually estimated on the differences of the variables on both sides of this equation. There are 12 parameters to capture the seasonality, while the total number of degrees of freedom is 14 (the other two coming from the MA parameter and the drift parameter).


The STL approach is preferable when the seasonality changes over time. The dynamic harmonic regression approach is preferable if there are covariates that are useful predictors as these can be added as additional regressors.


### Daily and sub-daily data


Daily and sub-daily (such as hourly) data are challenging for a different reason — they often involve multiple seasonal patterns, and so we need to use a method that handles such complex seasonality.


Of course, if the time series is relatively short so that only one type of seasonality is present, then it will be possible to use one of the single-seasonal methods we have discussed in previous chapters (e.g., ETS or a seasonal ARIMA model). But when the time series is long enough so that some of the longer seasonal periods become apparent, it will be necessary to use STL, dynamic harmonic regression or Prophet, as discussed in Section12.1.


However, these methods only allow for regular seasonality. Capturing seasonality associated with moving events such as Easter, Eid, or the Chinese New Year is more difficult. Even with monthly data, this can be tricky as the festivals can fall in either March or April (for Easter), in January or February (for the Chinese New Year), or at any time of the year (for Eid).


The best way to deal with moving holiday effects is to include dummy variables in the model. This can be done within theARIMA()orprophet()functions, for example, but not withinETS(). In fact,prophet()has aholiday()special to easily incorporate holiday effects.
