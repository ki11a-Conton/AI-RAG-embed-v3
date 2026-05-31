
# Forecasting: Principles and Practice(3rd ed)


## 7.10Exercises

- Half-hourly electricity demand for Victoria, Australia is contained invic_elec. Extract the January 2014 electricity demand, and aggregate this data to daily with daily total demands and maximum temperatures.jan14_vic_elec<-vic_elec|>filter(yearmonth(Time)==yearmonth("2014 Jan"))|>index_by(Date =as_date(Time))|>summarise(Demand =sum(Demand),Temperature =max(Temperature))Plot the data and find the regression model for Demand with temperature as a predictor variable. Why is there a positive relationship?Produce a residual plot. Is the model adequate? Are there any outliers or influential observations?Use the model to forecast the electricity demand that you would expect for the next day if the maximum temperature was\(15^\circ \text{C}\)and compare it with the forecast if the with maximum temperature was\(35^\circ \text{C}\). Do you believe these forecasts? The following R code will get you started:jan14_vic_elec|>model(TSLM(Demand~Temperature))|>forecast(new_data(jan14_vic_elec,1)|>mutate(Temperature =15))|>autoplot(jan14_vic_elec)Give prediction intervals for your forecasts.Plot Demand vs Temperature for all of the available data invic_elecaggregated to daily total demand and maximum temperature. What does this say about your model?

Half-hourly electricity demand for Victoria, Australia is contained invic_elec. Extract the January 2014 electricity demand, and aggregate this data to daily with daily total demands and maximum temperatures.


```
jan14_vic_elec <- vic_elec |>
  filter(yearmonth(Time) == yearmonth("2014 Jan")) |>
  index_by(Date = as_date(Time)) |>
  summarise(
    Demand = sum(Demand),
    Temperature = max(Temperature)
  )
```

- Plot the data and find the regression model for Demand with temperature as a predictor variable. Why is there a positive relationship?

Plot the data and find the regression model for Demand with temperature as a predictor variable. Why is there a positive relationship?

- Produce a residual plot. Is the model adequate? Are there any outliers or influential observations?

Produce a residual plot. Is the model adequate? Are there any outliers or influential observations?

- Use the model to forecast the electricity demand that you would expect for the next day if the maximum temperature was\(15^\circ \text{C}\)and compare it with the forecast if the with maximum temperature was\(35^\circ \text{C}\). Do you believe these forecasts? The following R code will get you started:jan14_vic_elec|>model(TSLM(Demand~Temperature))|>forecast(new_data(jan14_vic_elec,1)|>mutate(Temperature =15))|>autoplot(jan14_vic_elec)

Use the model to forecast the electricity demand that you would expect for the next day if the maximum temperature was\(15^\circ \text{C}\)and compare it with the forecast if the with maximum temperature was\(35^\circ \text{C}\). Do you believe these forecasts? The following R code will get you started:


```
jan14_vic_elec |>
  model(TSLM(Demand ~ Temperature)) |>
  forecast(
    new_data(jan14_vic_elec, 1) |>
      mutate(Temperature = 15)
  ) |>
  autoplot(jan14_vic_elec)
```

- Give prediction intervals for your forecasts.

Give prediction intervals for your forecasts.

- Plot Demand vs Temperature for all of the available data invic_elecaggregated to daily total demand and maximum temperature. What does this say about your model?

Plot Demand vs Temperature for all of the available data invic_elecaggregated to daily total demand and maximum temperature. What does this say about your model?

- Data setolympic_runningcontains the winning times (in seconds) in each Olympic Games sprint, middle-distance and long-distance track events from 1896 to 2016.Plot the winning time against the year for each event. Describe the main features of the plot.Fit a regression line to the data for each event. Obviously the winning times have been decreasing, but at whataveragerate per year?Plot the residuals against the year. What does this indicate about the suitability of the fitted lines?Predict the winning time for each race in the 2020 Olympics. Give a prediction interval for your forecasts. What assumptions have you made in these calculations?

Data setolympic_runningcontains the winning times (in seconds) in each Olympic Games sprint, middle-distance and long-distance track events from 1896 to 2016.

- Plot the winning time against the year for each event. Describe the main features of the plot.
- Fit a regression line to the data for each event. Obviously the winning times have been decreasing, but at whataveragerate per year?
- Plot the residuals against the year. What does this indicate about the suitability of the fitted lines?
- Predict the winning time for each race in the 2020 Olympics. Give a prediction interval for your forecasts. What assumptions have you made in these calculations?
- An elasticity coefficient is the ratio of the percentage change in the forecast variable (\(y\)) to the percentage change in the predictor variable (\(x\)). Mathematically, the elasticity is defined as\((dy/dx)\times(x/y)\). Consider the log-log model,\[
   \log y=\beta_0+\beta_1 \log x + \varepsilon.
\]Express\(y\)as a function of\(x\)and show that the coefficient\(\beta_1\)is the elasticity coefficient.

An elasticity coefficient is the ratio of the percentage change in the forecast variable (\(y\)) to the percentage change in the predictor variable (\(x\)). Mathematically, the elasticity is defined as\((dy/dx)\times(x/y)\). Consider the log-log model,\[
   \log y=\beta_0+\beta_1 \log x + \varepsilon.
\]Express\(y\)as a function of\(x\)and show that the coefficient\(\beta_1\)is the elasticity coefficient.

- The data setsouvenirsconcerns the monthly sales figures of a shop which opened in January 1987 and sells gifts, souvenirs, and novelties. The shop is situated on the wharf at a beach resort town in Queensland, Australia. The sales volume varies with the seasonal population of tourists. There is a large influx of visitors to the town at Christmas and for the local surfing festival, held every March since 1988. Over time, the shop has expanded its premises, range of products, and staff.Produce a time plot of the data and describe the patterns in the graph. Identify any unusual or unexpected fluctuations in the time series.Explain why it is necessary to take logarithms of these data before fitting a model.Fit a regression model to the logarithms of these sales data with a linear trend, seasonal dummies and a “surfing festival” dummy variable.Plot the residuals against time and against the fitted values. Do these plots reveal any problems with the model?Do boxplots of the residuals for each month. Does this reveal any problems with the model?What do the values of the coefficients tell you about each variable?What does the Ljung-Box test tell you about your model?Regardless of your answers to the above questions, use your regression model to predict the monthly sales for 1994, 1995, and 1996. Produce prediction intervals for each of your forecasts.How could you improve these predictions by modifying the model?

The data setsouvenirsconcerns the monthly sales figures of a shop which opened in January 1987 and sells gifts, souvenirs, and novelties. The shop is situated on the wharf at a beach resort town in Queensland, Australia. The sales volume varies with the seasonal population of tourists. There is a large influx of visitors to the town at Christmas and for the local surfing festival, held every March since 1988. Over time, the shop has expanded its premises, range of products, and staff.

- Produce a time plot of the data and describe the patterns in the graph. Identify any unusual or unexpected fluctuations in the time series.
- Explain why it is necessary to take logarithms of these data before fitting a model.
- Fit a regression model to the logarithms of these sales data with a linear trend, seasonal dummies and a “surfing festival” dummy variable.
- Plot the residuals against time and against the fitted values. Do these plots reveal any problems with the model?
- Do boxplots of the residuals for each month. Does this reveal any problems with the model?
- What do the values of the coefficients tell you about each variable?
- What does the Ljung-Box test tell you about your model?
- Regardless of your answers to the above questions, use your regression model to predict the monthly sales for 1994, 1995, and 1996. Produce prediction intervals for each of your forecasts.
- How could you improve these predictions by modifying the model?
- Theus_gasolineseries consists of weekly data for supplies of US finished motor gasoline product, from 2 February 1991 to 20 January 2017. The units are in “million barrels per day”. Consider only the data to the end of 2004.Fit a harmonic regression with trend to the data. Experiment with changing the number Fourier terms. Plot the observed gasoline and fitted values and comment on what you see.Select the appropriate number of Fourier terms to include by minimising the AICc or CV value.Plot the residuals of the final model using thegg_tsresiduals()function and comment on these. Use a Ljung-Box test to check for residual autocorrelation.Generate forecasts for the next year of data and plot these along with the actual data for 2005. Comment on the forecasts.

Theus_gasolineseries consists of weekly data for supplies of US finished motor gasoline product, from 2 February 1991 to 20 January 2017. The units are in “million barrels per day”. Consider only the data to the end of 2004.

- Fit a harmonic regression with trend to the data. Experiment with changing the number Fourier terms. Plot the observed gasoline and fitted values and comment on what you see.
- Select the appropriate number of Fourier terms to include by minimising the AICc or CV value.
- Plot the residuals of the final model using thegg_tsresiduals()function and comment on these. Use a Ljung-Box test to check for residual autocorrelation.
- Generate forecasts for the next year of data and plot these along with the actual data for 2005. Comment on the forecasts.
- The annual population of Afghanistan is available in theglobal_economydata set.Plot the data and comment on its features. Can you observe the effect of the Soviet-Afghan war?Fit a linear trend model and compare this to a piecewise linear trend model with knots at 1980 and 1989.Generate forecasts from these two models for the five years after the end of the data, and comment on the results.

The annual population of Afghanistan is available in theglobal_economydata set.

- Plot the data and comment on its features. Can you observe the effect of the Soviet-Afghan war?
- Fit a linear trend model and compare this to a piecewise linear trend model with knots at 1980 and 1989.
- Generate forecasts from these two models for the five years after the end of the data, and comment on the results.
- (For advanced readers following on from Section7.9).Using matrix notation it was shown that if\(\bm{y}=\bm{X}\bm{\beta}+\bm{\varepsilon}\), where\(\bm{\varepsilon}\)has mean\(\bm{0}\)and variance matrix\(\sigma^2\bm{I}\), the estimated coefficients are given by\(\hat{\bm{\beta}}=(\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y}\)and a forecast is given by\(\hat{y}=\bm{x}^*\hat{\bm{\beta}}=\bm{x}^*(\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y}\)where\(\bm{x}^*\)is a row vector containing the values of the predictors for the forecast (in the same format as\(\bm{X}\)), and the forecast variance is given by\(\text{Var}(\hat{y})=\sigma^2 \left[1+\bm{x}^*(\bm{X}'\bm{X})^{-1}(\bm{x}^*)'\right].\)Consider the simple time trend model where\(y_t = \beta_0 + \beta_1t\). Using the following results,\[
   \sum^{T}_{t=1}{t}=\frac{1}{2}T(T+1),\quad \sum^{T}_{t=1}{t^2}=\frac{1}{6}T(T+1)(2T+1)
\]derive the following expressions:\(\displaystyle\bm{X}'\bm{X}=\frac{1}{6}\left[
\begin{array}{cc}
  6T      & 3T(T+1) \\
  3T(T+1) & T(T+1)(2T+1) \\
\end{array}
\right]\)\(\displaystyle(\bm{X}'\bm{X})^{-1}=\frac{2}{T(T^2-1)}\left[
\begin{array}{cc}
  (T+1)(2T+1)   & -3(T+1) \\
  -3(T+1)       & 6 \\
\end{array}
\right]\)\(\displaystyle\hat{\beta}_0=\frac{2}{T(T-1)}\left[(2T+1)\sum^T_{t=1}y_t-3\sum^T_{t=1}ty_t
\right]\)\(\displaystyle\hat{\beta}_1=\frac{6}{T(T^2-1)}\left[2\sum^T_{t=1}ty_t-(T+1)\sum^T_{t=1}y_t \right]\)\(\displaystyle\text{Var}(\hat{y}_{t})=\hat{\sigma}^2\left[1+\frac{2}{T(T-1)}\left(1-4T-6h+6\frac{(T+h)^2}{T+1}\right)\right]\)

