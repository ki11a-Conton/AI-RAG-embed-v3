
# Forecasting: Principles and Practice(3rd ed)


## 5.4Residual diagnostics


A good forecasting method will yield innovation residuals with the following properties:

- The innovation residuals are uncorrelated. If there are correlations between innovation residuals, then there is information left in the residuals which should be used in computing forecasts.
- The innovation residuals have zero mean. If they have a mean other than zero, then the forecasts are biased.

Any forecasting method that does not satisfy these properties can be improved. However, that does not mean that forecasting methods that satisfy these properties cannot be improved. It is possible to have several different forecasting methods for the same data set, all of which satisfy these properties. Checking these properties is important in order to see whether a method is using all of the available information, but it is not a good way to select a forecasting method.


If either of these properties is not satisfied, then the forecasting method can be modified to give better forecasts. Adjusting for bias is easy: if the residuals have mean\(m\), then simply add\(m\)to all forecasts and the bias problem is solved. Fixing the correlation problem is harder, and we will not address it until Chapter10.


In addition to these essential properties, it is useful (but not necessary) for the residuals to also have the following two properties.

- The innovation residuals have constant variance. This is known as “homoscedasticity”.
- The innovation residuals are normally distributed.

These two properties make the calculation of prediction intervals easier (see Section5.5for an example). However, a forecasting method that does not satisfy these properties cannot necessarily be improved. Sometimes applying a Box-Cox transformation may assist with these properties, but otherwise there is usually little that you can do to ensure that your innovation residuals have constant variance and a normal distribution. Instead, an alternative approach to obtaining prediction intervals is necessary. We will show how to deal with non-normal innovation residuals in Section5.5.


### Example: Forecasting Google daily closing stock prices


We will continue with the Google daily closing stock price example from Section5.2. For stock market prices and indexes, the best forecasting method is often the naïve method. That is, each forecast is simply equal to the last observed value, or\(\hat{y}_{t} = y_{t-1}\). Hence, the residuals are simply equal to the difference between consecutive observations:\[
  e_{t} = y_{t} - \hat{y}_{t} = y_{t} - y_{t-1}.
\]


The following graph shows the Google daily closing stock price for trading days during 2015. The large jump corresponds to 17 July 2015 when the price jumped 16% due to unexpectedly strong second quarter results. (Thegoogle_2015object was created in Section5.2.)


```
autoplot(google_2015, Close) +
  labs(y = "$US",
       title = "Google daily closing stock prices in 2015")
```


Figure 5.9: Daily Google stock prices in 2015.


The residuals obtained from forecasting this series using the naïve method are shown in Figure5.10. The large positive residual is a result of the unexpected price jump in July.


```
aug <- google_2015 |>
  model(NAIVE(Close)) |>
  augment()
autoplot(aug, .innov) +
  labs(y = "$US",
       title = "Residuals from the naïve method")
```


Figure 5.10: Residuals from forecasting the Google stock price using the naïve method.


```
aug |>
  ggplot(aes(x = .innov)) +
  geom_histogram() +
  labs(title = "Histogram of residuals")
```


Figure 5.11: Histogram of the residuals from the naïve method applied to the Google stock price. The right tail seems a little too long for a normal distribution.


```
aug |>
  ACF(.innov) |>
  autoplot() +
  labs(title = "Residuals from the naïve method")
```


Figure 5.12: ACF of the residuals from the naïve method applied to the Google stock price. The lack of correlation suggesting the forecasts are good.


These graphs show that the naïve method produces forecasts that appear to account for all available information. The mean of the residuals is close to zero and there is no significant correlation in the residuals series. The time plot of the residuals shows that the variation of the residuals stays much the same across the historical data, apart from the one outlier, and therefore the residual variance can be treated as constant. This can also be seen on the histogram of the residuals. The histogram suggests that the residuals may not be normal — the right tail seems a little too long, even when we ignore the outlier. Consequently, forecasts from this method will probably be quite good, but prediction intervals that are computed assuming a normal distribution may be inaccurate.


A convenient shortcut for producing these residual diagnostic graphs is thegg_tsresiduals()function, which will produce a time plot, ACF plot and histogram of the residuals.


