
# Forecasting: Principles and Practice(3rd ed)


## 9.5Non-seasonal ARIMA models


If we combine differencing with autoregression and a moving average model, we obtain a non-seasonal ARIMA model. ARIMA is an acronym for AutoRegressive Integrated Moving Average (in this context, “integration” is the reverse of differencing). The full model can be written as\[\begin{equation}
  y'_{t} = c + \phi_{1}y'_{t-1} + \cdots + \phi_{p}y'_{t-p}
     + \theta_{1}\varepsilon_{t-1} + \cdots + \theta_{q}\varepsilon_{t-q} + \varepsilon_{t},  \tag{9.1}
\end{equation}\]where\(y'_{t}\)is the differenced series (it may have been differenced more than once). The “predictors” on the right hand side include both lagged values of\(y_t\)and lagged errors. We call this anARIMA(\(p, d, q\)) model, where


The same stationarity and invertibility conditions that are used for autoregressive and moving average models also apply to an ARIMA model.


Many of the models we have already discussed are special cases of the ARIMA model, as shown in Table9.1.


Once we start combining components in this way to form more complicated models, it is much easier to work with the backshift notation. For example, Equation(9.1)can be written in backshift notation as\[\begin{equation}
\tag{9.2}
  \begin{array}{c c c c}
    (1-\phi_1B - \cdots - \phi_p B^p) & (1-B)^d y_{t} &= &c + (1 + \theta_1 B + \cdots + \theta_q B^q)\varepsilon_t\\
    {\uparrow} & {\uparrow} & &{\uparrow}\\
    \text{AR($p$)} & \text{$d$ differences} & & \text{MA($q$)}\\
  \end{array}
\end{equation}\]


Selecting appropriate values for\(p\),\(d\)and\(q\)can be difficult. However, theARIMA()function from thefablepackage will do it for you automatically. In Section9.7, we will learn how this function works, along with some methods for choosing these values yourself.


### Example: Egyptian exports


Figure9.7shows Egyptian exports as a percentage of GDP from 1960 to 2017.


```
global_economy |>
  filter(Code == "EGY") |>
  autoplot(Exports) +
  labs(y = "% of GDP", title = "Egyptian exports")
```


Figure 9.7: Annual Egyptian exports as a percentage of GDP since 1960.


The following R code selects a non-seasonal ARIMA model automatically.


```
fit <- global_economy |>
  filter(Code == "EGY") |>
  model(ARIMA(Exports))
report(fit)
#> Series: Exports 
#> Model: ARIMA(2,0,1) w/ mean 
#> 
#> Coefficients:
#>          ar1      ar2      ma1  constant
#>       1.6764  -0.8034  -0.6896    2.5623
#> s.e.  0.1111   0.0928   0.1492    0.1161
#> 
#> sigma^2 estimated as 8.046:  log likelihood=-141.6
#> AIC=293.1   AICc=294.3   BIC=303.4
```


This is an ARIMA(2,0,1) model:\[
  y_t = 2.56
         + 1.68 y_{t-1}
          -0.80 y_{t-2}
          -0.69 \varepsilon_{t-1}
          + \varepsilon_{t},
\]where\(\varepsilon_t\)is white noise with a standard deviation of\(2.837 = \sqrt{8.046}\). Forecasts from the model are shown in Figure9.8. Notice how they have picked up the cycles evident in the Egyptian economy over the last few decades.


```
fit |> forecast(h=10) |>
  autoplot(global_economy) +
  labs(y = "% of GDP", title = "Egyptian exports")
```


Figure 9.8: Forecasts of Egyptian exports.


### Understanding ARIMA models


TheARIMA()function is useful, but anything automated can be a little dangerous, and it is worth understanding something of the behaviour of the models even when you rely on an automatic procedure to choose the model for you.


The constant\(c\)has an important effect on the long-term forecasts obtained from these models.

- If\(c=0\)and\(d=0\), the long-term forecasts will go to zero.
- If\(c=0\)and\(d=1\), the long-term forecasts will go to a non-zero constant.
- If\(c=0\)and\(d=2\), the long-term forecasts will follow a straight line.
- If\(c\ne0\)and\(d=0\), the long-term forecasts will go to the mean of the data.
- If\(c\ne0\)and\(d=1\), the long-term forecasts will follow a straight line.
- If\(c\ne0\)and\(d=2\), the long-term forecasts will follow a quadratic trend. (This is not recommended, andfablewill not permit it.)

The value of\(d\)also has an effect on the prediction intervals — the higher the value of\(d\), the more rapidly the prediction intervals increase in size. For\(d=0\), the long-term forecast standard deviation will go to the standard deviation of the historical data, so the prediction intervals will all be essentially the same.


This behaviour is seen in Figure9.8where\(d=0\)and\(c\ne0\). In this figure, the prediction intervals are almost the same width for the last few forecast horizons, and the final point forecasts are close to the mean of the data.


The value of\(p\)is important if the data show cycles. To obtain cyclic forecasts, it is necessary to have\(p\ge2\), along with some additional conditions on the parameters. For an AR(2) model, cyclic behaviour occurs if\(\phi_1^2+4\phi_2<0\)(as is the case for the Egyptian exports model). In that case, the average period of the cycles is19\[
  \frac{2\pi}{\text{arc cos}(-\phi_1(1-\phi_2)/(4\phi_2))}.
\]


### ACF and PACF plots


It is usually not possible to tell, simply from a time plot, what values of\(p\)and\(q\)are appropriate for the data. However, it is sometimes possible to use the ACF plot, and the closely related PACF plot, to determine appropriate values for\(p\)and\(q\).


Recall that an ACF plot shows the autocorrelations which measure the relationship between\(y_t\)and\(y_{t-k}\)for different values of\(k\). Now if\(y_t\)and\(y_{t-1}\)are correlated, then\(y_{t-1}\)and\(y_{t-2}\)must also be correlated. However, then\(y_t\)and\(y_{t-2}\)might be correlated, simply because they are both connected to\(y_{t-1}\), rather than because of any new information contained in\(y_{t-2}\)that could be used in forecasting\(y_t\).


To overcome this problem, we can usepartial autocorrelations. These measure the relationship between\(y_{t}\)and\(y_{t-k}\)after removing the effects of lags\(1, 2, 3, \dots, k - 1\). So the first partial autocorrelation is identical to the first autocorrelation, because there is nothing between them to remove. Each partial autocorrelation can be estimated as the last coefficient in an autoregressive model. Specifically,\(\alpha_k\), the\(k\)th partial autocorrelation coefficient, is equal to the estimate of\(\phi_k\)in an AR(\(k\)) model. In practice, there are more efficient algorithms for computing\(\alpha_k\)than fitting all of these autoregressions, but they give the same results.


Figures9.9and9.10shows the ACF and PACF plots for the Egyptian exports data shown in Figure9.7. The partial autocorrelations have the same critical values of\(\pm 1.96/\sqrt{T}\)as for ordinary autocorrelations, and these are typically shown on the plot as in Figure9.10.


```
global_economy |>
  filter(Code == "EGY") |>
  ACF(Exports) |>
  autoplot()
```


Figure 9.9: ACF of Egyptian exports.


```
global_economy |>
  filter(Code == "EGY") |>
  PACF(Exports) |>
  autoplot()
```


Figure 9.10: PACF of Egyptian exports.


A convenient way to produce a time plot, ACF plot and PACF plot in one command is to use thegg_tsdisplay()function withplot_type = "partial".


If the data are from an ARIMA(\(p\),\(d\),0) or ARIMA(0,\(d\),\(q\)) model, then the ACF and PACF plots can be helpful in determining the value of\(p\)or\(q\). If\(p\)and\(q\)are both positive, then the plots do not help in finding suitable values of\(p\)and\(q\).


The data may follow an ARIMA(\(p\),\(d\),0) model if the ACF and PACF plots of the differenced data show the following patterns:

- the ACF is exponentially decaying or sinusoidal;
- there is a significant spike at lag\(p\)in the PACF, but none beyond lag\(p\).

The data may follow an ARIMA(0,\(d\),\(q\)) model if the ACF and PACF plots of the differenced data show the following patterns:

- the PACF is exponentially decaying or sinusoidal;
- there is a significant spike at lag\(q\)in the ACF, but none beyond lag\(q\).

In Figure9.9, we see that there is a decaying sinusoidal pattern in the ACF, and in Figure9.10the PACF shows the last significant spike at lag 4. This is what you would expect from an ARIMA(4,0,0) model.


```
fit2 <- global_economy |>
  filter(Code == "EGY") |>
  model(ARIMA(Exports ~ pdq(4,0,0)))
report(fit2)
#> Series: Exports 
#> Model: ARIMA(4,0,0) w/ mean 
#> 
#> Coefficients:
#>          ar1      ar2     ar3      ar4  constant
#>       0.9861  -0.1715  0.1807  -0.3283    6.6922
#> s.e.  0.1247   0.1865  0.1865   0.1273    0.3562
#> 
#> sigma^2 estimated as 7.885:  log likelihood=-140.5
#> AIC=293.1   AICc=294.7   BIC=305.4
```


This model is only slightly worse than the ARIMA(2,0,1) model identified byARIMA()(with an AICc value of 294.70 compared to 294.29).


We can also specify particular values ofpdq()thatARIMA()can search for. For example, to find the best ARIMA model with\(p\in\{1,2,3\}\),\(q\in\{0,1,2\}\)and\(d=1\), you could useARIMA(y ~ pdq(p=1:3, d=1, q=0:2)).

- arc cos is the inverse cosine function. You should be able to find it on your calculator. It may be labelled acos or cos\(^{-1}\).↩︎

arc cos is the inverse cosine function. You should be able to find it on your calculator. It may be labelled acos or cos\(^{-1}\).↩︎
