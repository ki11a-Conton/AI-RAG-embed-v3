
# Forecasting: Principles and Practice(3rd ed)


## 11.4Forecasting Australian domestic tourism


We will compute forecasts for the Australian tourism data that was described in Section11.1. We use the data up to the end of 2015 as a training set, withholding the final two years (eight quarters, 2016Q1–2017Q4) as a test set for evaluation. The code below demonstrates the full workflow for generating coherent forecasts using the bottom-up, OLS and MinT methods.


```
tourism_full <- tourism |>
  aggregate_key((State/Region) * Purpose, Trips = sum(Trips))

fit <- tourism_full |>
  filter(year(Quarter) <= 2015) |>
  model(base = ETS(Trips)) |>
  reconcile(
    bu = bottom_up(base),
    ols = min_trace(base, method = "ols"),
    mint = min_trace(base, method = "mint_shrink")
  )
```


Here,fitcontains thebaseETS model (discussed in Chapter8) for each series intourism_full, along with the three methods for producing coherent forecasts as specified in thereconcile()function.


```
fc <- fit |> forecast(h = "2 years")
```


Passingfitintoforecast()generates base and coherent forecasts across all the series in the aggregation structure. Figures11.12and11.13plot the four point forecasts for the overnight trips for the Australian total, the states, and the purposes of travel, along with the actual observations of the test set.


```
fc |>
  filter(is_aggregated(Region), is_aggregated(Purpose)) |>
  autoplot(
    tourism_full |> filter(year(Quarter) >= 2011),
    level = NULL
  ) +
  labs(y = "Trips ('000)") +
  facet_wrap(vars(State), scales = "free_y")
```


Figure 11.12: Forecasts of overnight trips for Australia and its states over the test period 2016Q1–2017Q4.


```
fc |>
  filter(is_aggregated(State), !is_aggregated(Purpose)) |>
  autoplot(
    tourism_full |> filter(year(Quarter) >= 2011),
    level = NULL
  ) +
  labs(y = "Trips ('000)") +
  facet_wrap(vars(Purpose), scales = "free_y")
```


Figure 11.13: Forecasts of overnight trips by purpose of travel over the test period 2016Q1–2017Q4.


To make it easier to see the differences, we have included only the last five years of the training data, and have omitted the prediction intervals. In most panels, the increase in overnight trips, especially in the second half of the test set, is higher than what is predicted by the point forecasts. This is particularly noticeable for the mainland eastern states of ACT, New South Wales, Queensland and Victoria, and across all purposes of travel.


The accuracy of the forecasts over the test set can be evaluated using theaccuracy()function. We summarise some results in Table11.2using RMSE and MASE.


The scales of the series at different levels of aggregation are quite different, due to aggregation. Hence, we need to be cautious when comparing or calculating scale dependent error measures, such as the RMSE, across levels as the aggregate series will dominate. Therefore, we compare error measures across each level of aggregation, before providing the error measures across all the series in the bottom-row. Notice, that the RMSE increases as we go from the bottom level to the aggregate levels above.


The following code generates the accuracy measures for the aggregate series shown in the first row of the table. Similar code is used to evaluate forecasts for other levels.


```
fc |>
  filter(is_aggregated(State), is_aggregated(Purpose)) |>
  accuracy(
    data = tourism_full,
    measures = list(rmse = RMSE, mase = MASE)
  ) |>
  group_by(.model) |>
  summarise(rmse = mean(rmse), mase = mean(mase))
#> # A tibble: 4 × 3
#>   .model  rmse  mase
#>   <chr>  <dbl> <dbl>
#> 1 base   1721.  1.53
#> 2 bu     3071.  3.17
#> 3 mint   2158.  2.09
#> 4 ols    1804.  1.63
```


Reconciling the base forecasts using OLS and MinT results in more accurate forecasts compared to the bottom-up approach. This result is commonly observed in applications as reconciliation approaches use information from all levels of the structure, resulting in more accurate coherent forecasts compared to the older traditional methods which use limited information. Furthermore, reconciliation usually improves the incoherent base forecasts for almost all levels.
