
# Forecasting: Principles and Practice(3rd ed)


## 5.6Forecasting using transformations


Some common transformations which can be used when modelling were discussed in Section3.1. When forecasting from a model with transformations, we first produce forecasts of the transformed data. Then, we need to reverse the transformation (orback-transform) to obtain forecasts on the original scale. For Box-Cox transformations given by(3.1), the reverse transformation is given by\[\begin{equation}
\tag{5.2}
  y_{t} =
    \begin{cases}
      \exp(w_{t}) & \text{if $\lambda=0$};\\
      \text{sign}(\lambda w_t+1)|\lambda w_t+1|^{1/\lambda} & \text{otherwise}.
    \end{cases}
\end{equation}\]


Thefablepackage will automatically back-transform the forecasts whenever a transformation has been used in the model definition. The back-transformed forecast distribution is then a “transformed Normal” distribution.


### Prediction intervals with transformations


If a transformation has been used, then the prediction interval is first computed on the transformed scale, and the end points are back-transformed to give a prediction interval on the original scale. This approach preserves the probability coverage of the prediction interval, although it will no longer be symmetric around the point forecast.


The back-transformation of prediction intervals is done automatically when using thefablepackage, provided you have used a transformation in the model formula.


Transformations sometimes make little difference to the point forecasts but have a large effect on prediction intervals.


### Bias adjustments


One issue with using mathematical transformations such as Box-Cox transformations is that the back-transformed point forecast will not be the mean of the forecast distribution. In fact, it will usually be the median of the forecast distribution (assuming that the distribution on the transformed space is symmetric). For many purposes, this is acceptable, although the mean is usually preferable. For example, you may wish to add up sales forecasts from various regions to form a forecast for the whole country. But medians do not add up, whereas means do.


For a Box-Cox transformation, the back-transformed mean is given (approximately) by\[\begin{equation}
\tag{5.3}
\hat{y}_{T+h|T} =
  \begin{cases}
     \exp(\hat{w}_{T+h|T})\left[1 + \frac{\sigma_h^2}{2}\right] & \text{if $\lambda=0$;}\\
     (\lambda \hat{w}_{T+h|T}+1)^{1/\lambda}\left[1 + \frac{\sigma_h^2(1-\lambda)}{2(\lambda \hat{w}_{T+h|T}+1)^{2}}\right] & \text{otherwise;}
  \end{cases}
\end{equation}\]where\(\hat{w}_{T+h|T}\)is the\(h\)-step forecast mean and\(\sigma_h^2\)is the\(h\)-step forecast variance on the transformed scale. The larger the forecast variance, the bigger the difference between the mean and the median.


The difference between the simple back-transformed forecast given by(5.2)and the mean given by(5.3)is called thebias. When we use the mean, rather than the median, we say the point forecasts have beenbias-adjusted.


To see how much difference this bias-adjustment makes, consider the following example, where we forecast the average annual price of eggs using the drift method with a log transformation\((\lambda=0)\). The log transformation is useful in this case to ensure the forecasts and the prediction intervals stay positive.


```
fc <- prices |>
  filter(!is.na(eggs)) |>
  model(RW(log(eggs) ~ drift())) |>
  forecast(h = 50) |>
  mutate(.median = median(eggs))
fc |>
  autoplot(prices |> filter(!is.na(eggs)), level = 80) +
  geom_line(aes(y = .median), data = fc, linetype = 2, col = "blue") +
  labs(title = "Annual egg prices",
       y = "$US (in cents adjusted for inflation) ")
```


Figure 5.17: Forecasts of egg prices using the drift method applied to the logged data. The bias-adjusted mean forecasts are shown with a solid line, while the median forecasts are dashed.


The dashed line in Figure5.17shows the forecast medians while the solid line shows the forecast means. Notice how the skewed forecast distribution pulls up the forecast distribution’s mean; this is a result of the added term from the bias adjustment.


Bias-adjusted forecast means are automatically computed in thefablepackage. The forecast median (the point forecast prior to bias adjustment) can be obtained using themedian()function on the distribution column.
