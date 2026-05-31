
# Forecasting: Principles and Practice(3rd ed)


## 4.1Some simple statistics


Any numerical summary computed from a time series is a feature of that time series — the mean, minimum or maximum, for example. These can be computed using thefeatures()function. For example, let’s compute the means of all the series in the Australian tourism data.


```
tourism |>
  features(Trips, list(mean = mean)) |>
  arrange(mean)
#> # A tibble: 304 × 4
#>    Region          State              Purpose   mean
#>    <chr>           <chr>              <chr>    <dbl>
#>  1 Kangaroo Island South Australia    Other    0.340
#>  2 MacDonnell      Northern Territory Other    0.449
#>  3 Wilderness West Tasmania           Other    0.478
#>  4 Barkly          Northern Territory Other    0.632
#>  5 Clare Valley    South Australia    Other    0.898
#>  6 Barossa         South Australia    Other    1.02 
#>  7 Kakadu Arnhem   Northern Territory Other    1.04 
#>  8 Lasseter        Northern Territory Other    1.14 
#>  9 Wimmera         Victoria           Other    1.15 
#> 10 MacDonnell      Northern Territory Visiting 1.18 
#> # ℹ 294 more rows
```


Here we see that the series with least average number of visits was “Other” visits to Kangaroo Island in South Australia.


Rather than compute one feature at a time, it is convenient to compute many features at once. A common short summary of a data set is to compute five summary statistics: the minimum, first quartile, median, third quartile and maximum. These divide the data into four equal-size sections, each containing 25% of the data. Thequantile()function can be used to compute them.


```
tourism |> features(Trips, quantile)
#> # A tibble: 304 × 8
#>    Region         State           Purpose    `0%`  `25%`   `50%`  `75%` `100%`
#>    <chr>          <chr>           <chr>     <dbl>  <dbl>   <dbl>  <dbl>  <dbl>
#>  1 Adelaide       South Australia Busine…  68.7   134.   153.    177.   242.  
#>  2 Adelaide       South Australia Holiday 108.    135.   154.    172.   224.  
#>  3 Adelaide       South Australia Other    25.9    43.9   53.8    62.5  107.  
#>  4 Adelaide       South Australia Visiti… 137.    179.   206.    229.   270.  
#>  5 Adelaide Hills South Australia Busine…   0       0      1.26    3.92  28.6 
#>  6 Adelaide Hills South Australia Holiday   0       5.77   8.52   14.1   35.8 
#>  7 Adelaide Hills South Australia Other     0       0      0.908   2.09   8.95
#>  8 Adelaide Hills South Australia Visiti…   0.778   8.91  12.2    16.8   81.1 
#>  9 Alice Springs  Northern Terri… Busine…   1.01    9.13  13.3    18.5   34.1 
#> 10 Alice Springs  Northern Terri… Holiday   2.81   16.9   31.5    44.8   76.5 
#> # ℹ 294 more rows
```


Here the minimum is labelled0%and the maximum is labelled100%.
