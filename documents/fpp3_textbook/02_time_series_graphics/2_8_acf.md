
# Forecasting: Principles and Practice(3rd ed)


## 2.8Autocorrelation


Just as correlation measures the extent of a linear relationship between two variables, autocorrelation measures the linear relationship betweenlagged valuesof a time series.


There are several autocorrelation coefficients, corresponding to each panel in the lag plot. For example,\(r_{1}\)measures the relationship between\(y_{t}\)and\(y_{t-1}\),\(r_{2}\)measures the relationship between\(y_{t}\)and\(y_{t-2}\), and so on.


The value of\(r_{k}\)can be written as\[
r_{k} = \frac{\sum\limits_{t=k+1}^T (y_{t}-\bar{y})(y_{t-k}-\bar{y})}
{\sum\limits_{t=1}^T (y_{t}-\bar{y})^2},
\]where\(T\)is the length of the time series. The autocorrelation coefficients make up theautocorrelation functionor ACF.


The autocorrelation coefficients for the beer production data can be computed using theACF()function.


```
recent_production |> ACF(Beer, lag_max = 9)
#> # A tsibble: 9 x 2 [1Q]
#>        lag      acf
#>   <cf_lag>    <dbl>
#> 1       1Q -0.0530 
#> 2       2Q -0.758  
#> 3       3Q -0.0262 
#> 4       4Q  0.802  
#> 5       5Q -0.0775 
#> 6       6Q -0.657  
#> 7       7Q  0.00119
#> 8       8Q  0.707  
#> 9       9Q -0.0888
```


The values in theacfcolumn are\(r_1,\dots,r_9\), corresponding to the nine scatterplots in Figure2.19. We usually plot the ACF to see how the correlations change with the lag\(k\). The plot is sometimes known as acorrelogram.


```
recent_production |>
  ACF(Beer) |>
  autoplot() + labs(title="Australian beer production")
```


Figure 2.20: Autocorrelation function of quarterly beer production.


In this graph:

- \(r_{4}\)is higher than for the other lags. This is due to the seasonal pattern in the data: the peaks tend to be four quarters apart and the troughs tend to be four quarters apart.
- \(r_{2}\)is more negative than for the other lags because troughs tend to be two quarters behind peaks.
- The dashed blue lines indicate whether the correlations are significantly different from zero (as explained in Section2.9).

### Trend and seasonality in ACF plots


When data have a trend, the autocorrelations for small lags tend to be large and positive because observations nearby in time are also nearby in value. So the ACF of a trended time series tends to have positive values that slowly decrease as the lags increase.


When data are seasonal, the autocorrelations will be larger for the seasonal lags (at multiples of the seasonal period) than for other lags.


When data are both trended and seasonal, you see a combination of these effects. Thea10data plotted in Figure2.2shows both trend and seasonality. Its ACF is shown in Figure2.21. The slow decrease in the ACF as the lags increase is due to the trend, while the “scalloped” shape is due to the seasonality.


```
a10 |>
  ACF(Cost, lag_max = 48) |>
  autoplot() +
  labs(title="Australian antidiabetic drug sales")
```


Figure 2.21: ACF of monthly Australian antidiabetic drug sales.
