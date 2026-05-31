
# Forecasting: Principles and Practice(3rd ed)


## 5.5Distributional forecasts and prediction intervals


### Forecast distributions


As discussed in Section1.7, we express the uncertainty in our forecasts using a probability distribution. It describes the probability of observing possible future values using the fitted model. The point forecast is the mean of this distribution. Most time series models produce normally distributed forecasts — that is, we assume that the distribution of possible future values follows a normal distribution. We will look at a couple of alternatives to normal distributions later in this section.


### Prediction intervals


A prediction interval gives an interval within which we expect\(y_{t}\)to lie with a specified probability. For example, assuming that distribution of future observations is normal, a 95% prediction interval for the\(h\)-step forecast is\[
  \hat{y}_{T+h|T} \pm 1.96 \hat\sigma_h,
\]where\(\hat\sigma_h\)is an estimate of the standard deviation of the\(h\)-step forecast distribution.


More generally, a prediction interval can be written as\[
  \hat{y}_{T+h|T} \pm c \hat\sigma_h
\]where the multiplier\(c\)depends on the coverage probability. In this book we usually calculate 80% intervals and 95% intervals, although any percentage may be used. Table5.1gives the value of\(c\)for a range of coverage probabilities assuming a normal forecast distribution.


The value of prediction intervals is that they express the uncertainty in the forecasts. If we only produce point forecasts, there is no way of telling how accurate the forecasts are. However, if we also produce prediction intervals, then it is clear how much uncertainty is associated with each forecast. For this reason, point forecasts can be of almost no value without the accompanying prediction intervals.


### One-step prediction intervals


When forecasting one step ahead, the standard deviation of the forecast distribution can be estimated using the standard deviation of the residuals given by\[\begin{equation}
  \hat{\sigma} = \sqrt{\frac{1}{T-K-M}\sum_{t=1}^T e_t^2}, \tag{5.1}
\end{equation}\]where\(K\)is the number of parameters estimated in the forecasting method, and\(M\)is the number of missing values in the residuals. (For example,\(M=1\)for a naive forecast, because we can’t forecast the first observation.)


For example, consider a naïve forecast for the Google stock price datagoogle_2015(shown in Figure5.8). The last value of the observed series is 758.88, so the forecast of the next value of the price is 758.88. The standard deviation of the residuals from the naïve method, as given by Equation(5.1), is 11.19. Hence, a 95% prediction interval for the next value of the GSP is\[
  758.88 \pm 1.96(11.19) = [736.9, 780.8].
\]Similarly, an 80% prediction interval is given by\[
  758.88 \pm 1.28(11.19) = [744.5, 773.2].
\]


The value of the multiplier (1.96 or 1.28) is taken from Table5.1.


### Multi-step prediction intervals


A common feature of prediction intervals is that they usually increase in length as the forecast horizon increases. The further ahead we forecast, the more uncertainty is associated with the forecast, and thus the wider the prediction intervals. That is,\(\sigma_h\)usually increases with\(h\)(although there are some non-linear forecasting methods which do not have this property).


To produce a prediction interval, it is necessary to have an estimate of\(\sigma_h\). As already noted, for one-step forecasts (\(h=1\)), Equation(5.1)provides a good estimate of the forecast standard deviation\(\sigma_1\). For multi-step forecasts, a more complicated method of calculation is required. These calculations assume that the residuals are uncorrelated.


### Benchmark methods


For the four benchmark methods, it is possible to mathematically derive the forecast standard deviation under the assumption of uncorrelated residuals. If\(\hat{\sigma}_h\)denotes the standard deviation of the\(h\)-step forecast distribution, and\(\hat{\sigma}\)is the residual standard deviation given by(5.1), then we can use the expressions shown in Table5.2. Note that when\(h=1\)and\(T\)is large, these all give the same approximate value\(\hat\sigma\).


Prediction intervals can easily be computed for you when using thefablepackage. For example, here is the output when using the naïve method for the Google stock price.


