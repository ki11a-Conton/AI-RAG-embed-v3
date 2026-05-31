
# Forecasting: Principles and Practice(3rd ed)


## 8.3Methods with seasonality


Holt (1957)andWinters (1960)extended Holt’s method to capture seasonality. The Holt-Winters seasonal method comprises the forecast equation and three smoothing equations — one for the level\(\ell_t\), one for the trend\(b_t\), and one for the seasonal component\(s_t\), with corresponding smoothing parameters\(\alpha\),\(\beta^*\)and\(\gamma\). We use\(m\)to denote the period of the seasonality, i.e., the number of seasons in a year. For example, for quarterly data\(m=4\), and for monthly data\(m=12\).


There are two variations to this method that differ in the nature of the seasonal component. The additive method is preferred when the seasonal variations are roughly constant through the series, while the multiplicative method is preferred when the seasonal variations are changing proportional to the level of the series. With the additive method, the seasonal component is expressed in absolute terms in the scale of the observed series, and in the level equation the series is seasonally adjusted by subtracting the seasonal component. Within each year, the seasonal component will add up to approximately zero. With the multiplicative method, the seasonal component is expressed in relative terms (percentages), and the series is seasonally adjusted by dividing through by the seasonal component. Within each year, the seasonal component will sum up to approximately\(m\).


### Holt-Winters’ additive method


The component form for the additive method is:\[\begin{align*}
  \hat{y}_{t+h|t} &= \ell_{t} + hb_{t} + s_{t+h-m(k+1)} \\
  \ell_{t} &= \alpha(y_{t} - s_{t-m}) + (1 - \alpha)(\ell_{t-1} + b_{t-1})\\
  b_{t} &= \beta^*(\ell_{t} - \ell_{t-1}) + (1 - \beta^*)b_{t-1}\\
  s_{t} &= \gamma (y_{t}-\ell_{t-1}-b_{t-1}) + (1-\gamma)s_{t-m},
\end{align*}\]where\(k\)is the integer part of\((h-1)/m\), which ensures that the estimates of the seasonal indices used for forecasting come from the final year of the sample. The level equation shows a weighted average between the seasonally adjusted observation\((y_{t} - s_{t-m})\)and the non-seasonal forecast\((\ell_{t-1}+b_{t-1})\)for time\(t\). The trend equation is identical to Holt’s linear method. The seasonal equation shows a weighted average between the current seasonal index,\((y_{t}-\ell_{t-1}-b_{t-1})\), and the seasonal index of the same season last year (i.e.,\(m\)time periods ago).


The equation for the seasonal component is often expressed as\[
s_{t} = \gamma^* (y_{t}-\ell_{t})+ (1-\gamma^*)s_{t-m}.
\]If we substitute\(\ell_t\)from the smoothing equation for the level of the component form above, we get\[
s_{t} = \gamma^*(1-\alpha) (y_{t}-\ell_{t-1}-b_{t-1})+ [1-\gamma^*(1-\alpha)]s_{t-m},
\]which is identical to the smoothing equation for the seasonal component we specify here, with\(\gamma=\gamma^*(1-\alpha)\). The usual parameter restriction is\(0\le\gamma^*\le1\), which translates to\(0\le\gamma\le 1-\alpha\).


### Holt-Winters’ multiplicative method


The component form for the multiplicative method is:\[\begin{align*}
  \hat{y}_{t+h|t} &= (\ell_{t} + hb_{t})s_{t+h-m(k+1)} \\
  \ell_{t} &= \alpha \frac{y_{t}}{s_{t-m}} + (1 - \alpha)(\ell_{t-1} + b_{t-1})\\
  b_{t} &= \beta^*(\ell_{t}-\ell_{t-1}) + (1 - \beta^*)b_{t-1}                \\
  s_{t} &= \gamma \frac{y_{t}}{(\ell_{t-1} + b_{t-1})} + (1 - \gamma)s_{t-m}.
\end{align*}\]


### Example: Domestic overnight trips in Australia


We apply Holt-Winters’ method with both additive and multiplicative seasonality17to forecast quarterly visitor nights in Australia spent by domestic tourists. Figure8.7shows the data from 1998–2017, and the forecasts for 2018–2020. The data show an obvious seasonal pattern, with peaks observed in the March quarter of each year, corresponding to the Australian summer.


