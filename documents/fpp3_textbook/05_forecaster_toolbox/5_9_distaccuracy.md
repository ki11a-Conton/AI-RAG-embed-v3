
# Forecasting: Principles and Practice(3rd ed)


## 5.9Evaluating distributional forecast accuracy


The preceding measures all measure point forecast accuracy. When evaluating distributional forecasts, we need to use some other measures.


### Quantile scores


Consider the Google stock price example from the previous section. Figure5.23shows an 80% prediction interval for the forecasts from the naïve method.


```
google_fc |>
  filter(.model == "Naïve") |>
  autoplot(bind_rows(google_2015, google_jan_2016), level=80)+
  labs(y = "$US",
       title = "Google closing stock prices")
```


Figure 5.23: Naïve forecasts of the Google stock price for Jan 2016, along with 80% prediction intervals.


The lower limit of this prediction interval gives the 10th percentile (or 0.1 quantile) of the forecast distribution, so we would expect the actual value to lie below the lower limit about 10% of the time, and to lie above the lower limit about 90% of the time. When we compare the actual value to this percentile, we need to allow for the fact that it is more likely to be above than below.


More generally, suppose we are interested in the quantile forecast with probability\(p\)at future time\(t\), and let this be denoted by\(f_{p,t}\). That is, we expect the observation\(y_t\)to be less than\(f_{p,t}\)with probability\(p\). For example, the 10th percentile would be\(f_{0.10,t}\). If\(y_{t}\)denotes the observation at time\(t\), then theQuantile Scoreis\[
  Q_{p,t} = \begin{cases}
  2(1 - p) \big(f_{p,t} - y_{t}\big), & \text{if $y_{t} < f_{p,t}$}\\
  2p \big(y_{t} - f_{p,t}\big), & \text{if $y_{t} \ge f_{p,t}$} \end{cases}
\]This is sometimes called the “pinball loss function” because a graph of it resembles the trajectory of a ball on a pinball table. The multiplier of 2 is often omitted, but including it makes the interpretation a little easier. A low value of\(Q_{p,t}\)indicates a better estimate of the quantile.


The quantile score can be interpreted like an absolute error. In fact, when\(p=0.5\), the quantile score\(Q_{0.5,t}\)is the same as the absolute error. For other values of\(p\), the “error”\((y_t - f_{p,t})\)is weighted to take account of how likely it is to be positive or negative. If\(p>0.5\),\(Q_{p,t}\)gives a heavier penalty when the observation is greater than the estimated quantile than when the observation is less than the estimated quantile. The reverse is true for\(p<0.5\).


In Figure5.23, the one-step-ahead 10% quantile forecast (for 4 January 2016) is\(f_{0.1,t} = 744.54\)and the observed value is\(y_t = 741.84\). Then\[
  Q_{0.1,t} = 2(1-0.1) (744.54 - 741.84) = 4.86.
\]This is easily computed usingaccuracy()with thequantile_score()function:


```
google_fc |>
  filter(.model == "Naïve", Date == "2016-01-04") |>
  accuracy(google_stock, list(qs=quantile_score), probs=0.10)
#> # A tibble: 1 × 4
#>   .model Symbol .type    qs
#>   <chr>  <chr>  <chr> <dbl>
#> 1 Naïve  GOOG   Test   4.86
```


### Winkler Score


It is often of interest to evaluate a prediction interval, rather than a few quantiles, and the Winkler score proposed byWinkler (1972)is designed for this purpose. If the\(100(1-\alpha)\)% prediction interval at time\(t\)is given by\([\ell_{\alpha,t}, u_{\alpha,t}]\), then the Winkler score is defined as the length of the interval plus a penalty if the observation is outside the interval:\[
  W_{\alpha,t} = \begin{cases}
  (u_{\alpha,t} - \ell_{\alpha,t}) + \frac{2}{\alpha} (\ell_{\alpha,t} - y_t) & \text{if } y_t < \ell_{\alpha,t} \\
  (u_{\alpha,t} - \ell_{\alpha,t})   & \text{if }  \ell_{\alpha,t} \le y_t \le u_{\alpha,t} \\
  (u_{\alpha,t} - \ell_{\alpha,t}) + \frac{2}{\alpha} (y_t - u_{\alpha,t}) & \text{if } y_t > u_{\alpha,t}.
  \end{cases}
\]For observations that fall within the interval, the Winkler score is simply the length of the interval. Thus, low scores are associated with narrow intervals. However, if the observation falls outside the interval, the penalty applies, with the penalty proportional to how far the observation is outside the interval.


