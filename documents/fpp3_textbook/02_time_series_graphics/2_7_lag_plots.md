
# Forecasting: Principles and Practice(3rd ed)


## 2.7Lag plots


Figure2.19displays scatterplots of quarterly Australian beer production (introduced in Figure1.1), where the horizontal axis shows lagged values of the time series. Each graph shows\(y_{t}\)plotted against\(y_{t-k}\)for different values of\(k\).


```
recent_production <- aus_production |>
  filter(year(Quarter) >= 2000)
recent_production |>
  gg_lag(Beer, geom = "point") +
  labs(x = "lag(Beer, k)")
```


Figure 2.19: Lagged scatterplots for quarterly beer production.


Here the colours indicate the quarter of the variable on the vertical axis. The relationship is strongly positive at lags 4 and 8, reflecting the strong seasonality in the data. The negative relationship seen for lags 2 and 6 occurs because peaks (in Q4) are plotted against troughs (in Q2)
