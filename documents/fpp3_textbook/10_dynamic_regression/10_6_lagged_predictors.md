
# Forecasting: Principles and Practice(3rd ed)


## 10.6Lagged predictors


Sometimes, the impact of a predictor that is included in a regression model will not be simple and immediate. For example, an advertising campaign may impact sales for some time beyond the end of the campaign, and sales in one month will depend on the advertising expenditure in each of the past few months. Similarly, a change in a company’s safety policy may reduce accidents immediately, but have a diminishing effect over time as employees take less care when they become familiar with the new working conditions.


In these situations, we need to allow for lagged effects of the predictor. Suppose that we have only one predictor in our model. Then a model which allows for lagged effects can be written as\[
  y_t = \beta_0 + \gamma_0x_t + \gamma_1 x_{t-1} + \dots + \gamma_k x_{t-k} + \eta_t,
\]where\(\eta_t\)is an ARIMA process. The value of\(k\)can be selected using the AICc, along with the values of\(p\)and\(q\)for the ARIMA error.


### Example: TV advertising and insurance quotations


A US insurance company advertises on national television in an attempt to increase the number of insurance quotations provided (and consequently the number of new policies). Figure10.12shows the number of quotations and the expenditure on television advertising for the company each month from January 2002 to April 2005.


```
insurance |>
  pivot_longer(Quotes:TVadverts) |>
  ggplot(aes(x = Month, y = value)) +
  geom_line() +
  facet_grid(vars(name), scales = "free_y") +
  labs(y = "", title = "Insurance advertising and quotations")
```


Figure 10.12: Numbers of insurance quotations provided per month and the expenditure on advertising per month.


We will consider including advertising expenditure for up to four months; that is, the model may include advertising expenditure in the current month, and the three months before that. When comparing models, it is important that they all use the same training set. In the following code, we exclude the first three months in order to make fair comparisons.


```
fit <- insurance |>
  # Restrict data so models use same fitting period
  mutate(Quotes = c(NA, NA, NA, Quotes[4:40])) |>
  # Estimate models
  model(
    lag0 = ARIMA(Quotes ~ pdq(d = 0) + TVadverts),
    lag1 = ARIMA(Quotes ~ pdq(d = 0) +
                 TVadverts + lag(TVadverts)),
    lag2 = ARIMA(Quotes ~ pdq(d = 0) +
                 TVadverts + lag(TVadverts) +
                 lag(TVadverts, 2)),
    lag3 = ARIMA(Quotes ~ pdq(d = 0) +
                 TVadverts + lag(TVadverts) +
                 lag(TVadverts, 2) + lag(TVadverts, 3))
  )
```


Next we choose the optimal lag length for advertising based on the AICc.


```
glance(fit)
#> # A tibble: 4 × 8
#>   .model sigma2 log_lik   AIC  AICc   BIC ar_roots  ma_roots 
#>   <chr>   <dbl>   <dbl> <dbl> <dbl> <dbl> <list>    <list>   
#> 1 lag0    0.265   -28.3  66.6  68.3  75.0 <cpl [2]> <cpl [0]>
#> 2 lag1    0.209   -24.0  58.1  59.9  66.5 <cpl [1]> <cpl [1]>
#> 3 lag2    0.215   -24.0  60.0  62.6  70.2 <cpl [1]> <cpl [1]>
#> 4 lag3    0.206   -22.2  60.3  65.0  73.8 <cpl [1]> <cpl [1]>
```


The best model (with the smallest AICc value) islag1with two predictors; that is, it includes advertising only in the current month and the previous month. So we now re-estimate that model, but using all the available data.


```
fit_best <- insurance |>
  model(ARIMA(Quotes ~ pdq(d = 0) +
              TVadverts + lag(TVadverts)))
report(fit_best)
#> Series: Quotes 
#> Model: LM w/ ARIMA(1,0,2) errors 
#> 
#> Coefficients:
#>          ar1     ma1     ma2  TVadverts  lag(TVadverts)  intercept
#>       0.5123  0.9169  0.4591     1.2527          0.1464     2.1554
#> s.e.  0.1849  0.2051  0.1895     0.0588          0.0531     0.8595
#> 
#> sigma^2 estimated as 0.2166:  log likelihood=-23.94
#> AIC=61.88   AICc=65.38   BIC=73.7
```


The chosen model has ARIMA(1,0,2) errors. The model can be written as\[
  y_t = 2.155 +
         1.253 x_t +
         0.146 x_{t-1} + \eta_t,
\]where\(y_t\)is the number of quotations provided in month\(t\),\(x_t\)is the advertising expenditure in month\(t\),\[
  \eta_t = 0.512 \eta_{t-1} +
                                     \varepsilon_t +
            0.917 \varepsilon_{t-1} +
            0.459 \varepsilon_{t-2},
\]and\(\varepsilon_t\)is white noise.


We can calculate forecasts using this model if we assume future values for the advertising variable. If we set the future monthly advertising to 8 units, we get the forecasts in Figure10.13.


```
insurance_future <- new_data(insurance, 20) |>
  mutate(TVadverts = 8)
fit_best |>
  forecast(insurance_future) |>
  autoplot(insurance) +
  labs(
    y = "Quotes",
    title = "Forecast quotes with future advertising set to 8"
  )
```


Figure 10.13: Forecasts of monthly insurance quotes, assuming that the future advertising expenditure is 8 units in each future month.
