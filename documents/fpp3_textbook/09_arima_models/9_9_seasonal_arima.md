
# Forecasting: Principles and Practice(3rd ed)


## 9.9Seasonal ARIMA models


So far, we have restricted our attention to non-seasonal data and non-seasonal ARIMA models. However, ARIMA models are also capable of modelling a wide range of seasonal data.


A seasonal ARIMA model is formed by including additional seasonal terms in the ARIMA models we have seen so far. It is written as follows:


where\(m =\)the seasonal period (e.g., number of observations per year). We use uppercase notation for the seasonal parts of the model, and lowercase notation for the non-seasonal parts of the model.


The seasonal part of the model consists of terms that are similar to the non-seasonal components of the model, but involve backshifts of the seasonal period. For example, an ARIMA(1,1,1)(1,1,1)\(_{4}\)model (without a constant) is for quarterly data (\(m=4\)), and can be written as\[
  (1 - \phi_{1}B)~(1 - \Phi_{1}B^{4}) (1 - B) (1 - B^{4})y_{t} =
  (1 + \theta_{1}B)~ (1 + \Theta_{1}B^{4})\varepsilon_{t}.
\]


The additional seasonal terms are simply multiplied by the non-seasonal terms.


### ACF/PACF


The seasonal part of an AR or MA model will be seen in the seasonal lags of the PACF and ACF. For example, an ARIMA(0,0,0)(0,0,1)\(_{12}\)model will show:

- a spike at lag 12 in the ACF but no other significant spikes;
- exponential decay in the seasonal lags of the PACF (i.e., at lags 12, 24, 36, …).

Similarly, an ARIMA(0,0,0)(1,0,0)\(_{12}\)model will show:

- exponential decay in the seasonal lags of the ACF;
- a single significant spike at lag 12 in the PACF.

In considering the appropriate seasonal orders for a seasonal ARIMA model, restrict attention to the seasonal lags.


The modelling procedure is almost the same as for non-seasonal data, except that we need to select seasonal AR and MA terms as well as the non-seasonal components of the model. The process is best illustrated via examples.


### Example: Monthly US leisure and hospitality employment


We will describe seasonal ARIMA modelling using monthly US employment data for leisure and hospitality jobs from January 2001 to September 2019, shown in Figure9.18.


```
leisure <- us_employment |>
  filter(Title == "Leisure and Hospitality",
         year(Month) > 2000) |>
  mutate(Employed = Employed/1000) |>
  select(Month, Employed)
autoplot(leisure, Employed) +
  labs(title = "US employment: leisure and hospitality",
       y="Number of people (millions)")
```


Figure 9.18: Monthly US leisure and hospitality employment, 2001-2019.


The data are clearly non-stationary, with strong seasonality and a nonlinear trend, so we will first take a seasonal difference. The seasonally differenced data are shown in Figure9.19.


```
leisure |>
  gg_tsdisplay(difference(Employed, 12),
               plot_type='partial', lag=36) +
  labs(title="Seasonally differenced", y="")
```


Figure 9.19: Seasonally differenced Monthly US leisure and hospitality employment.


These are also clearly non-stationary, so we take a further first difference in Figure9.20.


```
leisure |>
  gg_tsdisplay(difference(Employed, 12) |> difference(),
               plot_type='partial', lag=36) +
  labs(title = "Double differenced", y="")
```


Figure 9.20: Double differenced Monthly US leisure and hospitality employment.


Our aim now is to find an appropriate ARIMA model based on the ACF and PACF shown in Figure9.20. The significant spike at lag 2 in the ACF suggests a non-seasonal MA(2) component. The significant spike at lag 12 in the ACF suggests a seasonal MA(1) component. Consequently, we begin with an ARIMA(0,1,2)(0,1,1)\(_{12}\)model, indicating a first difference, a seasonal difference, and non-seasonal MA(2) and seasonal MA(1) component. If we had started with the PACF, we may have selected an ARIMA(2,1,0)(0,1,1)\(_{12}\)model — using the PACF to select the non-seasonal part of the model and the ACF to select the seasonal part of the model. We will also include an automatically selected model. By settingstepwise=FALSEandapproximation=FALSE, we are making R work extra hard to find a good model. This takes much longer, but with only one series to model, the extra time taken is not a problem.


