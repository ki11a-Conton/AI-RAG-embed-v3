
# Forecasting: Principles and Practice(3rd ed)


## 13.9Dealing with outliers and missing values


Real data often contains missing values, outlying observations, and other messy features. Dealing with them can sometimes be troublesome.


### Outliers


Outliers are observations that are very different from the majority of the observations in the time series. They may be errors, or they may simply be unusual. (See Section7.3for a discussion of outliers in a regression context.) None of the methods we have considered in this book will work well if there are extreme outliers in the data. In this case, we may wish to replace them with missing values, or with an estimate that is more consistent with the majority of the data.


Simply replacing outliers without thinking about why they have occurred is a dangerous practice. They may provide useful information about the process that produced the data, which should be taken into account when forecasting. However, if we are willing to assume that the outliers are genuinely errors, or that they won’t occur in the forecasting period, then replacing them can make the forecasting task easier.


Figure13.11shows the number of visitors to the Adelaide Hills region of South Australia. There appears to be an unusual observation in 2002 Q4.


```
tourism |>
  filter(
    Region == "Adelaide Hills", Purpose == "Visiting"
  ) |>
  autoplot(Trips) +
  labs(title = "Quarterly overnight trips to Adelaide Hills",
       y = "Number of trips")
```


Figure 13.11: Number of overnight trips to the Adelaide Hills region of South Australia.


One useful way to find outliers is to applySTL()to the series with the argumentrobust=TRUE. Then any outliers should show up in the remainder series. The data in Figure13.11have almost no visible seasonality, so we will apply STL without a seasonal component by settingperiod=1.


```
ah_decomp <- tourism |>
  filter(
    Region == "Adelaide Hills", Purpose == "Visiting"
  ) |>
  # Fit a non-seasonal STL decomposition
  model(
    stl = STL(Trips ~ season(period = 1), robust = TRUE)
  ) |>
  components()
ah_decomp |> autoplot()
```


Figure 13.12: STL decomposition of visitors to the Adelaide Hills region of South Australia, with no seasonal component.


In the above example the outlier was easy to identify. In more challenging cases, using a boxplot of the remainder series would be useful. We can identify as outliers those that are greater than 1.5 interquartile ranges (IQRs) from the central 50% of the data. If the remainder was normally distributed, this would show 7 in every 1000 observations as “outliers”. A stricter rule is to define outliers as those that are greater than 3 interquartile ranges (IQRs) from the central 50% of the data, which would make only 1 in 500,000 normally distributed observations to be outliers. This is the rule we prefer to use.


```
outliers <- ah_decomp |>
  filter(
    remainder < quantile(remainder, 0.25) - 3*IQR(remainder) |
    remainder > quantile(remainder, 0.75) + 3*IQR(remainder)
  )
outliers
#> # A dable: 1 x 9 [1Q]
#> # Key:     Region, State, Purpose, .model [1]
#> # :        Trips = trend + remainder
#>   Region      State Purpose .model Quarter Trips trend remainder season_adjust
#>   <chr>       <chr> <chr>   <chr>    <qtr> <dbl> <dbl>     <dbl>         <dbl>
#> 1 Adelaide H… Sout… Visiti… stl    2002 Q4  81.1  11.1      70.0          81.1
```


This finds the one outlier that we suspected from Figure13.11. Something similar could be applied to the full data set to identify unusual observations in other series.


### Missing values


Missing data can arise for many reasons, and it is worth considering whether the missingness will induce bias in the forecasting model. For example, suppose we are studying sales data for a store, and missing values occur on public holidays when the store is closed. The following day may have increased sales as a result. If we fail to allow for this in our forecasting model, we will most likely under-estimate sales on the first day after the public holiday, but over-estimate sales on the days after that. One way to deal with this kind of situation is to use a dynamic regression model, with dummy variables indicating if the day is a public holiday or the day after a public holiday. No automated method can handle such effects as they depend on the specific forecasting context.


In other situations, the missingness may be essentially random. For example, someone may have forgotten to record the sales figures, or the data recording device may have malfunctioned. If the timing of the missing data is not informative for the forecasting problem, then the missing values can be handled more easily.


Finally, we might remove some unusual observations, thus creating missing values in the series.


Some methods allow for missing values without any problems. For example, the naïve forecasting method continues to work, with the most recent non-missing value providing the forecast for the future time periods. Similarly, the other benchmark methods introduced in Section5.2will all produce forecasts when there are missing values present in the historical data. Thefablefunctions for ARIMA models, dynamic regression models and NNAR models will also work correctly without causing errors. However, other modelling functions do not handle missing values includingETS()andSTL().


When missing values cause errors, there are at least two ways to handle the problem. First, we could just take the section of data after the last missing value, assuming there is a long enough series of observations to produce meaningful forecasts. Alternatively, we could replace the missing values with estimates. To do this, we first fit an ARIMA model to the data containing missing values, and then use the model to interpolate the missing observations.


We will replace the outlier identified in Figure13.12by an estimate using an ARIMA model.


```
ah_miss <- tourism |>
  filter(
    Region == "Adelaide Hills",
    Purpose == "Visiting"
  ) |>
  # Remove outlying observations
  anti_join(outliers) |>
  # Replace with missing values
  fill_gaps()
ah_fill <- ah_miss |>
  # Fit ARIMA model to the data containing missing values
  model(ARIMA(Trips)) |>
  # Estimate Trips for all periods
  interpolate(ah_miss)
ah_fill |>
  # Only show outlying periods
  right_join(outliers |> select(-Trips))
#> # A tsibble: 1 x 9 [?]
#> # Key:       Region, State, Purpose [1]
#>   Region      State Purpose Quarter Trips .model trend remainder season_adjust
#>   <chr>       <chr> <chr>     <qtr> <dbl> <chr>  <dbl>     <dbl>         <dbl>
#> 1 Adelaide H… Sout… Visiti… 2002 Q4  8.50 stl     11.1      70.0          81.1
```


Theinterpolate()function uses the ARIMA model to estimate any missing values in the series. In this case, the outlier of 81.1 has been replaced with 8.5. The resulting series is shown in Figure13.13.


Theah_filldata could now be modeled with a function that does not allow missing values.


```
ah_fill |>
  autoplot(Trips) +
  autolayer(ah_fill |> filter_index("2002 Q3"~"2003 Q1"),
    Trips, colour="#D55E00") +
  labs(title = "Quarterly overnight trips to Adelaide Hills",
       y = "Number of trips")
```


Figure 13.13: Number of overnight trips to the Adelaide Hills region of South Australia with the 2002Q4 outlier being replaced using an ARIMA model for interpolation.