Prediction intervals are usually constructed from quantiles by setting\(\ell_{\alpha,t} = f_{\alpha/2,t}\)and\(u_{\alpha,t} = f_{1-\alpha/2,t}\). If we add the corresponding quantile scores and divide by\(\alpha\), we get the Winkler score:\[
  W_{\alpha,t} = (Q_{\alpha/2,t} + Q_{1-\alpha/2,t})/\alpha.
\]


The one-step-ahead 80% interval shown in Figure5.23for 4 January 2016 is [744.54, 773.22], and the actual value was 741.84, so the Winkler score is\[
  W_{\alpha,t} = (773.22 - 744.54) + \frac{2}{0.2} (744.54 - 741.84)  =
   55.68.
\]This is easily computed usingaccuracy()with thewinkler_score()function:


```
google_fc |>
  filter(.model == "Naïve", Date == "2016-01-04") |>
  accuracy(google_stock,
    list(winkler = winkler_score), level = 80)
#> # A tibble: 1 × 4
#>   .model Symbol .type winkler
#>   <chr>  <chr>  <chr>   <dbl>
#> 1 Naïve  GOOG   Test     55.7
```


### Continuous Ranked Probability Score


Often we are interested in the whole forecast distribution, rather than particular quantiles or prediction intervals. In that case, we can average the quantile scores over all values of\(p\)to obtain theContinuous Ranked Probability Scoreor CRPS(Gneiting & Katzfuss, 2014).


In the Google stock price example, we can compute the average CRPS value for all days in the test set. A CRPS value is a little like a weighted absolute error computed from the entire forecast distribution, where the weighting takes account of the probabilities.


```
google_fc |>
  accuracy(google_stock, list(crps = CRPS))
#> # A tibble: 3 × 4
#>   .model Symbol .type  crps
#>   <chr>  <chr>  <chr> <dbl>
#> 1 Drift  GOOG   Test   33.5
#> 2 Mean   GOOG   Test   76.7
#> 3 Naïve  GOOG   Test   26.5
```


Here, the naïve method is giving better distributional forecasts than the drift or mean methods.


### Scale-free comparisons using skill scores


As with point forecasts, it is useful to be able to compare the distributional forecast accuracy of several methods across series on different scales. For point forecasts, we used scaled errors for that purpose. Another approach is to use skill scores. These can be used for both point forecast accuracy and distributional forecast accuracy.


With skill scores, we compute a forecast accuracy measure relative to some benchmark method. For example, if we use the naïve method as a benchmark, and also compute forecasts using the drift method, we can compute the CRPS skill score of the drift method relative to the naïve method as\[
\frac{\text{CRPS}_{\text{Naïve}} - \text{CRPS}_{\text{Drift}}}{\text{CRPS}_{\text{Naïve}}}.
\]This gives the proportion that the drift method improves over the naïve method based on CRPS. It is easy to compute using theaccuracy()function.


```
google_fc |>
  accuracy(google_stock, list(skill = skill_score(CRPS)))
#> # A tibble: 3 × 4
#>   .model Symbol .type  skill
#>   <chr>  <chr>  <chr>  <dbl>
#> 1 Drift  GOOG   Test  -0.266
#> 2 Mean   GOOG   Test  -1.90 
#> 3 Naïve  GOOG   Test   0
```


Of course, the skill score for the naïve method is 0 because it can’t improve on itself. The other two methods have larger CRPS values than naïve, so the skills scores are negative; the drift method is 26.6% worse than the naïve method.


Theskill_score()function will always compute the CRPS for the appropriate benchmark forecasts, even if these are not included in thefableobject. When the data are seasonal, the benchmark used is the seasonal naïve method rather than the naïve method. To ensure that the same training data are used for the benchmark forecasts, it is important that the data provided to theaccuracy()function starts at the same time as the training data.


Theskill_score()function can be used with any accuracy measure. For example,skill_score(MSE)provides a way of comparing MSE values across diverse series. However, it is important that the test set is large enough to allow reliable calculation of the error measure, especially in the denominator. For that reason, MASE or RMSSE are often preferable scale-free measures for point forecast accuracy.


### Bibliography
