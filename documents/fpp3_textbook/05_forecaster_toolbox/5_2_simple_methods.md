
# Forecasting: Principles and Practice(3rd ed)


## 5.2Some simple forecasting methods


Some forecasting methods are extremely simple and surprisingly effective. We will use four simple forecasting methods as benchmarks throughout this book. To illustrate them, we will use quarterly Australian clay brick production between 1970 and 2004.


```
bricks <- aus_production |>
  filter_index("1970 Q1" ~ "2004 Q4") |>
  select(Bricks)
```


Thefilter_index()function is a convenient shorthand for extracting a section of a time series.


### Mean method


Here, the forecasts of all future values are equal to the average (or “mean”) of the historical data. If we let the historical data be denoted by\(y_{1},\dots,y_{T}\), then we can write the forecasts as\[
  \hat{y}_{T+h|T} = \bar{y} = (y_{1}+\dots+y_{T})/T.
\]The notation\(\hat{y}_{T+h|T}\)is a short-hand for the estimate of\(y_{T+h}\)based on the data\(y_1,\dots,y_T\).


```
bricks |> model(MEAN(Bricks))
```


Figure 5.3: Mean (or average) forecasts applied to clay brick production in Australia.


### Naïve method


For naïve forecasts, we simply set all forecasts to be the value of the last observation. That is,\[
  \hat{y}_{T+h|T} = y_{T}.
\]This method works remarkably well for many economic and financial time series.


```
bricks |> model(NAIVE(Bricks))
```


Figure 5.4: Naïve forecasts applied to clay brick production in Australia.


Because a naïve forecast is optimal when data follow a random walk (see Section9.1), these are also calledrandom walk forecastsand theRW()function can be used instead ofNAIVE.


### Seasonal naïve method


A similar method is useful for highly seasonal data. In this case, we set each forecast to be equal to the last observed value from the same season (e.g., the same month of the previous year). Formally, the forecast for time\(T+h\)is written as\[
   \hat{y}_{T+h|T} = y_{T+h-m(k+1)},
\]where\(m=\)the seasonal period, and\(k\)is the integer part of\((h-1)/m\)(i.e., the number of complete years in the forecast period prior to time\(T+h\)). This looks more complicated than it really is. For example, with monthly data, the forecast for all future February values is equal to the last observed February value. With quarterly data, the forecast of all future Q2 values is equal to the last observed Q2 value (where Q2 means the second quarter). Similar rules apply for other months and quarters, and for other seasonal periods.


```
bricks |> model(SNAIVE(Bricks ~ lag("year")))
```


Thelag()function is optional here asbricksis quarterly data and so a seasonal naïve method will need a one-year lag. However, for some time series there is more than one seasonal period, and then the required lag must be specified.


Figure 5.5: Seasonal naïve forecasts applied to clay brick production in Australia.


### Drift method


A variation on the naïve method is to allow the forecasts to increase or decrease over time, where the amount of change over time (called thedrift) is set to be the average change seen in the historical data. Thus the forecast for time\(T+h\)is given by\[
  \hat{y}_{T+h|T} = y_{T} + \frac{h}{T-1}\sum_{t=2}^T (y_{t}-y_{t-1}) = y_{T} + h \left( \frac{y_{T} -y_{1}}{T-1}\right).
\]This is equivalent to drawing a line between the first and last observations, and extrapolating it into the future.


```
bricks |> model(RW(Bricks ~ drift()))
```


Figure 5.6: Drift forecasts applied to clay brick production in Australia.


### Example: Australian quarterly beer production


Figure5.7shows the first three methods applied to Australian quarterly beer production from 1992 to 2006, with the forecasts compared against actual values in the next 3.5 years.


```
# Set training data from 1992 to 2006
train <- aus_production |>
  filter_index("1992 Q1" ~ "2006 Q4")
# Fit the models
beer_fit <- train |>
  model(
    Mean = MEAN(Beer),
    `Naïve` = NAIVE(Beer),
    `Seasonal naïve` = SNAIVE(Beer)
  )
# Generate forecasts for 14 quarters
beer_fc <- beer_fit |> forecast(h = 14)
# Plot forecasts against actual values
beer_fc |>
  autoplot(train, level = NULL) +
  autolayer(
    filter_index(aus_production, "2007 Q1" ~ .),
    colour = "black"
  ) +
  labs(
    y = "Megalitres",
    title = "Forecasts for quarterly beer production"
  ) +
  guides(colour = guide_legend(title = "Forecast"))
```


Figure 5.7: Forecasts of Australian quarterly beer production.


In this case, only the seasonal naïve forecasts are close to the observed values from 2007 onwards.


### Example: Google’s daily closing stock price


In Figure5.8, the non-seasonal methods are applied to Google’s daily closing stock price in 2015, and used to forecast one month ahead. Because stock prices are not observed every day, we first set up a new time index based on the trading days rather than calendar days.


```
# Re-index based on trading days
google_stock <- gafa_stock |>
  filter(Symbol == "GOOG", year(Date) >= 2015) |>
  mutate(day = row_number()) |>
  update_tsibble(index = day, regular = TRUE)
# Filter the year of interest
google_2015 <- google_stock |> filter(year(Date) == 2015)
# Fit the models
google_fit <- google_2015 |>
  model(
    Mean = MEAN(Close),
    `Naïve` = NAIVE(Close),
    Drift = NAIVE(Close ~ drift())
  )
# Produce forecasts for the trading days in January 2016
google_jan_2016 <- google_stock |>
  filter(yearmonth(Date) == yearmonth("2016 Jan"))
google_fc <- google_fit |>
  forecast(new_data = google_jan_2016)
# Plot the forecasts
google_fc |>
  autoplot(google_2015, level = NULL) +
  autolayer(google_jan_2016, Close, colour = "black") +
  labs(y = "$US",
       title = "Google daily closing stock prices",
       subtitle = "(Jan 2015 - Jan 2016)") +
  guides(colour = guide_legend(title = "Forecast"))
```


Figure 5.8: Forecasts based on Google’s daily closing stock price in 2015.


Sometimes one of these simple methods will be the best forecasting method available; but in many cases, these methods will serve as benchmarks rather than the method of choice. That is, any forecasting methods we develop will be compared to these simple methods to ensure that the new method is better than these simple alternatives. If not, the new method is not worth considering.