```
google_2015 |>
  model(NAIVE(Close)) |>
  gg_tsresiduals()
```


Figure 5.13: Residual diagnostic graphs for the naïve method applied to the Google stock price.


### Portmanteau tests for autocorrelation


In addition to looking at the ACF plot, we can also do a more formal test for autocorrelation by considering a whole set of\(r_k\)values as a group, rather than treating each one separately.


Recall that\(r_k\)is the autocorrelation for lag\(k\). When we look at the ACF plot to see whether each spike is within the required limits, we are implicitly carrying out multiple hypothesis tests, each one with a small probability of giving a false positive. When enough of these tests are done, it is likely that at least one will give a false positive, and so we may conclude that the residuals have some remaining autocorrelation, when in fact they do not.


In order to overcome this problem, we test whether the first\(\ell\)autocorrelations are significantly different from what would be expected from a white noise process. A test for a group of autocorrelations is called aportmanteau test, from a French word describing a suitcase or coat rack carrying several items of clothing.


One such test is theBox-Pierce test, based on the following statistic\[
  Q = T \sum_{k=1}^\ell r_k^2,
\]where\(\ell\)is the maximum lag being considered and\(T\)is the number of observations. If each\(r_k\)is close to zero, then\(Q\)will be small. If some\(r_k\)values are large (positive or negative), then\(Q\)will be large. We suggest using\(\ell=10\)for non-seasonal data and\(\ell=2m\)for seasonal data, where\(m\)is the period of seasonality. However, the test is not good when\(\ell\)is large, so if these values are larger than\(T/5\), then use\(\ell=T/5\)


A related (and more accurate) test is theLjung-Box test, based on\[
  Q^* = T(T+2) \sum_{k=1}^\ell (T-k)^{-1}r_k^2.
\]


Again, large values of\(Q^*\)suggest that the autocorrelations do not come from a white noise series.


How large is too large? If the autocorrelations did come from a white noise series, then both\(Q\)and\(Q^*\)would have a\(\chi^2\)distribution with\(\ell\)degrees of freedom.4.


In the following code,lag\(=\ell\).


```
aug |> features(.innov, box_pierce, lag = 10)
#> # A tibble: 1 × 4
#>   Symbol .model       bp_stat bp_pvalue
#>   <chr>  <chr>          <dbl>     <dbl>
#> 1 GOOG   NAIVE(Close)    7.74     0.654

aug |> features(.innov, ljung_box, lag = 10)
#> # A tibble: 1 × 4
#>   Symbol .model       lb_stat lb_pvalue
#>   <chr>  <chr>          <dbl>     <dbl>
#> 1 GOOG   NAIVE(Close)    7.91     0.637
```


For both\(Q\)and\(Q^*\), the results are not significant (i.e., the\(p\)-values are relatively large). Thus, we can conclude that the residuals are not distinguishable from a white noise series.


An alternative simple approach that may be appropriate for forecasting the Google daily closing stock price is the drift method. Thetidy()function shows the one estimated parameter, the drift coefficient, measuring the average daily change observed in the historical data.


```
fit <- google_2015 |> model(RW(Close ~ drift()))
tidy(fit)
#> # A tibble: 1 × 7
#>   Symbol .model              term  estimate std.error statistic p.value
#>   <chr>  <chr>               <chr>    <dbl>     <dbl>     <dbl>   <dbl>
#> 1 GOOG   RW(Close ~ drift()) b        0.944     0.705      1.34   0.182
```


Applying the Ljung-Box test, we obtain the following result.


```
augment(fit) |> features(.innov, ljung_box, lag=10)
#> # A tibble: 1 × 4
#>   Symbol .model              lb_stat lb_pvalue
#>   <chr>  <chr>                 <dbl>     <dbl>
#> 1 GOOG   RW(Close ~ drift())    7.91     0.637
```


As with the naïve method, the residuals from the drift method are indistinguishable from a white noise series.

- For the ARIMA models discussed in chapters9and10, the degrees of freedom is adjusted to give better results.↩︎

For the ARIMA models discussed in chapters9and10, the degrees of freedom is adjusted to give better results.↩︎
