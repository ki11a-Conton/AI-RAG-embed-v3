
# Forecasting: Principles and Practice(3rd ed)


## 4.3STL Features


The STL decomposition discussed in Chapter3is the basis for several more features.


A time series decomposition can be used to measure the strength of trend and seasonality in a time series. Recall that the decomposition is written as\[
  y_t = T_t + S_{t} + R_t,
\]where\(T_t\)is the smoothed trend component,\(S_{t}\)is the seasonal component and\(R_t\)is a remainder component. For strongly trended data, the seasonally adjusted data should have much more variation than the remainder component. Therefore Var\((R_t)\)/Var\((T_t+R_t)\)should be relatively small. But for data with little or no trend, the two variances should be approximately the same. So we define the strength of trend as:\[
  F_T = \max\left(0, 1 - \frac{\text{Var}(R_t)}{\text{Var}(T_t+R_t)}\right).
\]This will give a measure of the strength of the trend between 0 and 1. Because the variance of the remainder might occasionally be even larger than the variance of the seasonally adjusted data, we set the minimal possible value of\(F_T\)equal to zero.


The strength of seasonality is defined similarly, but with respect to the detrended data rather than the seasonally adjusted data:\[
  F_S = \max\left(0, 1 - \frac{\text{Var}(R_t)}{\text{Var}(S_{t}+R_t)}\right).
\]A series with seasonal strength\(F_S\)close to 0 exhibits almost no seasonality, while a series with strong seasonality will have\(F_S\)close to 1 because Var\((R_t)\)will be much smaller than Var\((S_{t}+R_t)\).


These measures can be useful, for example, when you have a large collection of time series, and you need to find the series with the most trend or the most seasonality. These and other STL-based features are computed using thefeat_stl()function.


```
tourism |>
  features(Trips, feat_stl)
#> # A tibble: 304 × 12
#>    Region         State          Purpose trend_strength seasonal_strength_year
#>    <chr>          <chr>          <chr>            <dbl>                  <dbl>
#>  1 Adelaide       South Austral… Busine…          0.464                  0.407
#>  2 Adelaide       South Austral… Holiday          0.554                  0.619
#>  3 Adelaide       South Austral… Other            0.746                  0.202
#>  4 Adelaide       South Austral… Visiti…          0.435                  0.452
#>  5 Adelaide Hills South Austral… Busine…          0.464                  0.179
#>  6 Adelaide Hills South Austral… Holiday          0.528                  0.296
#>  7 Adelaide Hills South Austral… Other            0.593                  0.404
#>  8 Adelaide Hills South Austral… Visiti…          0.488                  0.254
#>  9 Alice Springs  Northern Terr… Busine…          0.534                  0.251
#> 10 Alice Springs  Northern Terr… Holiday          0.381                  0.832
#> # ℹ 294 more rows
#> # ℹ 7 more variables: seasonal_peak_year <dbl>, seasonal_trough_year <dbl>,
#> #   spikiness <dbl>, linearity <dbl>, curvature <dbl>, stl_e_acf1 <dbl>,
#> #   stl_e_acf10 <dbl>
```


We can then use these features in plots to identify what type of series are heavily trended and what are most seasonal.


```
tourism |>
  features(Trips, feat_stl) |>
  ggplot(aes(x = trend_strength, y = seasonal_strength_year,
             col = Purpose)) +
  geom_point() +
  facet_wrap(vars(State))
```


Figure 4.1: Seasonal strength vs trend strength for all tourism series.


Clearly, holiday series are most seasonal which is unsurprising. The strongest trends tend to be in Western Australia and Victoria. The most seasonal series can also be easily identified and plotted.


```
tourism |>
  features(Trips, feat_stl) |>
  filter(
    seasonal_strength_year == max(seasonal_strength_year)
  ) |>
  left_join(tourism, by = c("State", "Region", "Purpose"), multiple = "all") |>
  ggplot(aes(x = Quarter, y = Trips)) +
  geom_line() +
  facet_grid(vars(State, Region, Purpose))
```


Figure 4.2: The most seasonal series in the Australian tourism data.


This shows holiday trips to the most popular ski region of Australia.


Thefeat_stl()function returns several more features other than those discussed above.

- seasonal_peak_yearindicates the timing of the peaks — which month or quarter contains the largest seasonal component. This tells us something about the nature of the seasonality. In the Australian tourism data, if Quarter 3 is the peak seasonal period, then people are travelling to the region in winter, whereas a peak in Quarter 1 suggests that the region is more popular in summer.
- seasonal_trough_yearindicates the timing of the troughs — which month or quarter contains the smallest seasonal component.
- spikinessmeasures the prevalence of spikes in the remainder component\(R_t\)of the STL decomposition. It is the variance of the leave-one-out variances of\(R_t\).
- linearitymeasures the linearity of the trend component of the STL decomposition. It is based on the coefficient of a linear regression applied to the trend component.
- curvaturemeasures the curvature of the trend component of the STL decomposition. It is based on the coefficient from an orthogonal quadratic regression applied to the trend component.
- stl_e_acf1is the first autocorrelation coefficient of the remainder series.
- stl_e_acf10is the sum of squares of the first ten autocorrelation coefficients of the remainder series.