```
fit <- leisure |>
  model(
    arima012011 = ARIMA(Employed ~ pdq(0,1,2) + PDQ(0,1,1)),
    arima210011 = ARIMA(Employed ~ pdq(2,1,0) + PDQ(0,1,1)),
    auto = ARIMA(Employed, stepwise = FALSE, approx = FALSE)
  )
fit |> pivot_longer(everything(), names_to = "Model name",
                     values_to = "Orders")
#> # A mable: 3 x 2
#> # Key:     Model name [3]
#>   `Model name`                    Orders
#>   <chr>                          <model>
#> 1 arima012011  <ARIMA(0,1,2)(0,1,1)[12]>
#> 2 arima210011  <ARIMA(2,1,0)(0,1,1)[12]>
#> 3 auto         <ARIMA(2,1,0)(1,1,1)[12]>
glance(fit) |> arrange(AICc) |> select(.model:BIC)
#> # A tibble: 3 × 6
#>   .model       sigma2 log_lik   AIC  AICc   BIC
#>   <chr>         <dbl>   <dbl> <dbl> <dbl> <dbl>
#> 1 auto        0.00142    395. -780. -780. -763.
#> 2 arima210011 0.00145    392. -776. -776. -763.
#> 3 arima012011 0.00146    391. -775. -775. -761.
```


TheARIMA()function usesunitroot_nsdiffs()to determine\(D\)(the number of seasonal differences to use), andunitroot_ndiffs()to determine\(d\)(the number of ordinary differences to use), when these are not specified. The selection of the other model parameters (\(p,q,P\)and\(Q\)) are all determined by minimizing the AICc, as with non-seasonal ARIMA models.


The three fitted models have similar AICc values, with the automatically selected model being a little better. Our second “guess” of ARIMA(2,1,0)(0,1,1)\(_{12}\)turned out to be very close to the automatically selected model of ARIMA(2,1,0)(1,1,1)\(_{12}\).


The residuals for the best model are shown in Figure9.21.


```
fit |> select(auto) |> gg_tsresiduals(lag=36)
```


Figure 9.21: Residuals from the fitted ARIMA(2,1,0)(1,1,1)\(_{12}\)model.


One small but significant spike (at lag 11) out of 36 is still consistent with white noise. To be sure, we use a Ljung-Box test, being careful to set the degrees of freedom to match the number of parameters in the model.


```
augment(fit) |>
  filter(.model == "auto") |>
  features(.innov, ljung_box, lag=24, dof=4)
#> # A tibble: 1 × 3
#>   .model lb_stat lb_pvalue
#>   <chr>    <dbl>     <dbl>
#> 1 auto      16.6     0.680
```


The large p-value confims that the residuals are similar to white noise.


Thus, we now have a seasonal ARIMA model that passes the required checks and is ready for forecasting. Forecasts from the model for the next three years are shown in Figure9.22. The forecasts have captured the seasonal pattern very well, and the increasing trend extends the recent pattern. The trend in the forecasts is induced by the double differencing.


```
forecast(fit, h=36) |>
  filter(.model=='auto') |>
  autoplot(leisure) +
  labs(title = "US employment: leisure and hospitality",
       y="Number of people (millions)")
```


Figure 9.22: Forecasts of monthly US leisure and hospitality employment using the ARIMA(2,1,0)(1,1,1)\(_{12}\)model. 80% and 95% prediction intervals are shown.


### Example: Corticosteroid drug sales in Australia


For our second example, we will try to forecast monthly corticosteroid drug sales in Australia. These are known as H02 drugs under the Anatomical Therapeutic Chemical classification scheme.


```
h02 <- PBS |>
  filter(ATC2 == "H02") |>
  summarise(Cost = sum(Cost)/1e6)
h02 |>
  mutate(log(Cost)) |>
  pivot_longer(-Month) |>
  ggplot(aes(x = Month, y = value)) +
  geom_line() +
  facet_grid(name ~ ., scales = "free_y") +
  labs(y="", title="Corticosteroid drug scripts (H02)")
```


Figure 9.23: Corticosteroid drug sales in Australia (in millions of scripts per month). Logged data shown in bottom panel.