```
google_2015 |>
  model(NAIVE(Close)) |>
  forecast(h = 10) |>
  hilo()
#> # A tsibble: 10 x 7 [1]
#> # Key:       Symbol, .model [1]
#>    Symbol .model         day
#>    <chr>  <chr>        <dbl>
#>  1 GOOG   NAIVE(Close)   253
#>  2 GOOG   NAIVE(Close)   254
#>  3 GOOG   NAIVE(Close)   255
#>  4 GOOG   NAIVE(Close)   256
#>  5 GOOG   NAIVE(Close)   257
#>  6 GOOG   NAIVE(Close)   258
#>  7 GOOG   NAIVE(Close)   259
#>  8 GOOG   NAIVE(Close)   260
#>  9 GOOG   NAIVE(Close)   261
#> 10 GOOG   NAIVE(Close)   262
#> # ℹ 4 more variables: Close <dist>, .mean <dbl>, `80%` <hilo>, `95%` <hilo>
```


Thehilo()function converts the forecast distributions into intervals. By default, 80% and 95% prediction intervals are returned, although other options are possible via thelevelargument.


When plotted, the prediction intervals are shown as shaded regions, with the strength of colour indicating the probability associated with the interval. Again, 80% and 95% intervals are shown by default, with other options available via thelevelargument.


```
google_2015 |>
  model(NAIVE(Close)) |>
  forecast(h = 10) |>
  autoplot(google_2015) +
  labs(title="Google daily closing stock price", y="$US" )
```


Figure 5.14: 80% and 95% prediction intervals for the Google closing stock price based on a naïve method.


### Prediction intervals from bootstrapped residuals


When a normal distribution for the residuals is an unreasonable assumption, one alternative is to use bootstrapping, which only assumes that the residuals are uncorrelated with constant variance. We will illustrate the procedure using a naïve forecasting method.


A one-step forecast error is defined as\(e_t = y_t - \hat{y}_{t|t-1}\). For a naïve forecasting method,\(\hat{y}_{t|t-1} = y_{t-1}\), so we can rewrite this as\[
  y_t = y_{t-1} + e_t.
\]Assuming future errors will be similar to past errors, when\(t>T\)we can replace\(e_{t}\)by sampling from the collection of errors we have seen in the past (i.e., the residuals). So we can simulate the next observation of a time series using\[
  y^*_{T+1} = y_{T} + e^*_{T+1}
\]where\(e^*_{T+1}\)is a randomly sampled error from the past, and\(y^*_{T+1}\)is the possible future value that would arise if that particular error value occurred. We use a * to indicate that this is not the observed\(y_{T+1}\)value, but one possible future that could occur. Adding the new simulated observation to our data set, we can repeat the process to obtain\[
  y^*_{T+2} = y_{T+1}^* + e^*_{T+2},
\]where\(e^*_{T+2}\)is another draw from the collection of residuals. Continuing in this way, we can simulate an entire set of future values for our time series.


Doing this repeatedly, we obtain many possible futures. To see some of them, we can use thegenerate()function.


```
fit <- google_2015 |>
  model(NAIVE(Close))
sim <- fit |> generate(h = 30, times = 5, bootstrap = TRUE)
sim
#> # A tsibble: 150 x 5 [1]
#> # Key:       Symbol, .model, .rep [5]
#>    Symbol .model         day .rep   .sim
#>    <chr>  <chr>        <dbl> <chr> <dbl>
#>  1 GOOG   NAIVE(Close)   253 1      756.
#>  2 GOOG   NAIVE(Close)   254 1      749.
#>  3 GOOG   NAIVE(Close)   255 1      751.
#>  4 GOOG   NAIVE(Close)   256 1      750.
#>  5 GOOG   NAIVE(Close)   257 1      754.
#>  6 GOOG   NAIVE(Close)   258 1      754.
#>  7 GOOG   NAIVE(Close)   259 1      758.
#>  8 GOOG   NAIVE(Close)   260 1      763.
#>  9 GOOG   NAIVE(Close)   261 1      759.
#> 10 GOOG   NAIVE(Close)   262 1      748.
#> # ℹ 140 more rows
```


Here we have generated five possible sample paths for the next 30 trading days. The.repvariable provides a new key for the tsibble. The plot below shows the five sample paths along with the historical data.


```
google_2015 |>
  ggplot(aes(x = day)) +
  geom_line(aes(y = Close)) +
  geom_line(aes(y = .sim, colour = as.factor(.rep)),
    data = sim) +
  labs(title="Google daily closing stock price", y="$US" ) +
  guides(colour = "none")
```


