
# Forecasting: Principles and Practice(3rd ed)


## 13.8Forecasting on training and test sets


Typically, we compute one-step forecasts on the training data (the “fitted values”) and multi-step forecasts on the test data. However, occasionally we may wish to compute multi-step forecasts on the training data, or one-step forecasts on the test data.


### Multi-step forecasts on training data


We normally define fitted values to be one-step forecasts on the training set (see Section5.3), but a similar idea can be used for multi-step forecasts. We will illustrate the method using an ARIMA model for the Australian take-away food expenditure. The last five years are used for a test set, and the forecasts are plotted in Figure13.9.


```
training <- auscafe |> filter(year(Month) <= 2013)
test <- auscafe |> filter(year(Month) > 2013)
cafe_fit <- training |>
  model(ARIMA(log(Turnover)))
cafe_fit |>
  forecast(h = 60) |>
  autoplot(auscafe) +
  labs(title = "Australian food expenditure",
       y = "$ (billions)")
```


Figure 13.9: Forecasts from an ARIMA model fitted to the Australian monthly expenditure on cafés, restaurants and takeaway food services.


Thefitted()function has anhargument to allow for\(h\)-step “fitted values” on the training set. Figure13.10is a plot of 12-step (one year) forecasts on the training set. Because the model involves both seasonal (lag 12) and first (lag 1) differencing, it is not possible to compute these forecasts for the first few observations.


```
fits12 <- fitted(cafe_fit, h = 12)
training |>
  autoplot(Turnover) +
  autolayer(fits12, .fitted, col = "#D55E00") +
  labs(title = "Australian food expenditure",
       y = "$ (billions)")
```


Figure 13.10: Twelve-step fitted values from an ARIMA model fitted to the Australian café training data.


### One-step forecasts on test data


It is common practice to fit a model using training data, and then to evaluate its performance on a test data set. The way this is usually done means the comparisons on the test data use different forecast horizons. In the above example, we have used the last sixty observations for the test data, and estimated our forecasting model on the training data. Then the forecast errors will be for 1-step, 2-steps, …, 60-steps ahead. The forecast variance usually increases with the forecast horizon, so if we are simply averaging the absolute or squared errors from the test set, we are combining results with different variances.


One solution to this issue is to obtain 1-step errors on the test data. That is, we still use the training data to estimate any parameters, but when we compute forecasts on the test data, we use all of the data preceding each observation (both training and test data). So our training data are for times\(1,2,\dots,T-60\). We estimate the model on these data, but then compute\(\hat{y}_{T-60+h|T-61+h}\), for\(h=1,\dots,T-1\). Because the test data are not used to estimate the parameters, this still gives us a “fair” forecast.


Using the same ARIMA model used above, we now apply the model to the test data.


```
cafe_fit |>
  refit(test) |>
  accuracy()
#> # A tibble: 1 × 10
#>   .model              .type    ME  RMSE   MAE    MPE  MAPE  MASE RMSSE    ACF1
#>   <chr>               <chr> <dbl> <dbl> <dbl>  <dbl> <dbl> <dbl> <dbl>   <dbl>
#> 1 ARIMA(log(Turnover… Trai… -2.49  20.5  15.4 -0.169  1.06 0.236 0.259 -0.0502
```


Note that model is not re-estimated in this case. Instead, the model obtained previously (and stored ascafe_fit) is applied to thetestdata. Because the model was not re-estimated, the “residuals” obtained here are actually one-step forecast errors. Consequently, the results produced from theaccuracy()command are actually on the test set (despite the output saying “Training set”). This approach can be used to compare one-step forecasts from different models.
