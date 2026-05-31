
# Forecasting: Principles and Practice(3rd ed)


## 5.3Fitted values and residuals


### Fitted values


Each observation in a time series can be forecast using all previous observations. We call thesefitted valuesand they are denoted by\(\hat{y}_{t|t-1}\), meaning the forecast of\(y_t\)based on observations\(y_{1},\dots,y_{t-1}\). We use these so often, we sometimes drop part of the subscript and just write\(\hat{y}_t\)instead of\(\hat{y}_{t|t-1}\). Fitted values almost always involve one-step forecasts (but see Section13.8).


Actually, fitted values are often not true forecasts because any parameters involved in the forecasting method are estimated using all available observations in the time series, including future observations. For example, if we use the mean method, the fitted values are given by\[
  \hat{y}_t = \hat{c}
\]where\(\hat{c}\)is the average computed over all available observations, including those at timesafter\(t\). Similarly, for the drift method, the drift parameter is estimated using all available observations. In this case, the fitted values are given by\[
\hat{y}_t = y_{t-1} + \hat{c}
\]where\(\hat{c} = (y_T-y_1)/(T-1)\). In both cases, there is a parameter to be estimated from the data. The “hat” above the\(c\)reminds us that this is an estimate. When the estimate of\(c\)involves observations after time\(t\), the fitted values are not true forecasts. On the other hand, naïve or seasonal naïve forecasts do not involve any parameters, and so fitted values are true forecasts in such cases.


### Residuals


The “residuals” in a time series model are what is left over after fitting a model. The residuals are equal to the difference between the observations and the corresponding fitted values:\[
  e_{t} = y_{t}-\hat{y}_{t}.
\]


If a transformation has been used in the model, then it is often useful to look at residuals on the transformed scale. We call these “innovation residuals”. For example, suppose we modelled the logarithms of the data,\(w_t = \log(y_t)\). Then the innovation residuals are given by\(w_t - \hat{w}_t\)whereas the regular residuals are given by\(y_t - \hat{y}_t\). (See Section5.6for how to use transformations when forecasting.) If no transformation has been used then the innovation residuals are identical to the regular residuals, and in such cases we will simply call them “residuals”.


The fitted values and residuals from a model can be obtained using theaugment()function. In the beer production example in Section5.2, we saved the fitted models asbeer_fit. So we can simply applyaugment()to this object to compute the fitted values and residuals for all models.


```
augment(beer_fit)
#> # A tsibble: 180 x 6 [1Q]
#> # Key:       .model [3]
#>    .model Quarter  Beer .fitted .resid .innov
#>    <chr>    <qtr> <dbl>   <dbl>  <dbl>  <dbl>
#>  1 Mean   1992 Q1   443    436.   6.55   6.55
#>  2 Mean   1992 Q2   410    436. -26.4  -26.4 
#>  3 Mean   1992 Q3   420    436. -16.4  -16.4 
#>  4 Mean   1992 Q4   532    436.  95.6   95.6 
#>  5 Mean   1993 Q1   433    436.  -3.45  -3.45
#>  6 Mean   1993 Q2   421    436. -15.4  -15.4 
#>  7 Mean   1993 Q3   410    436. -26.4  -26.4 
#>  8 Mean   1993 Q4   512    436.  75.6   75.6 
#>  9 Mean   1994 Q1   449    436.  12.6   12.6 
#> 10 Mean   1994 Q2   381    436. -55.4  -55.4 
#> # ℹ 170 more rows
```


There are three new columns added to the original data:

- .fittedcontains the fitted values;
- .residcontains the residuals;
- .innovcontains the “innovation residuals” which, in this case, are identical to the regular residuals.

Residuals are useful in checking whether a model has adequately captured the information in the data. For this purpose, we use innovation residuals.


If patterns are observable in the innovation residuals, the model can probably be improved. We will look at some tools for exploring patterns in residuals in the next section.
