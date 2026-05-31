
# Forecasting: Principles and Practice(3rd ed)


## 13.4Forecast combinations


An easy way to improve forecast accuracy is to use several different methods on the same time series, and to average the resulting forecasts. Over 50 years ago, John Bates and Clive Granger wrote a famous paper(Bates & Granger, 1969), showing that combining forecasts often leads to better forecast accuracy. Twenty years later,Clemen (1989)wrote


> The results have been virtually unanimous: combining multiple forecasts leads to increased forecast accuracy. In many cases one can make dramatic performance improvements by simply averaging the forecasts.


The results have been virtually unanimous: combining multiple forecasts leads to increased forecast accuracy. In many cases one can make dramatic performance improvements by simply averaging the forecasts.


While there has been considerable research on using weighted averages, or some other more complicated combination approach, using a simple average has proven hard to beat(Wang et al., 2023).


Here is an example using monthly revenue from take-away food in Australia, from April 1982 to December 2018. We use forecasts from the following models: ETS, STL-ETS, and ARIMA; and we compare the results using the last 5 years (60 months) of observations.


```
auscafe <- aus_retail |>
  filter(stringr::str_detect(Industry, "Takeaway")) |>
  summarise(Turnover = sum(Turnover))
train <- auscafe |>
  filter(year(Month) <= 2013)
STLF <- decomposition_model(
  STL(log(Turnover) ~ season(window = Inf)),
  ETS(season_adjust ~ season("N"))
)
cafe_models <- train |>
  model(
    ets = ETS(Turnover),
    stlf = STLF,
    arima = ARIMA(log(Turnover))
  ) |>
  mutate(combination = (ets + stlf + arima) / 3)
cafe_fc <- cafe_models |>
  forecast(h = "5 years")
```


Notice that we form a combination in themutate()function by simply taking a linear function of the estimated models. This very simple syntax will automatically handle the forecast distribution appropriately by taking account of the correlation between the forecast errors of the models that are included. However, to keep the next plot simple, we will omit the prediction intervals.


```
cafe_fc |>
  autoplot(auscafe |> filter(year(Month) > 2008),
           level = NULL) +
  labs(y = "$ billion",
       title = "Australian monthly expenditure on eating out")
```


Figure 13.6: Point forecasts from various methods applied to Australian monthly expenditure on eating out.


```
cafe_fc |>
  accuracy(auscafe) |>
  arrange(RMSE)
#> # A tibble: 4 × 10
#>   .model      .type     ME  RMSE   MAE    MPE  MAPE  MASE RMSSE  ACF1
#>   <chr>       <chr>  <dbl> <dbl> <dbl>  <dbl> <dbl> <dbl> <dbl> <dbl>
#> 1 combination Test    8.09  41.0  31.8  0.401  2.19 0.776 0.790 0.747
#> 2 arima       Test  -25.4   46.2  38.9 -1.77   2.65 0.949 0.890 0.786
#> 3 stlf        Test  -36.9   64.1  51.7 -2.55   3.54 1.26  1.23  0.775
#> 4 ets         Test   86.5  122.  101.   5.51   6.66 2.46  2.35  0.880
```


ARIMA does particularly well with this series, while the combination approach does even better (based on most measures including RMSE and MAE). For other data, ARIMA may be quite poor, while the combination approach is usually not far off, or better than, the best component method.


### Forecast combination distributions


Thecafe_fcobject contains forecast distributions, from which any prediction interval can usually be computed. Let’s look at the intervals for the first period.


```
cafe_fc |> filter(Month == min(Month))
#> # A fable: 4 x 4 [1M]
#> # Key:     .model [4]
#>   .model         Month
#>   <chr>          <mth>
#> 1 ets         2014 Jan
#> 2 stlf        2014 Jan
#> 3 arima       2014 Jan
#> 4 combination 2014 Jan
#> # ℹ 2 more variables: Turnover <dist>, .mean <dbl>
```


The first three are a mixture of normal and transformed normal distributions. The package does not yet combine such diverse distributions, so thecombinationoutput is simply the mean instead.


However, if we work with simulated sample paths, it is possible to create forecast distributions for the combination forecast as well.


```
cafe_futures <- cafe_models |>
  # Generate 1000 future sample paths
  generate(h = "5 years", times = 1000) |>
  # Compute forecast distributions from future sample paths
  as_tibble() |>
  group_by(Month, .model) |>
  summarise(
    dist = distributional::dist_sample(list(.sim))
  ) |>
  ungroup() |>
  # Create fable object
  as_fable(index = Month, key = .model,
           distribution = dist, response = "Turnover")
```


```
# Forecast distributions for h=1
cafe_futures |> filter(Month == min(Month))
#> # A fable: 4 x 3 [1M]
#> # Key:     .model [4]
#>      Month .model              dist
#>      <mth> <chr>             <dist>
#> 1 2014 Jan arima       sample[1000]
#> 2 2014 Jan combination sample[1000]
#> 3 2014 Jan ets         sample[1000]
#> 4 2014 Jan stlf        sample[1000]
```


Now all four models, including the combination, are stored as empirical distributions, and we can plot prediction intervals for the combination forecast, as shown in Figure13.7.


```
cafe_futures |>
  filter(.model == "combination") |>
  autoplot(auscafe |> filter(year(Month) > 2008)) +
  labs(y = "$ billion",
       title = "Australian monthly expenditure on eating out")
```


Figure 13.7: Prediction intervals for the combination forecast of Australian monthly expenditure on eating out.


To check the accuracy of the 95% prediction intervals, we can use a Winkler score (defined in Section5.9).


```
cafe_futures |>
  accuracy(auscafe, measures = interval_accuracy_measures,
    level = 95) |>
  arrange(winkler)
#> # A tibble: 4 × 5
#>   .model      .type winkler pinball scaled_pinball
#>   <chr>       <chr>   <dbl>   <dbl>          <dbl>
#> 1 combination Test     427.    17.8          0.217
#> 2 stlf        Test     590.    29.4          0.358
#> 3 ets         Test     712.    22.6          0.276
#> 4 arima       Test     760.    36.9          0.450
```


Lower is better, so thecombinationforecast is again better than any of the component models.


### Bibliography
