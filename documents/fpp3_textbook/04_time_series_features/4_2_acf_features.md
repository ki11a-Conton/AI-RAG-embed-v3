
# Forecasting: Principles and Practice(3rd ed)


## 4.2ACF features


Autocorrelations were discussed in Section2.8. All the autocorrelations of a series can be considered features of that series. We can also summarise the autocorrelations to produce new features; for example, the sum of the first ten squared autocorrelation coefficients is a useful summary of how much autocorrelation there is in a series, regardless of lag.


We can also compute autocorrelations of the changes in the series between periods. That is, we “difference” the data and create a new time series consisting of the differences between consecutive observations. Then we can compute the autocorrelations of this new differenced series. Occasionally it is useful to apply the same differencing operation again, so we compute the differences of the differences. The autocorrelations of this double differenced series may provide useful information.


Another related approach is to compute seasonal differences of a series. If we had monthly data, for example, we would compute the difference between consecutive Januaries, consecutive Februaries, and so on. This enables us to look at how the series is changing between years, rather than between months. Again, the autocorrelations of the seasonally differenced series may provide useful information.


We discuss differencing of time series in more detail in Section9.1.


Thefeat_acf()function computes a selection of the autocorrelations discussed here. It will return six or seven features:

- the first autocorrelation coefficient from the original data;
- the sum of squares of the first ten autocorrelation coefficients from the original data;
- the first autocorrelation coefficient from the differenced data;
- the sum of squares of the first ten autocorrelation coefficients from the differenced data;
- the first autocorrelation coefficient from the twice differenced data;
- the sum of squares of the first ten autocorrelation coefficients from the twice differenced data;
- For seasonal data, the autocorrelation coefficient at the first seasonal lag is also returned.

When applied to the Australian tourism data, we get the following output.


```
tourism |> features(Trips, feat_acf)
#> # A tibble: 304 × 10
#>    Region       State Purpose     acf1 acf10 diff1_acf1 diff1_acf10 diff2_acf1
#>    <chr>        <chr> <chr>      <dbl> <dbl>      <dbl>       <dbl>      <dbl>
#>  1 Adelaide     Sout… Busine…  0.0333  0.131     -0.520       0.463     -0.676
#>  2 Adelaide     Sout… Holiday  0.0456  0.372     -0.343       0.614     -0.487
#>  3 Adelaide     Sout… Other    0.517   1.15      -0.409       0.383     -0.675
#>  4 Adelaide     Sout… Visiti…  0.0684  0.294     -0.394       0.452     -0.518
#>  5 Adelaide Hi… Sout… Busine…  0.0709  0.134     -0.580       0.415     -0.750
#>  6 Adelaide Hi… Sout… Holiday  0.131   0.313     -0.536       0.500     -0.716
#>  7 Adelaide Hi… Sout… Other    0.261   0.330     -0.253       0.317     -0.457
#>  8 Adelaide Hi… Sout… Visiti…  0.139   0.117     -0.472       0.239     -0.626
#>  9 Alice Sprin… Nort… Busine…  0.217   0.367     -0.500       0.381     -0.658
#> 10 Alice Sprin… Nort… Holiday -0.00660 2.11      -0.153       2.11      -0.274
#> # ℹ 294 more rows
#> # ℹ 2 more variables: diff2_acf10 <dbl>, season_acf1 <dbl>
```
