
# Forecasting: Principles and Practice(3rd ed)


## 5.8Evaluating point forecast accuracy


### Training and test sets


It is important to evaluate forecast accuracy using genuine forecasts. Consequently, the size of the residuals is not a reliable indication of how large true forecast errors are likely to be. The accuracy of forecasts can only be determined by considering how well a model performs on new data that were not used when fitting the model.


When choosing models, it is common practice to separate the available data into two portions,trainingandtestdata, where the training data is used to estimate any parameters of a forecasting method and the test data is used to evaluate its accuracy. Because the test data is not used in determining the forecasts, it should provide a reliable indication of how well the model is likely to forecast on new data.


The size of the test set is typically about 20% of the total sample, although this value depends on how long the sample is and how far ahead you want to forecast. The test set should ideally be at least as large as the maximum forecast horizon required. The following points should be noted.

- A model which fits the training data well will not necessarily forecast well.
- A perfect fit can always be obtained by using a model with enough parameters.
- Over-fitting a model to data is just as bad as failing to identify a systematic pattern in the data.

Some references describe the test set as the “hold-out set” because these data are “held out” of the data used for fitting. Other references call the training set the “in-sample data” and the test set the “out-of-sample data”. We prefer to use “training data” and “test data” in this book.


### Functions to subset a time series


Thefilter()function is useful when extracting a portion of a time series, such as we need when creating training and test sets. When splitting data into evaluation sets, filtering the index of the data is particularly useful. For example,


```
aus_production |> filter(year(Quarter) >= 1995)
```


extracts all data from 1995 onward. Equivalently,


```
aus_production |> filter_index("1995 Q1" ~ .)
```


can be used.


Another useful function isslice(), which allows the use of indices to choose a subset from each group. For example,


```
aus_production |>
  slice(n()-19:0)
```


extracts the last 20 observations (5 years).


Slice also works with groups, making it possible to subset observations from each key. For example,


```
aus_retail |>
  group_by(State, Industry) |>
  slice(1:12)
```


will subset the first year of data from each time series in the data.


### Forecast errors


A forecast “error” is the difference between an observed value and its forecast. Here “error” does not mean a mistake, it means the unpredictable part of an observation. It can be written as\[
  e_{T+h} = y_{T+h} - \hat{y}_{T+h|T},
\]where the training data is given by\(\{y_1,\dots,y_T\}\)and the test data is given by\(\{y_{T+1},y_{T+2},\dots\}\).


Note that forecast errors are different from residuals in two ways. First, residuals are calculated on thetrainingset while forecast errors are calculated on thetestset. Second, residuals are based onone-stepforecasts while forecast errors can involvemulti-stepforecasts.


We can measure forecast accuracy by summarising the forecast errors in different ways.


### Scale-dependent errors


The forecast errors are on the same scale as the data. Accuracy measures that are based only on\(e_{t}\)are therefore scale-dependent and cannot be used to make comparisons between series that involve different units.


The two most commonly used scale-dependent measures are based on the absolute errors or squared errors:\[\begin{align*}
  \text{Mean absolute error: MAE} & = \text{mean}(|e_{t}|),\\
  \text{Root mean squared error: RMSE} & = \sqrt{\text{mean}(e_{t}^2)}.
\end{align*}\]When comparing forecast methods applied to a single time series, or to several time series with the same units, the MAE is popular as it is easy to both understand and compute. A forecast method that minimises the MAE will lead to forecasts of the median, while minimising the RMSE will lead to forecasts of the mean. Consequently, the RMSE is also widely used, despite being more difficult to interpret.


### Percentage errors


The percentage error is given by\(p_{t} = 100 e_{t}/y_{t}\). Percentage errors have the advantage of being unit-free, and so are frequently used to compare forecast performances between data sets. The most commonly used measure is:\[
  \text{Mean absolute percentage error: MAPE} = \text{mean}(|p_{t}|).
\]Measures based on percentage errors have the disadvantage of being infinite or undefined if\(y_{t}=0\)for any\(t\)in the period of interest, and having extreme values if any\(y_{t}\)is close to zero. Another problem with percentage errors that is often overlooked is that they assume the unit of measurement has a meaningful zero.5For example, a percentage error makes no sense when measuring the accuracy of temperature forecasts on either the Fahrenheit or Celsius scales, because temperature has an arbitrary zero point.


They also have the disadvantage that they put a heavier penalty on negative errors than on positive errors. This observation led to the use of the so-called “symmetric” MAPE (sMAPE) proposed byArmstrong (1978, p. 348), which was used in the M3 forecasting competition. It is defined by\[
  \text{sMAPE} = \text{mean}\left(200|y_{t} - \hat{y}_{t}|/(y_{t}+\hat{y}_{t})\right).
\]However, if\(y_{t}\)is close to zero,\(\hat{y}_{t}\)is also likely to be close to zero. Thus, the measure still involves division by a number close to zero, making the calculation unstable. Also, the value of sMAPE can be negative, so it is not really a measure of “absolute percentage errors” at all.