```
aus_holidays <- tourism |>
  filter(Purpose == "Holiday") |>
  summarise(Trips = sum(Trips)/1e3)
fit <- aus_holidays |>
  model(
    additive = ETS(Trips ~ error("A") + trend("A") +
                                                season("A")),
    multiplicative = ETS(Trips ~ error("M") + trend("A") +
                                                season("M"))
  )
fc <- fit |> forecast(h = "3 years")
fc |>
  autoplot(aus_holidays, level = NULL) +
  labs(title="Australian domestic tourism",
       y="Overnight trips (millions)") +
  guides(colour = guide_legend(title = "Forecast"))
```


Figure 8.7: Forecasting domestic overnight trips in Australia using the Holt-Winters method with both additive and multiplicative seasonality.


The applications of both methods (with additive and multiplicative seasonality) are presented in Tables8.3and8.4respectively. Because both methods have exactly the same number of parameters to estimate, we can compare the training RMSE from both models. In this case, the method with multiplicative seasonality fits the data slightly better.


The estimated components for both models are plotted in Figure8.8. The small value of\(\gamma\)for the multiplicative model means that the seasonal component hardly changes over time. The small value of\(\beta^{*}\)means the slope component hardly changes over time (compare the vertical scales of the slope and level components).


Figure 8.8: Estimated components for the Holt-Winters method with additive and multiplicative seasonal components.


### Holt-Winters’ damped method


Damping is possible with both additive and multiplicative Holt-Winters’ methods. A method that often provides accurate and robust forecasts for seasonal data is the Holt-Winters method with a damped trend and multiplicative seasonality:\[\begin{align*}
  \hat{y}_{t+h|t} &= \left[\ell_{t} + (\phi+\phi^2 + \dots + \phi^{h})b_{t}\right]s_{t+h-m(k+1)} \\
  \ell_{t} &= \alpha(y_{t} / s_{t-m}) + (1 - \alpha)(\ell_{t-1} + \phi b_{t-1})\\
  b_{t} &= \beta^*(\ell_{t} - \ell_{t-1}) + (1 - \beta^*)\phi b_{t-1}             \\
  s_{t} &= \gamma \frac{y_{t}}{(\ell_{t-1} + \phi b_{t-1})} + (1 - \gamma)s_{t-m}.
\end{align*}\]


### Example: Holt-Winters method with daily data


The Holt-Winters method can also be used for daily type of data, where the seasonal period is\(m=7\), and the appropriate unit of time for\(h\)is in days. Here we forecast pedestrian traffic at a busy Melbourne train station in July 2016.


```
sth_cross_ped <- pedestrian |>
  filter(Date >= "2016-07-01",
         Sensor == "Southern Cross Station") |>
  index_by(Date) |>
  summarise(Count = sum(Count)/1000)
sth_cross_ped |>
  filter(Date <= "2016-07-31") |>
  model(
    hw = ETS(Count ~ error("M") + trend("Ad") + season("M"))
  ) |>
  forecast(h = "2 weeks") |>
  autoplot(sth_cross_ped |> filter(Date <= "2016-08-14")) +
  labs(title = "Daily traffic: Southern Cross",
       y="Pedestrians ('000)")
```


Figure 8.9: Forecasts of daily pedestrian traffic at the Southern Cross railway station, Melbourne.


Clearly the model has identified the weekly seasonal pattern and the increasing trend at the end of the data, and the forecasts are a close match to the test data.


### Bibliography

- Our implementation uses maximum likelihood estimation as described in Section8.6while Holt and Winters originally minimized the sum of squared errors. For multiplicative seasonality, this will lead to slightly different parameter estimates. Optimizing the sum of squared errors can be obtained by settingopt_crit="mse"inETS().↩︎

Our implementation uses maximum likelihood estimation as described in Section8.6while Holt and Winters originally minimized the sum of squared errors. For multiplicative seasonality, this will lead to slightly different parameter estimates. Optimizing the sum of squared errors can be obtained by settingopt_crit="mse"inETS().↩︎