Data from July 1991 to June 2008 are plotted in Figure9.23. There is a small increase in the variance with the level, so we take logarithms to stabilise the variance.


The data are strongly seasonal and obviously non-stationary, so seasonal differencing will be used. The seasonally differenced data are shown in Figure9.24. It is not clear at this point whether we should do another difference or not. We decide not to, but the choice is not obvious.


The last few observations appear to be different (more variable) from the earlier data. This may be due to the fact that data are sometimes revised when earlier sales are reported late.


```
h02 |> gg_tsdisplay(difference(log(Cost), 12),
                     plot_type='partial', lag_max = 24)
```


Figure 9.24: Seasonally differenced corticosteroid drug sales in Australia (in millions of scripts per month).


In the plots of the seasonally differenced data, there are spikes in the PACF at lags 12 and 24, but nothing at seasonal lags in the ACF. This may be suggestive of a seasonal AR(2) term. In the non-seasonal lags, there are three significant spikes in the PACF, suggesting a possible AR(3) term. The pattern in the ACF is not indicative of any simple model.


Consequently, this initial analysis suggests that a possible model for these data is an ARIMA(3,0,0)(2,1,0)\(_{12}\). We fit this model, along with some variations on it, and compute the AICc values shown in Table9.2.


Of these models, the best is the ARIMA(3,0,1)(0,1,2)\(_{12}\)model (i.e., it has the smallest AICc value). The innovation residuals from this model are shown in Figure9.25.


```
fit <- h02 |>
  model(ARIMA(log(Cost) ~ 0 + pdq(3,0,1) + PDQ(0,1,2)))
fit |> gg_tsresiduals(lag_max=36)
```


Figure 9.25: Innovation residuals from the ARIMA(3,0,1)(0,1,2)\(_{12}\)model applied to the H02 monthly script sales data.


```
augment(fit) |>
  features(.innov, ljung_box, lag = 24, dof = 6)
#> # A tibble: 1 × 3
#>   .model                                             lb_stat lb_pvalue
#>   <chr>                                                <dbl>     <dbl>
#> 1 ARIMA(log(Cost) ~ 0 + pdq(3, 0, 1) + PDQ(0, 1, 2))    23.7     0.166
```


There are a few significant spikes in the ACF, but the model passes the Ljung-Box test.


Next we will try using the automatic ARIMA algorithm. RunningARIMA()with all arguments left at their default values led to an ARIMA(2,1,0)(0,1,1)\(_{12}\)model. RunningARIMA()withstepwise=FALSEandapproximation=FALSEgives an ARIMA(2,1,3)(0,1,1)\(_{12}\)model. All of these models will give almost the same forecasts, so it doesn’t matter much which one we use.


### Test set evaluation:


We will compare some of the models fitted so far using a test set consisting of the last two years of data. Thus, we fit the models using data from July 1991 to June 2006, and forecast the script sales for July 2006 – June 2008. The results are summarised in Table9.3.


The models chosen manually are close to the best model over this test set based on the RMSE values, while those models chosen automatically withARIMA()are not far behind.


When models are compared using AICc values, it is important that all models have the same orders of differencing. However, when comparing models using a test set, it does not matter how the forecasts were produced — the comparisons are always valid. Consequently, in the table above, we can include some models with only seasonal differencing and some models with both first and seasonal differencing, while in the earlier table containing AICc values, we only compared models with seasonal differencing but no first differencing.


Sometimes it is not possible to find a model that passes all of the residual tests. In practice, we would normally use the best model we could find, even if it did not pass all of the tests.


Forecasts from the ARIMA(3,0,1)(0,1,2)\(_{12}\)model (which has the second lowest RMSE value on the test set, and the best AICc value amongst models with only seasonal differencing) are shown in Figure9.26.


```
h02 |>
  model(ARIMA(log(Cost) ~ 0 + pdq(3,0,1) + PDQ(0,1,2))) |>
  forecast() |>
  autoplot(h02) +
  labs(y=" $AU (millions)",
       title="Corticosteroid drug scripts (H02) sales")
```


Figure 9.26: Forecasts from the ARIMA(3,0,1)(0,1,2)\(_{12}\)model applied to the H02 monthly script sales data.
