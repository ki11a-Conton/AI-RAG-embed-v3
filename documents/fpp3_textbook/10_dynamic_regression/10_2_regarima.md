
# Forecasting: Principles and Practice(3rd ed)


## 10.2Regression with ARIMA errors usingfable


The functionARIMA()will fit a regression model with ARIMA errors if exogenous regressors are included in the formula. As introduced in Section9.5, thepdq()special specifies the order of the ARIMA error model. If differencing is specified, then the differencing is applied to all variables in the regression model before the model is estimated. For example, the command


```
ARIMA(y ~ x + pdq(1,1,0))
```


will fit the model\(y_t' = \beta_1 x'_t + \eta'_t\), where\(\eta'_t = \phi_1 \eta'_{t-1} + \varepsilon_t\)is an AR(1) error. This is equivalent to the model\[
  y_t = \beta_0 + \beta_1 x_t + \eta_t,
\]where\(\eta_t\)is an ARIMA(1,1,0) error. Notice that the constant term disappears due to the differencing. To include a constant in the differenced model, we would add1to the model formula.


TheARIMA()function can also be used to select the best ARIMA model for the errors. This is done by not specifying thepdq()special. Whether differencing is required is determined by applying a KPSS test to the residuals from the regression model estimated using ordinary least squares. If differencing is required, then all variables are differenced and the model re-estimated using maximum likelihood estimation. The final model will be expressed in terms of the original variables, even if it has been estimated using differenced variables.


The AICc is calculated for the final model, and this value can be used to determine the best predictors. That is, the procedure should be repeated for all subsets of predictors to be considered, and the model with the lowest AICc value selected.


### Example: US Personal Consumption and Income


Figure10.1shows the quarterly changes in personal consumption expenditure and personal disposable income from 1970 to 2019 Q2. We would like to forecast changes in expenditure based on changes in income. A change in income does not necessarily translate to an instant change in consumption (e.g., after the loss of a job, it may take a few months for expenses to be reduced to allow for the new circumstances). However, we will ignore this complexity in this example and try to measure the instantaneous effect of the average change of income on the average change of consumption expenditure.


```
us_change |>
  pivot_longer(c(Consumption, Income),
               names_to = "var", values_to = "value") |>
  ggplot(aes(x = Quarter, y = value)) +
  geom_line() +
  facet_grid(vars(var), scales = "free_y") +
  labs(title = "US consumption and personal income",
       y = "Quarterly % change")
```


Figure 10.1: Percentage changes in quarterly personal consumption expenditure and personal disposable income for the USA, 1970 Q1 to 2019 Q2.


```
fit <- us_change |>
  model(ARIMA(Consumption ~ Income))
report(fit)
#> Series: Consumption 
#> Model: LM w/ ARIMA(1,0,2) errors 
#> 
#> Coefficients:
#>          ar1      ma1     ma2  Income  intercept
#>       0.7070  -0.6172  0.2066  0.1976     0.5949
#> s.e.  0.1068   0.1218  0.0741  0.0462     0.0850
#> 
#> sigma^2 estimated as 0.3113:  log likelihood=-163
#> AIC=338.1   AICc=338.5   BIC=357.8
```


The data are clearly already stationary (as we are considering percentage changes rather than raw expenditure and income), so there is no need for any differencing. The fitted model is\[\begin{align*}
  y_t &= 0.595 +
         0.198 x_t + \eta_t, \\
  \eta_t &= 0.707 \eta_{t-1} + \varepsilon_t
        -0.617 \varepsilon_{t-1} +
        0.207 \varepsilon_{t-2},\\
  \varepsilon_t &\sim \text{NID}(0,0.311).
\end{align*}\]


We can recover estimates of both the\(\eta_t\)and\(\varepsilon_t\)series using theresiduals()function.


```
bind_rows(
    `Regression residuals` =
        as_tibble(residuals(fit, type = "regression")),
    `ARIMA residuals` =
        as_tibble(residuals(fit, type = "innovation")),
    .id = "type"
  ) |>
  mutate(
    type = factor(type, levels=c(
      "Regression residuals", "ARIMA residuals"))
  ) |>
  ggplot(aes(x = Quarter, y = .resid)) +
  geom_line() +
  facet_grid(vars(type))
```


Figure 10.2: Regression residuals (\(\eta_t\)) and ARIMA residuals (\(\varepsilon_t\)) from the fitted model.


It is the ARIMA estimated errors (the innovation residuals) that should resemble a white noise series.


```
fit |> gg_tsresiduals()
```


Figure 10.3: The innovation residuals (i.e., the estimated ARIMA errors) are not significantly different from white noise.


```
augment(fit) |>
  features(.innov, ljung_box, dof = 3, lag = 8)
#> # A tibble: 1 × 3
#>   .model                      lb_stat lb_pvalue
#>   <chr>                         <dbl>     <dbl>
#> 1 ARIMA(Consumption ~ Income)    5.21     0.391
```
