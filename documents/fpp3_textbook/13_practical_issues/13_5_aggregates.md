
# Forecasting: Principles and Practice(3rd ed)


## 13.5Prediction intervals for aggregates


A common problem is to forecast the aggregate of several time periods of data, using a model fitted to the disaggregated data. For example, we may have monthly data but wish to forecast the total for the next year. Or we may have weekly data, and want to forecast the total for the next four weeks.


If the point forecasts are means, then adding them up will give a good estimate of the total. But prediction intervals are more tricky due to the correlations between forecast errors.


A general solution is to use simulations. Here is an example using ETS models applied to Australian take-away food sales, assuming we wish to forecast the aggregate revenue in the next 12 months.


```
fit <- auscafe |>
  # Fit a model to the data
  model(ETS(Turnover))
futures <- fit |>
  # Simulate 10000 future sample paths, each of length 12
  generate(times = 10000, h = 12) |>
  # Sum the results for each sample path
  as_tibble() |>
  group_by(.rep) |>
  summarise(.sim = sum(.sim)) |>
  # Store as a distribution
  summarise(total = distributional::dist_sample(list(.sim)))
```


We can compute the mean of the simulations, along with prediction intervals:


```
futures |>
  mutate(
    mean = mean(total),
    pi80 = hilo(total, 80),
    pi95 = hilo(total, 95)
  )
#> # A tibble: 1 × 4
#>           total   mean             pi80             pi95
#>          <dist>  <dbl>           <hilo>           <hilo>
#> 1 sample[10000] 19212. [18307, 20134]80 [17846, 20639]95
```


As expected, the mean of the simulated data is close to the sum of the individual forecasts.


```
forecast(fit, h = 12) |>
  as_tibble() |>
  summarise(total = sum(.mean))
#> # A tibble: 1 × 1
#>    total
#>    <dbl>
#> 1 19212.
```
