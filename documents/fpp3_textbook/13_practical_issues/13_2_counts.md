
# Forecasting: Principles and Practice(3rd ed)


## 13.2Time series of counts


All of the methods discussed in this book assume that the data have a continuous sample space. But often data comes in the form of counts. For example, we may wish to forecast the number of customers who enter a store each day. We could have\(0, 1, 2, \dots\), customers, but we cannot have 3.45693 customers.


In practice, this rarely matters provided our counts are sufficiently large. If the minimum number of customers is at least 100, then the difference between a continuous sample space\([100,\infty)\)and the discrete sample space\(\{100,101,102,\dots\}\)has no perceivable effect on our forecasts. However, if our data contains small counts\((0, 1, 2, \dots)\), then we need to use forecasting methods that are more appropriate for a sample space of non-negative integers.


Such models are beyond the scope of this book. However, there is one simple method which gets used in this context, that we would like to mention. It is “Croston’s method”, named after its British inventor, John Croston, and first described inCroston (1972). Actually, this method does not properly deal with the count nature of the data either, but it is used so often, that it is worth knowing about it.


With Croston’s method, we construct two new series from our original time series by noting which time periods contain zero values, and which periods contain non-zero values. Let\(q_i\)be the\(i\)th non-zero quantity, and let\(a_i\)be the time between\(q_{i-1}\)and\(q_i\). Croston’s method involves separate simple exponential smoothing forecasts on the two new series\(a\)and\(q\). Because the method is usually applied to time series of demand for items,\(q\)is often called the “demand” and\(a\)the “inter-arrival time”.


If\(\hat{q}_{i+1|i}\)and\(\hat{a}_{i+1|i}\)are the one-step forecasts of the\((i+1)\)th demand and inter-arrival time respectively, based on data up to demand\(i\), then Croston’s method gives\[\begin{align}
  \hat{q}_{i+1|i} & = (1-\alpha_q)\hat{q}_{i|i-1} + \alpha_q q_i, \tag{13.1}\\
  \hat{a}_{i+1|i} & = (1-\alpha_a)\hat{a}_{i|i-1} + \alpha_a a_i. \tag{13.2}
\end{align}\]The smoothing parameters\(\alpha_a\)and\(\alpha_q\)take values between 0 and 1. Let\(j\)be the time for the last observed positive observation. Then the\(h\)-step ahead forecast for the demand at time\(T+h\), is given by the ratio\[
  \hat{y}_{T+h|T} = \hat{q}_{j+1|j}/\hat{a}_{j+1|j}.
\]There are no algebraic results allowing us to compute prediction intervals for this method, because the method does not correspond to any statistical model(Shenstone & Hyndman, 2005). Forecasts obtained from Croston’s method are also known to be biased(Syntetos & Boylan, 2001).


TheCROSTON()function produces forecasts using Croston’s method. The two smoothing parameters\(\alpha_a\)and\(\alpha_q\)are estimated from the data. This is different from the way Croston envisaged the method being used. He would simply use\(\alpha_a=\alpha_q=0.1\), and set\(a_0\)and\(q_0\)to be equal to the first observation in each of the series.


### Example: Pharmaceutical sales


Figure13.3shows the numbers of scripts sold each month for immune sera and immunoglobulin products in Australia. The data contain small counts, with many months registering no sales at all, and only small numbers of items sold in other months.


```
j06 <- PBS |>
  filter(ATC2 == "J06") |>
  summarise(Scripts = sum(Scripts))

j06 |> autoplot(Scripts) +
  labs(y="Number of scripts",
       title = "Sales for immune sera and immunoglobulins")
```


Figure 13.3: Numbers of scripts sold for Immune sera and immunoglobulins on the Australian Pharmaceutical Benefits Scheme.


Tables13.1and13.2shows the first 10 non-zero demand values, with their corresponding inter-arrival times.


In this example, the smoothing parameters are estimated to be\(\alpha_a = 0.08\),\(\alpha_q = 0.71\),\(\hat{q}_{1|0}=4.17\), and\(\hat{a}_{1|0}=3.52\). The final forecasts for the two series are\(\hat{q}_{T+1|T} = 2.419\)and\(\hat{a}_{T+1|T} = 2.484\). So the forecasts are all equal to\(\hat{y}_{T+h|T} = 2.419/2.484 = 0.974\).


In practice,fabledoes these calculations for you:


```
j06 |>
  model(CROSTON(Scripts)) |>
  forecast(h = 6)
#> # A fable: 6 x 4 [1M]
#> # Key:     .model [1]
#>   .model              Month Scripts .mean
#>   <chr>               <mth>  <dist> <dbl>
#> 1 CROSTON(Scripts) 2008 Jul  0.9735 0.974
#> 2 CROSTON(Scripts) 2008 Aug  0.9735 0.974
#> 3 CROSTON(Scripts) 2008 Sep  0.9735 0.974
#> 4 CROSTON(Scripts) 2008 Oct  0.9735 0.974
#> 5 CROSTON(Scripts) 2008 Nov  0.9735 0.974
#> 6 CROSTON(Scripts) 2008 Dec  0.9735 0.974
```


TheScriptscolumn repeats the mean rather than provide a full distribution, because there is no underlying stochastic model.


Forecasting models that deal more directly with the count nature of the data, and allow for a forecasting distribution, are described inChristou & Fokianos (2015).


### Bibliography
