
# Forecasting: Principles and Practice(3rd ed)


## 11.6Forecasting Australian prison population


Returning to the Australian prison population data (Section11.1), we will compare the forecasts from bottom-up and MinT methods applied to base ETS models, using a test set comprising the final two years or eight quarters 2015Q1–2016Q4 of the available data.


```
fit <- prison_gts |>
  filter(year(Quarter) <= 2014) |>
  model(base = ETS(Count)) |>
  reconcile(
    bottom_up = bottom_up(base),
    MinT = min_trace(base, method = "mint_shrink")
  )
fc <- fit |> forecast(h = 8)
```


```
fc |>
  filter(is_aggregated(State), is_aggregated(Gender),
         is_aggregated(Legal)) |>
  autoplot(prison_gts, alpha = 0.7, level = 90) +
  labs(y = "Number of prisoners ('000)",
       title = "Australian prison population (total)")
```


Figure 11.14: Forecasts for the total Australian quarterly adult prison population for the period 2015Q1–2016Q4.


Figure11.14shows the three sets of forecasts for the aggregate Australian prison population. The base and bottom-up forecasts from the ETS models seem to underestimate the trend over the test period. The MinT approach combines information from all the base forecasts in the aggregation structure; in this case, the base forecasts at the top level are adjusted upwards.


The MinT reconciled prediction intervals are much tighter than the base forecasts, due to MinT being based on an estimator that minimizes variances. The base forecast distributions are also incoherent, and therefore carry with them the extra uncertainty of the incoherency error.


We exclude the bottom-up forecasts from the remaining plots in order to simplify the visual exploration. However, we do revisit their accuracy in the evaluation results presented later.


Figures11.15–11.17show the MinT and base forecasts at various levels of aggregation. To make it easier to see the effect, we only show the last five years of training data. In general, MinT adjusts the base forecasts in the direction of the test set, hence improving the forecast accuracy. There is no guarantee that MinT reconciled forecasts will be more accurate than the base forecasts for every series, but they will be more accurate on average(seePanagiotelis et al., 2021).


```
fc |>
  filter(
    .model %in% c("base", "MinT"),
    !is_aggregated(State), is_aggregated(Legal),
    is_aggregated(Gender)
  ) |>
  autoplot(
    prison_gts |> filter(year(Quarter) >= 2010),
    alpha = 0.7, level = 90
  ) +
  labs(title = "Prison population (by state)",
       y = "Number of prisoners ('000)") +
  facet_wrap(vars(State), scales = "free_y", ncol = 4) +
  theme(axis.text.x = element_text(angle = 90, hjust = 1))
```


Figure 11.15: Forecasts for the Australian quarterly adult prison population, disaggregated by state.


Figure11.15shows forecasts for each of the eight states. There is a general upward trend during the test set period across all the states. However, there appears to be a relatively large and sudden surge in New South Wales and Tasmania, which means the test set observations are well outside the upper bound of the forecast intervals for both these states. Because New South Wales is the state with the largest prison population, this surge will have a substantial impact on the total. In contrast, Victoria shows a substantial dip in 2015Q2–2015Q3, before returning to an upward trend. This dip is not captured in any of the Victorian forecasts.


Figure 11.16: Forecasts for the Australian quarterly adult prison population, disaggregated by legal status and by gender.


Figure 11.17: Forecasts for bottom-level series the Australian quarterly adult prison population, disaggregated by state, by legal status and by gender.


Figure11.17shows the forecasts for some selected bottom-level series of the Australian prison population. The four largest states are represented across the columns, with legal status and gender down the rows. These allow for some interesting analysis and observations that have policy implications. The large increase observed across the states during the 2015Q1–2016Q4 test period appears to be driven by large increases in the remand prison population. These increases seem to be generally missed by both forecasts. In contrast to the other states, for New South Wales there is also a substantial increase in the sentenced prison population. In particular, the increase in numbers of sentenced males in NSW contributes substantially to the rise in state and national prison numbers.


Using theaccuracy()function, we evaluate the forecast accuracy across the grouped structure. The code below evaluates the forecast accuracy for only the top-level national aggregate of the Australian prison population time series. Similar code is used for the rest of the results shown in Table11.3.


```
fc |>
  filter(is_aggregated(State), is_aggregated(Gender),
         is_aggregated(Legal)) |>
  accuracy(data = prison_gts,
           measures = list(mase = MASE,
                           ss = skill_score(CRPS)
                           )
           ) |>
  group_by(.model) |>
  summarise(mase = mean(mase), sspc = mean(ss) * 100)
#> # A tibble: 3 × 3
#>   .model     mase  sspc
#>   <chr>     <dbl> <dbl>
#> 1 MinT      0.895  76.8
#> 2 base      1.72   55.9
#> 3 bottom_up 1.84   33.5
```


Table11.3summarises the accuracy of the base, bottom-up and the MinT reconciled forecasts over the 2015Q1–2016Q4 test period across each of the levels of the grouped aggregation structure as well as all the levels.


We use scaled measures because the numbers of prisoners vary substantially across the groups. The MASE gives a scaled measure of point-forecast accuracy (see Section5.8), while the CRPS skill score gives a scaled measure of distributional forecast accuracy (see Section5.9). A low value of MASE indicates a good forecast, while a high value of the skill score indicates a good forecast.


The results show that the MinT reconciled forecasts improve on the accuracy of the base forecasts and are also more accurate than the bottom-up forecasts. As the MinT optimal reconciliation approach uses information from all levels in the structure, it generates more accurate forecasts than the traditional approaches (such as bottom-up) which use limited information.


### Bibliography