Figure 5.15: Five simulated future sample paths of the Google closing stock price based on a naïve method with bootstrapped residuals.


Then we can compute prediction intervals by calculating percentiles of the future sample paths for each forecast horizon. The result is called abootstrappedprediction interval. The name “bootstrap” is a reference to pulling ourselves up by our bootstraps, because the process allows us to measure future uncertainty by only using the historical data.


This is all built into theforecast()function so you do not need to callgenerate()directly.


```
fc <- fit |> forecast(h = 30, bootstrap = TRUE)
fc
#> # A fable: 30 x 5 [1]
#> # Key:     Symbol, .model [1]
#>    Symbol .model         day        Close .mean
#>    <chr>  <chr>        <dbl>       <dist> <dbl>
#>  1 GOOG   NAIVE(Close)   253 sample[5000]  759.
#>  2 GOOG   NAIVE(Close)   254 sample[5000]  759.
#>  3 GOOG   NAIVE(Close)   255 sample[5000]  758.
#>  4 GOOG   NAIVE(Close)   256 sample[5000]  759.
#>  5 GOOG   NAIVE(Close)   257 sample[5000]  759.
#>  6 GOOG   NAIVE(Close)   258 sample[5000]  759.
#>  7 GOOG   NAIVE(Close)   259 sample[5000]  759.
#>  8 GOOG   NAIVE(Close)   260 sample[5000]  759.
#>  9 GOOG   NAIVE(Close)   261 sample[5000]  759.
#> 10 GOOG   NAIVE(Close)   262 sample[5000]  759.
#> # ℹ 20 more rows
```


Notice that the forecast distribution is now represented as a simulation with 5000 sample paths. Because there is no normality assumption, the prediction intervals are not symmetric. The.meancolumn is the mean of the bootstrap samples, so it may be slightly different from the results obtained without a bootstrap.


```
autoplot(fc, google_2015) +
  labs(title="Google daily closing stock price", y="$US" )
```


Figure 5.16: Forecasts of the Google closing stock price based on a naïve method with bootstrapped residuals.


The number of samples can be controlled using thetimesargument forforecast().
For example, intervals based on 1000 bootstrap samples can be sampled with:


```
google_2015 |>
  model(NAIVE(Close)) |>
  forecast(h = 10, bootstrap = TRUE, times = 1000) |>
  hilo()
#> # A tsibble: 10 x 7 [1]
#> # Key:       Symbol, .model [1]
#>    Symbol .model      day        Close .mean            `80%`            `95%`
#>    <chr>  <chr>     <dbl>       <dist> <dbl>           <hilo>           <hilo>
#>  1 GOOG   NAIVE(Cl…   253 sample[1000]  760. [748.2, 770.8]80 [743.9, 777.6]95
#>  2 GOOG   NAIVE(Cl…   254 sample[1000]  760. [743.9, 776.1]80 [734.1, 801.6]95
#>  3 GOOG   NAIVE(Cl…   255 sample[1000]  760. [739.5, 781.7]80 [728.6, 809.0]95
#>  4 GOOG   NAIVE(Cl…   256 sample[1000]  760. [736.7, 784.7]80 [723.4, 813.1]95
#>  5 GOOG   NAIVE(Cl…   257 sample[1000]  760. [734.4, 787.2]80 [719.4, 819.7]95
#>  6 GOOG   NAIVE(Cl…   258 sample[1000]  760. [731.5, 790.2]80 [717.8, 820.3]95
#>  7 GOOG   NAIVE(Cl…   259 sample[1000]  761. [730.4, 793.0]80 [713.0, 826.3]95
#>  8 GOOG   NAIVE(Cl…   260 sample[1000]  761. [726.2, 796.2]80 [706.3, 830.7]95
#>  9 GOOG   NAIVE(Cl…   261 sample[1000]  761. [723.5, 800.2]80 [707.5, 841.0]95
#> 10 GOOG   NAIVE(Cl…   262 sample[1000]  760. [719.2, 801.8]80 [701.9, 841.4]95
```


In this case, they are similar (but not identical) to the prediction intervals based on the normal distribution.


Use the slider below to see the effect of varying the number of bootstrap samples (times) on the forecast distribution:
