
# Forecasting: Principles and Practice(3rd ed)


## 12.1Complex seasonality


So far, we have mostly considered relatively simple seasonal patterns such as quarterly and monthly data. However, higher frequency time series often exhibit more complicated seasonal patterns. For example, daily data may have a weekly pattern as well as an annual pattern. Hourly data usually has three types of seasonality: a daily pattern, a weekly pattern, and an annual pattern. Even weekly data can be challenging to forecast as there are not a whole number of weeks in a year, so the annual pattern has a seasonal period of\(365.25/7\approx 52.179\)on average. Most of the methods we have considered so far are unable to deal with these seasonal complexities.


We don’t necessarily want to include all of the possible seasonal periods in our models — just the ones that are likely to be present in the data. For example, if we have only 180 days of data, we may ignore the annual seasonality. If the data are measurements of a natural phenomenon (e.g., temperature), we can probably safely ignore any weekly seasonality.


Figure12.1shows the number of calls to a North American commercial bank per 5-minute interval between 7:00am and 9:05pm each weekday over a 33 week period. The lower panel shows the first four weeks of the same time series. There is a strong daily seasonal pattern with period 169 (there are 169 5-minute intervals per day), and a weak weekly seasonal pattern with period\(169 \times 5=845\). (Call volumes on Mondays tend to be higher than the rest of the week.) If a longer series of data were available, we may also have observed an annual seasonal pattern.


```
bank_calls |>
  fill_gaps() |>
  autoplot(Calls) +
  labs(y = "Calls",
       title = "Five-minute call volume to bank")
```


Figure 12.1: Five-minute call volume handled on weekdays between 7:00am and 9:05pm in a large North American commercial bank. Top panel: data from 3 March – 24 October 2003. Bottom panel: first four weeks of data.


Apart from the multiple seasonal periods, this series has the additional complexity of missing values between the working periods.


### STL with multiple seasonal periods


TheSTL()function is designed to deal with multiple seasonality. It will return multiple seasonal components, as well as a trend and remainder component. In this case, we need to re-index the tsibble to avoid the missing values, and then explicitly give the seasonal periods.


```
calls <- bank_calls |>
  mutate(t = row_number()) |>
  update_tsibble(index = t, regular = TRUE)
```


```
calls |>
  model(
    STL(sqrt(Calls) ~ season(period = 169) +
                      season(period = 5*169),
        robust = TRUE)
  ) |>
  components() |>
  autoplot() + labs(x = "Observation")
```


Figure 12.2: STL decomposition with multiple seasonality for the call volume data.


There are two seasonal patterns shown, one for the time of day (the third panel), and one for the time of week (the fourth panel). To properly interpret this graph, it is important to notice the vertical scales. In this case, the trend and the weekly seasonality have wider bars (and therefore relatively narrower ranges) compared to the other components, because there is little trend seen in the data, and the weekly seasonality is weak.


The decomposition can also be used in forecasting, with each of the seasonal components forecast using a seasonal naïve method, and the seasonally adjusted data forecast using ETS.


The code is slightly more complicated than usual because we have to add back the time stamps that were lost when we re-indexed the tsibble to handle the periods of missing observations. The square root transformation used in the STL decomposition has ensured the forecasts remain positive.


```
# Forecasts from STL+ETS decomposition
my_dcmp_spec <- decomposition_model(
  STL(sqrt(Calls) ~ season(period = 169) +
                    season(period = 5*169),
      robust = TRUE),
  ETS(season_adjust ~ season("N"))
)
fc <- calls |>
  model(my_dcmp_spec) |>
  forecast(h = 5 * 169)

# Add correct time stamps to fable
fc_with_times <- bank_calls |>
  new_data(n = 7 * 24 * 60 / 5) |>
  mutate(time = format(DateTime, format = "%H:%M:%S")) |>
  filter(
    time %in% format(bank_calls$DateTime, format = "%H:%M:%S"),
    wday(DateTime, week_start = 1) <= 5
  ) |>
  mutate(t = row_number() + max(calls$t)) |>
  left_join(fc, by = "t") |>
  as_fable(response = "Calls", distribution = Calls)

# Plot results with last 3 weeks of data
fc_with_times |>
  fill_gaps() |>
  autoplot(bank_calls |> tail(14 * 169) |> fill_gaps()) +
  labs(y = "Calls",
       title = "Five-minute call volume to bank")
```


Figure 12.3: Forecasts of the call volume data using an STL decomposition with the seasonal components forecast using a seasonal naïve method, and the seasonally adjusted data forecast using ETS.


### Dynamic harmonic regression with multiple seasonal periods


With multiple seasonalities, we can use Fourier terms as we did in earlier chapters (see Sections7.4and10.5). Because there are multiple seasonalities, we need to add Fourier terms for each seasonal period. In this case, the seasonal periods are 169 and 845, so the Fourier terms are of the form\[
  \sin\left(\frac{2\pi kt}{169}\right), \quad
  \cos\left(\frac{2\pi kt}{169}\right), \quad
  \sin\left(\frac{2\pi kt}{845}\right), \quad  \text{and} \quad
  \cos\left(\frac{2\pi kt}{845}\right),
\]for\(k=1,2,\dots\). As usual, thefourier()function can generate these for you.


We will fit a dynamic harmonic regression model with an ARIMA error structure. The total number of Fourier terms for each seasonal period could be selected to minimise the AICc. However, for high seasonal periods, this tends to over-estimate the number of terms required, so we will use a more subjective choice with 10 terms for the daily seasonality and 5 for the weekly seasonality. Again, we will use a square root transformation to ensure the forecasts and prediction intervals remain positive. We set\(D=d=0\)in order to handle the non-stationarity through the regression terms, and\(P=Q=0\)in order to handle the seasonality through the regression terms.


```
fit <- calls |>
  model(
    dhr = ARIMA(sqrt(Calls) ~ PDQ(0, 0, 0) + pdq(d = 0) +
                  fourier(period = 169, K = 10) +
                  fourier(period = 5*169, K = 5)))

fc <- fit |> forecast(h = 5 * 169)

# Add correct time stamps to fable
fc_with_times <- bank_calls |>
  new_data(n = 7 * 24 * 60 / 5) |>
  mutate(time = format(DateTime, format = "%H:%M:%S")) |>
  filter(
    time %in% format(bank_calls$DateTime, format = "%H:%M:%S"),
    wday(DateTime, week_start = 1) <= 5
  ) |>
  mutate(t = row_number() + max(calls$t)) |>
  left_join(fc, by = "t") |>
  as_fable(response = "Calls", distribution = Calls)
```


```
# Plot results with last 3 weeks of data
fc_with_times |>
  fill_gaps() |>
  autoplot(bank_calls |> tail(14 * 169) |> fill_gaps()) +
  labs(y = "Calls",
       title = "Five-minute call volume to bank")
```


Figure 12.4: Forecasts from a dynamic harmonic regression applied to the call volume data.


This is a large model, containing 33 parameters: 4 ARMA coefficients, 20 Fourier coefficients for period 169, and 8 Fourier coefficients for period 845. Not all of the Fourier terms for period 845 are used because there is some overlap with the terms of period 169 (since\(845=5\times169\)).


### Example: Electricity demand


One common application of such models is electricity demand modelling. Figure12.5shows half-hourly electricity demand (MWh) in Victoria, Australia, during 2012–2014, along with temperatures (degrees Celsius) for the same period for Melbourne (the largest city in Victoria).


```
vic_elec |>
  pivot_longer(Demand:Temperature, names_to = "Series") |>
  ggplot(aes(x = Time, y = value)) +
  geom_line() +
  facet_grid(rows = vars(Series), scales = "free_y") +
  labs(y = "")
```


Figure 12.5: Half-hourly electricity demand and corresponding temperatures in 2012–2014, Victoria, Australia.


Plotting electricity demand against temperature (Figure12.6) shows that there is a nonlinear relationship between the two, with demand increasing for low temperatures (due to heating) and increasing for high temperatures (due to cooling).


```
elec <- vic_elec |>
  mutate(
    DOW = wday(Date, label = TRUE),
    Working_Day = !Holiday & !(DOW %in% c("Sat", "Sun")),
    Cooling = pmax(Temperature, 18)
  )
elec |>
  ggplot(aes(x=Temperature, y=Demand, col=Working_Day)) +
  geom_point(alpha = 0.6) +
  labs(x="Temperature (degrees Celsius)", y="Demand (MWh)")
```


Figure 12.6: Half-hourly electricity demand for Victoria, plotted against temperatures for the same times in Melbourne, the largest city in Victoria.


We will fit a regression model with a piecewise linear function of temperature (containing a knot at 18 degrees), and harmonic regression terms to allow for the daily seasonal pattern. Again, we set the orders of the Fourier terms subjectively, while using the AICc to select the order of the ARIMA errors.


```
fit <- elec |>
  model(
    ARIMA(Demand ~ PDQ(0, 0, 0) + pdq(d = 0) +
          Temperature + Cooling + Working_Day +
          fourier(period = "day", K = 10) +
          fourier(period = "week", K = 5) +
          fourier(period = "year", K = 3))
  )
```


Forecasting with such models is difficult because we require future values of the predictor variables. Future values of the Fourier terms are easy to compute, but future temperatures are, of course, unknown. If we are only interested in forecasting up to a week ahead, we could use temperature forecasts obtained from a meteorological model. Alternatively, we could use scenario forecasting (Section6.5) and plug in possible temperature patterns. In the following example, we have used a repeat of the last two days of temperatures to generate future possible demand values.


```
elec_newdata <- new_data(elec, 2*48) |>
  mutate(
    Temperature = tail(elec$Temperature, 2 * 48),
    Date = lubridate::as_date(Time),
    DOW = wday(Date, label = TRUE),
    Working_Day = (Date != "2015-01-01") &
                   !(DOW %in% c("Sat", "Sun")),
    Cooling = pmax(Temperature, 18)
  )
fc <- fit |>
  forecast(new_data = elec_newdata)

fc |>
  autoplot(elec |> tail(10 * 48)) +
  labs(title="Half hourly electricity demand: Victoria",
       y = "Demand (MWh)", x = "Time [30m]")
```


Figure 12.7: Forecasts from a dynamic harmonic regression model applied to half-hourly electricity demand data.


Although the short-term forecasts look reasonable, this is a crude model for a complicated process. The residuals, plotted in Figure12.8, demonstrate that there is a lot of information that has not been captured with this model.


```
fit |> gg_tsresiduals()
```


Figure 12.8: Residual diagnostics for the dynamic harmonic regression model.


More sophisticated versions of this model which provide much better forecasts are described inHyndman & Fan (2010)andFan & Hyndman (2012).


### Bibliography
