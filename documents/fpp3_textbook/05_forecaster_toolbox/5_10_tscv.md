
# Forecasting: Principles and Practice(3rd ed)


## 5.10Time series cross-validation


A more sophisticated version of training/test sets is time series cross-validation. In this procedure, there are a series of test sets, each consisting of a single observation. The corresponding training set consists only of observations that occurredpriorto the observation that forms the test set. Thus, no future observations can be used in constructing the forecast. Since it is not possible to obtain a reliable forecast based on a small training set, the earliest observations are not considered as test sets.


The following diagram illustrates the series of training and test sets, where the blue observations form the training sets, and the orange observations form the test sets.


The forecast accuracy is computed by averaging over the test sets. This procedure is sometimes known as “evaluation on a rolling forecasting origin” because the “origin” at which the forecast is based rolls forward in time.


With time series forecasting, one-step forecasts may not be as relevant as multi-step forecasts. In this case, the cross-validation procedure based on a rolling forecasting origin can be modified to allow multi-step errors to be used. Suppose that we are interested in models that produce good\(4\)-step-ahead forecasts. Then the corresponding diagram is shown below.


In the following example, we compare the forecast accuracy obtained via time series cross-validation with the residual accuracy. Thestretch_tsibble()function is used to create many training sets. In this example, we start with a training set of length.init=3, and increase the size of successive training sets by.step=1.


```
# Time series cross-validation accuracy
google_2015_tr <- google_2015 |>
  stretch_tsibble(.init = 3, .step = 1) |>
  relocate(Date, Symbol, .id)
google_2015_tr
#> # A tsibble: 31,875 x 10 [1]
#> # Key:       Symbol, .id [250]
#>    Date       Symbol   .id  Open  High   Low Close Adj_Close  Volume   day
#>    <date>     <chr>  <int> <dbl> <dbl> <dbl> <dbl>     <dbl>   <dbl> <int>
#>  1 2015-01-02 GOOG       1  526.  528.  521.  522.      522. 1447600     1
#>  2 2015-01-05 GOOG       1  520.  521.  510.  511.      511. 2059800     2
#>  3 2015-01-06 GOOG       1  512.  513.  498.  499.      499. 2899900     3
#>  4 2015-01-02 GOOG       2  526.  528.  521.  522.      522. 1447600     1
#>  5 2015-01-05 GOOG       2  520.  521.  510.  511.      511. 2059800     2
#>  6 2015-01-06 GOOG       2  512.  513.  498.  499.      499. 2899900     3
#>  7 2015-01-07 GOOG       2  504.  504.  497.  498.      498. 2065100     4
#>  8 2015-01-02 GOOG       3  526.  528.  521.  522.      522. 1447600     1
#>  9 2015-01-05 GOOG       3  520.  521.  510.  511.      511. 2059800     2
#> 10 2015-01-06 GOOG       3  512.  513.  498.  499.      499. 2899900     3
#> # ℹ 31,865 more rows
```


The.idcolumn provides a new key indicating the various training sets. Theaccuracy()function can be used to evaluate the forecast accuracy across the training sets.


```
# TSCV accuracy
google_2015_tr |>
  model(RW(Close ~ drift())) |>
  forecast(h = 1) |>
  accuracy(google_2015)
# Training set accuracy
google_2015 |>
  model(RW(Close ~ drift())) |>
  accuracy()
```


As expected, the accuracy measures from the residuals are smaller, as the corresponding “forecasts” are based on a model fitted to the entire data set, rather than being true forecasts.


A good way to choose the best forecasting model is to find the model with the smallest RMSE computed using time series cross-validation.


### Example: Forecast horizon accuracy with cross-validation


Thegoogle_2015subset of thegafa_stockdata, plotted in Figure5.9, includes daily closing stock price of Google Inc from the NASDAQ exchange for all trading days in 2015.


The code below evaluates the forecasting performance of 1- to 8-step-ahead drift forecasts. The plot shows that the forecast error increases as the forecast horizon increases, as we would expect.


```
google_2015_tr <- google_2015 |>
  stretch_tsibble(.init = 3, .step = 1)
fc <- google_2015_tr |>
  model(RW(Close ~ drift())) |>
  forecast(h = 8) |>
  group_by(.id) |>
  mutate(h = row_number()) |>
  ungroup() |>
  as_fable(response = "Close", distribution = Close)
fc |>
  accuracy(google_2015, by = c("h", ".model")) |>
  ggplot(aes(x = h, y = RMSE)) +
  geom_point()
```


Figure 5.24: RMSE as a function of forecast horizon for the drift method applied to Google closing stock prices.