Hyndman & Koehler (2006)recommend that the sMAPE not be used. It is included here only because it is widely used, although we will not use it in this book.


### Scaled errors


Scaled errors were proposed byHyndman & Koehler (2006)as an alternative to using percentage errors when comparing forecast accuracy across series with different units. They proposed scaling the errors based on thetrainingMAE from a simple forecast method.


For a non-seasonal time series, a useful way to define a scaled error uses naïve forecasts:\[
  q_{j} = \frac{\displaystyle e_{j}}
    {\displaystyle\frac{1}{T-1}\sum_{t=2}^T |y_{t}-y_{t-1}|}.
\]Because the numerator and denominator both involve values on the scale of the original data,\(q_{j}\)is independent of the scale of the data. A scaled error is less than one if it arises from a better forecast than the average one-step naïve forecast computed on the training data. Conversely, it is greater than one if the forecast is worse than the average one-step naïve forecast computed on the training data.


For seasonal time series, a scaled error can be defined using seasonal naïve forecasts:\[
  q_{j} = \frac{\displaystyle e_{j}}
    {\displaystyle\frac{1}{T-m}\sum_{t=m+1}^T |y_{t}-y_{t-m}|}.
\]


Themean absolute scaled erroris simply\[
  \text{MASE} = \text{mean}(|q_{j}|).
\]Similarly, theroot mean squared scaled erroris given by\[
  \text{RMSSE} = \sqrt{\text{mean}(q_{j}^2)},
\]where\[
  q^2_{j} = \frac{\displaystyle e^2_{j}}
    {\displaystyle\frac{1}{T-m}\sum_{t=m+1}^T (y_{t}-y_{t-m})^2},
\]and we set\(m=1\)for non-seasonal data.


### Examples


```
recent_production <- aus_production |>
  filter(year(Quarter) >= 1992)
beer_train <- recent_production |>
  filter(year(Quarter) <= 2007)

beer_fit <- beer_train |>
  model(
    Mean = MEAN(Beer),
    `Naïve` = NAIVE(Beer),
    `Seasonal naïve` = SNAIVE(Beer),
    Drift = RW(Beer ~ drift())
  )

beer_fc <- beer_fit |>
  forecast(h = 10)

beer_fc |>
  autoplot(
    aus_production |> filter(year(Quarter) >= 1992),
    level = NULL
  ) +
  labs(
    y = "Megalitres",
    title = "Forecasts for quarterly beer production"
  ) +
  guides(colour = guide_legend(title = "Forecast"))
```


Figure 5.21: Forecasts of Australian quarterly beer production using data up to the end of 2007.


Figure5.21shows four forecast methods applied to the quarterly Australian beer production using data only to the end of 2007. The actual values for the period 2008–2010 are also shown. We compute the forecast accuracy measures for this period.


```
accuracy(beer_fc, recent_production)
```


Theaccuracy()function will automatically extract the relevant periods from the data (recent_productionin this example) to match the forecasts when computing the various accuracy measures.


It is obvious from the graph that the seasonal naïve method is best for these data, although it can still be improved, as we will discover later. Sometimes, different accuracy measures will lead to different results as to which forecast method is best. However, in this case, all of the results point to the seasonal naïve method as the best of these four methods for this data set.


To take a non-seasonal example, consider the Google stock price. The following graph shows the closing stock prices from 2015, along with forecasts for January 2016 obtained from three different methods.


```
google_fit <- google_2015 |>
  model(
    Mean = MEAN(Close),
    `Naïve` = NAIVE(Close),
    Drift = RW(Close ~ drift())
  )

google_fc <- google_fit |>
  forecast(google_jan_2016)
```


```
google_fc |>
  autoplot(bind_rows(google_2015, google_jan_2016),
    level = NULL) +
  labs(y = "$US",
       title = "Google closing stock prices from Jan 2015") +
  guides(colour = guide_legend(title = "Forecast"))
```


Figure 5.22: Forecasts of the Google stock price for Jan 2016.


```
accuracy(google_fc, google_stock)
```


Here, the best method is the naïve method (regardless of which accuracy measure is used).


### Bibliography

- That is, a percentage is valid on a ratio scale, but not on an interval scale. Only ratio scale variables have meaningful zeros.↩︎

That is, a percentage is valid on a ratio scale, but not on an interval scale. Only ratio scale variables have meaningful zeros.↩︎