(For advanced readers following on from Section7.9).


Using matrix notation it was shown that if\(\bm{y}=\bm{X}\bm{\beta}+\bm{\varepsilon}\), where\(\bm{\varepsilon}\)has mean\(\bm{0}\)and variance matrix\(\sigma^2\bm{I}\), the estimated coefficients are given by\(\hat{\bm{\beta}}=(\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y}\)and a forecast is given by\(\hat{y}=\bm{x}^*\hat{\bm{\beta}}=\bm{x}^*(\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y}\)where\(\bm{x}^*\)is a row vector containing the values of the predictors for the forecast (in the same format as\(\bm{X}\)), and the forecast variance is given by\(\text{Var}(\hat{y})=\sigma^2 \left[1+\bm{x}^*(\bm{X}'\bm{X})^{-1}(\bm{x}^*)'\right].\)


Consider the simple time trend model where\(y_t = \beta_0 + \beta_1t\). Using the following results,\[
   \sum^{T}_{t=1}{t}=\frac{1}{2}T(T+1),\quad \sum^{T}_{t=1}{t^2}=\frac{1}{6}T(T+1)(2T+1)
\]derive the following expressions:

- \(\displaystyle\bm{X}'\bm{X}=\frac{1}{6}\left[
\begin{array}{cc}
  6T      & 3T(T+1) \\
  3T(T+1) & T(T+1)(2T+1) \\
\end{array}
\right]\)

\(\displaystyle\bm{X}'\bm{X}=\frac{1}{6}\left[
\begin{array}{cc}
  6T      & 3T(T+1) \\
  3T(T+1) & T(T+1)(2T+1) \\
\end{array}
\right]\)

- \(\displaystyle(\bm{X}'\bm{X})^{-1}=\frac{2}{T(T^2-1)}\left[
\begin{array}{cc}
  (T+1)(2T+1)   & -3(T+1) \\
  -3(T+1)       & 6 \\
\end{array}
\right]\)

\(\displaystyle(\bm{X}'\bm{X})^{-1}=\frac{2}{T(T^2-1)}\left[
\begin{array}{cc}
  (T+1)(2T+1)   & -3(T+1) \\
  -3(T+1)       & 6 \\
\end{array}
\right]\)

- \(\displaystyle\hat{\beta}_0=\frac{2}{T(T-1)}\left[(2T+1)\sum^T_{t=1}y_t-3\sum^T_{t=1}ty_t
\right]\)\(\displaystyle\hat{\beta}_1=\frac{6}{T(T^2-1)}\left[2\sum^T_{t=1}ty_t-(T+1)\sum^T_{t=1}y_t \right]\)

\(\displaystyle\hat{\beta}_0=\frac{2}{T(T-1)}\left[(2T+1)\sum^T_{t=1}y_t-3\sum^T_{t=1}ty_t
\right]\)


\(\displaystyle\hat{\beta}_1=\frac{6}{T(T^2-1)}\left[2\sum^T_{t=1}ty_t-(T+1)\sum^T_{t=1}y_t \right]\)

- \(\displaystyle\text{Var}(\hat{y}_{t})=\hat{\sigma}^2\left[1+\frac{2}{T(T-1)}\left(1-4T-6h+6\frac{(T+h)^2}{T+1}\right)\right]\)

\(\displaystyle\text{Var}(\hat{y}_{t})=\hat{\sigma}^2\left[1+\frac{2}{T(T-1)}\left(1-4T-6h+6\frac{(T+h)^2}{T+1}\right)\right]\)
