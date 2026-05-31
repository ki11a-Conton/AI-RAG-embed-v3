
# Forecasting: Principles and Practice(3rd ed)


## 9.11Exercises

- Figure9.32shows the ACFs for 36 random numbers, 360 random numbers and 1,000 random numbers.Explain the differences among these figures. Do they all indicate that the data are white noise?Figure 9.32: Left: ACF for a white noise series of 36 numbers. Middle: ACF for a white noise series of 360 numbers. Right: ACF for a white noise series of 1,000 numbers.Why are the critical values at different distances from the mean of zero? Why are the autocorrelations different in each figure when they each refer to white noise?

Figure9.32shows the ACFs for 36 random numbers, 360 random numbers and 1,000 random numbers.

- Explain the differences among these figures. Do they all indicate that the data are white noise?

Figure 9.32: Left: ACF for a white noise series of 36 numbers. Middle: ACF for a white noise series of 360 numbers. Right: ACF for a white noise series of 1,000 numbers.

- Why are the critical values at different distances from the mean of zero? Why are the autocorrelations different in each figure when they each refer to white noise?
- A classic example of a non-stationary series are stock prices. Plot the daily closing prices for Amazon stock (contained ingafa_stock), along with the ACF and PACF. Explain how each plot shows that the series is non-stationary and should be differenced.

A classic example of a non-stationary series are stock prices. Plot the daily closing prices for Amazon stock (contained ingafa_stock), along with the ACF and PACF. Explain how each plot shows that the series is non-stationary and should be differenced.

- For the following series, find an appropriate Box-Cox transformation and order of differencing in order to obtain stationary data.Turkish GDP fromglobal_economy.Accommodation takings in the state of Tasmania fromaus_accommodation.Monthly sales fromsouvenirs.

For the following series, find an appropriate Box-Cox transformation and order of differencing in order to obtain stationary data.

- Turkish GDP fromglobal_economy.
- Accommodation takings in the state of Tasmania fromaus_accommodation.
- Monthly sales fromsouvenirs.
- For thesouvenirsdata, write down the differences you chose above using backshift operator notation.

For thesouvenirsdata, write down the differences you chose above using backshift operator notation.

- For your retail data (from Exercise 7 in Section2.10), find the appropriate order of differencing (after transformation if necessary) to obtain stationary data.

For your retail data (from Exercise 7 in Section2.10), find the appropriate order of differencing (after transformation if necessary) to obtain stationary data.

- Simulate and plot some data from simple ARIMA models.Use the following R code to generate data from an AR(1) model with\(\phi_{1} = 0.6\)and\(\sigma^2=1\). The process starts with\(y_1=0\).y<-numeric(100)e<-rnorm(100)for(iin2:100)y[i]<-0.6*y[i-1]+e[i]sim<-tsibble(idx =seq_len(100),y =y,index =idx)Produce a time plot for the series. How does the plot change as you change\(\phi_1\)?Write your own code to generate data from an MA(1) model with\(\theta_{1}  =  0.6\)and\(\sigma^2=1\).Produce a time plot for the series. How does the plot change as you change\(\theta_1\)?Generate data from an ARMA(1,1) model with\(\phi_{1} = 0.6\),\(\theta_{1}  = 0.6\)and\(\sigma^2=1\).Generate data from an AR(2) model with\(\phi_{1} =-0.8\),\(\phi_{2} = 0.3\)and\(\sigma^2=1\). (Note that these parameters will give a non-stationary series.)Graph the latter two series and compare them.

Simulate and plot some data from simple ARIMA models.

- Use the following R code to generate data from an AR(1) model with\(\phi_{1} = 0.6\)and\(\sigma^2=1\). The process starts with\(y_1=0\).y<-numeric(100)e<-rnorm(100)for(iin2:100)y[i]<-0.6*y[i-1]+e[i]sim<-tsibble(idx =seq_len(100),y =y,index =idx)

Use the following R code to generate data from an AR(1) model with\(\phi_{1} = 0.6\)and\(\sigma^2=1\). The process starts with\(y_1=0\).


```
y <- numeric(100)
e <- rnorm(100)
for(i in 2:100)
  y[i] <- 0.6*y[i-1] + e[i]
sim <- tsibble(idx = seq_len(100), y = y, index = idx)
```

- Produce a time plot for the series. How does the plot change as you change\(\phi_1\)?

Produce a time plot for the series. How does the plot change as you change\(\phi_1\)?

- Write your own code to generate data from an MA(1) model with\(\theta_{1}  =  0.6\)and\(\sigma^2=1\).

Write your own code to generate data from an MA(1) model with\(\theta_{1}  =  0.6\)and\(\sigma^2=1\).

- Produce a time plot for the series. How does the plot change as you change\(\theta_1\)?

Produce a time plot for the series. How does the plot change as you change\(\theta_1\)?

- Generate data from an ARMA(1,1) model with\(\phi_{1} = 0.6\),\(\theta_{1}  = 0.6\)and\(\sigma^2=1\).

Generate data from an ARMA(1,1) model with\(\phi_{1} = 0.6\),\(\theta_{1}  = 0.6\)and\(\sigma^2=1\).

- Generate data from an AR(2) model with\(\phi_{1} =-0.8\),\(\phi_{2} = 0.3\)and\(\sigma^2=1\). (Note that these parameters will give a non-stationary series.)

Generate data from an AR(2) model with\(\phi_{1} =-0.8\),\(\phi_{2} = 0.3\)and\(\sigma^2=1\). (Note that these parameters will give a non-stationary series.)

- Graph the latter two series and compare them.

Graph the latter two series and compare them.

- Consideraus_airpassengers, the total number of passengers (in millions) from Australian air carriers for the period 1970-2011.UseARIMA()to find an appropriate ARIMA model. What model was selected. Check that the residuals look like white noise. Plot forecasts for the next 10 periods.Write the model in terms of the backshift operator.Plot forecasts from an ARIMA(0,1,0) model with drift and compare these to part a.Plot forecasts from an ARIMA(2,1,2) model with drift and compare these to parts a and c. Remove the constant and see what happens.Plot forecasts from an ARIMA(0,2,1) model with a constant. What happens?

Consideraus_airpassengers, the total number of passengers (in millions) from Australian air carriers for the period 1970-2011.

- UseARIMA()to find an appropriate ARIMA model. What model was selected. Check that the residuals look like white noise. Plot forecasts for the next 10 periods.
- Write the model in terms of the backshift operator.
- Plot forecasts from an ARIMA(0,1,0) model with drift and compare these to part a.
- Plot forecasts from an ARIMA(2,1,2) model with drift and compare these to parts a and c. Remove the constant and see what happens.
- Plot forecasts from an ARIMA(0,2,1) model with a constant. What happens?
- For the United States GDP series (fromglobal_economy):if necessary, find a suitable Box-Cox transformation for the data;fit a suitable ARIMA model to the transformed data usingARIMA();try some other plausible models by experimenting with the orders chosen;choose what you think is the best model and check the residual diagnostics;produce forecasts of your fitted model. Do the forecasts look reasonable?compare the results with what you would obtain usingETS()(with no transformation).

For the United States GDP series (fromglobal_economy):

- if necessary, find a suitable Box-Cox transformation for the data;
- fit a suitable ARIMA model to the transformed data usingARIMA();
- try some other plausible models by experimenting with the orders chosen;
- choose what you think is the best model and check the residual diagnostics;
- produce forecasts of your fitted model. Do the forecasts look reasonable?
- compare the results with what you would obtain usingETS()(with no transformation).
- Consideraus_arrivals, the quarterly number of international visitors to Australia from several countries for the period 1981 Q1 – 2012 Q3.Select one country and describe the time plot.Use differencing to obtain stationary data.What can you learn from the ACF graph of the differenced data?What can you learn from the PACF graph of the differenced data?What model do these graphs suggest?DoesARIMA()give the same model that you chose? If not, which model do you think is better?Write the model in terms of the backshift operator, then without using the backshift operator.

Consideraus_arrivals, the quarterly number of international visitors to Australia from several countries for the period 1981 Q1 – 2012 Q3.

- Select one country and describe the time plot.
- Use differencing to obtain stationary data.
- What can you learn from the ACF graph of the differenced data?
- What can you learn from the PACF graph of the differenced data?
- What model do these graphs suggest?
- DoesARIMA()give the same model that you chose? If not, which model do you think is better?
- Write the model in terms of the backshift operator, then without using the backshift operator.
- Choose a series fromus_employment, the total employment in different industries in the United States.Produce an STL decomposition of the data and describe the trend and seasonality.Do the data need transforming? If so, find a suitable transformation.Are the data stationary? If not, find an appropriate differencing which yields stationary data.Identify a couple of ARIMA models that might be useful in describing the time series. Which of your models is the best according to their AICc values?Estimate the parameters of your best model and do diagnostic testing on the residuals. Do the residuals resemble white noise? If not, try to find another ARIMA model which fits better.Forecast the next 3 years of data. Get the latest figures fromhttps://fred.stlouisfed.org/categories/11to check the accuracy of your forecasts.Eventually, the prediction intervals are so wide that the forecasts are not particularly useful. How many years of forecasts do you think are sufficiently accurate to be usable?

Choose a series fromus_employment, the total employment in different industries in the United States.

- Produce an STL decomposition of the data and describe the trend and seasonality.
- Do the data need transforming? If so, find a suitable transformation.
- Are the data stationary? If not, find an appropriate differencing which yields stationary data.
- Identify a couple of ARIMA models that might be useful in describing the time series. Which of your models is the best according to their AICc values?
- Estimate the parameters of your best model and do diagnostic testing on the residuals. Do the residuals resemble white noise? If not, try to find another ARIMA model which fits better.
- Forecast the next 3 years of data. Get the latest figures fromhttps://fred.stlouisfed.org/categories/11to check the accuracy of your forecasts.
- Eventually, the prediction intervals are so wide that the forecasts are not particularly useful. How many years of forecasts do you think are sufficiently accurate to be usable?
- Choose one of the following seasonal time series: the Australian production of electricity, cement, or gas (fromaus_production).Do the data need transforming? If so, find a suitable transformation.Are the data stationary? If not, find an appropriate differencing which yields stationary data.Identify a couple of ARIMA models that might be useful in describing the time series. Which of your models is the best according to their AIC values?Estimate the parameters of your best model and do diagnostic testing on the residuals. Do the residuals resemble white noise? If not, try to find another ARIMA model which fits better.Forecast the next 24 months of data using your preferred model.Compare the forecasts obtained usingETS().

Choose one of the following seasonal time series: the Australian production of electricity, cement, or gas (fromaus_production).

- Do the data need transforming? If so, find a suitable transformation.
- Are the data stationary? If not, find an appropriate differencing which yields stationary data.
- Identify a couple of ARIMA models that might be useful in describing the time series. Which of your models is the best according to their AIC values?
- Estimate the parameters of your best model and do diagnostic testing on the residuals. Do the residuals resemble white noise? If not, try to find another ARIMA model which fits better.
- Forecast the next 24 months of data using your preferred model.
- Compare the forecasts obtained usingETS().
- For the same time series you used in the previous exercise, try using a non-seasonal model applied to the seasonally adjusted data obtained from STL. Compare the forecasts with those obtained in the previous exercise. Which do you think is the best approach?

For the same time series you used in the previous exercise, try using a non-seasonal model applied to the seasonally adjusted data obtained from STL. Compare the forecasts with those obtained in the previous exercise. Which do you think is the best approach?

- For the Australian tourism data (fromtourism):Fit ARIMA models for each time series.Produce forecasts of your fitted models.Check the forecasts for the “Snowy Mountains” and “Melbourne” regions. Do they look reasonable?

For the Australian tourism data (fromtourism):

- Fit ARIMA models for each time series.
- Produce forecasts of your fitted models.
- Check the forecasts for the “Snowy Mountains” and “Melbourne” regions. Do they look reasonable?
- For your retail time series (Exercise 5 above):develop an appropriate seasonal ARIMA model;compare the forecasts with those you obtained in earlier chapters;Obtain up-to-date retail data from theABS website(Cat 8501.0, Table 11), and compare your forecasts with the actual numbers. How good were the forecasts from the various models?

For your retail time series (Exercise 5 above):

- develop an appropriate seasonal ARIMA model;
- compare the forecasts with those you obtained in earlier chapters;
- Obtain up-to-date retail data from theABS website(Cat 8501.0, Table 11), and compare your forecasts with the actual numbers. How good were the forecasts from the various models?
- Consider the number of Snowshoe Hare furs traded by the Hudson Bay Company between 1845 and 1935 (data setpelt).Produce a time plot of the time series.Assume you decide to fit the following model:\[
   y_t = c + \phi_1 y_{t-1} + \phi_2 y_{t-2} + \phi_3 y_{t-3} + \phi_4 y_{t-4} + \varepsilon_t,
\]where\(\varepsilon_t\)is a white noise series. What sort of ARIMA model is this (i.e., what are\(p\),\(d\), and\(q\))?By examining the ACF and PACF of the data, explain why this model is appropriate.The last five values of the series are given below:Year19311932193319341935Number of hare pelts1952082110897608166015760The estimated parameters are\(c = 30993\),\(\phi_1 = 0.82\),\(\phi_2 = -0.29\),\(\phi_3 = -0.01\), and\(\phi_4 = -0.22\).
Without using theforecast()function, calculate forecasts for the next three years (1936–1939).Now fit the model in R and obtain the forecasts usingforecast(). How are they different from yours? Why?

Consider the number of Snowshoe Hare furs traded by the Hudson Bay Company between 1845 and 1935 (data setpelt).

- Produce a time plot of the time series.

Produce a time plot of the time series.

- Assume you decide to fit the following model:\[
   y_t = c + \phi_1 y_{t-1} + \phi_2 y_{t-2} + \phi_3 y_{t-3} + \phi_4 y_{t-4} + \varepsilon_t,
\]where\(\varepsilon_t\)is a white noise series. What sort of ARIMA model is this (i.e., what are\(p\),\(d\), and\(q\))?

Assume you decide to fit the following model:\[
   y_t = c + \phi_1 y_{t-1} + \phi_2 y_{t-2} + \phi_3 y_{t-3} + \phi_4 y_{t-4} + \varepsilon_t,
\]where\(\varepsilon_t\)is a white noise series. What sort of ARIMA model is this (i.e., what are\(p\),\(d\), and\(q\))?

- By examining the ACF and PACF of the data, explain why this model is appropriate.

By examining the ACF and PACF of the data, explain why this model is appropriate.

- The last five values of the series are given below:Year19311932193319341935Number of hare pelts1952082110897608166015760The estimated parameters are\(c = 30993\),\(\phi_1 = 0.82\),\(\phi_2 = -0.29\),\(\phi_3 = -0.01\), and\(\phi_4 = -0.22\).
Without using theforecast()function, calculate forecasts for the next three years (1936–1939).

The last five values of the series are given below:


The estimated parameters are\(c = 30993\),\(\phi_1 = 0.82\),\(\phi_2 = -0.29\),\(\phi_3 = -0.01\), and\(\phi_4 = -0.22\).
Without using theforecast()function, calculate forecasts for the next three years (1936–1939).

- Now fit the model in R and obtain the forecasts usingforecast(). How are they different from yours? Why?

Now fit the model in R and obtain the forecasts usingforecast(). How are they different from yours? Why?

- The population of Switzerland from 1960 to 2017 is in data setglobal_economy.Produce a time plot of the data.You decide to fit the following model to the series:\[y_t = c + y_{t-1} + \phi_1 (y_{t-1} - y_{t-2}) + \phi_2 (y_{t-2} - y_{t-3}) + \phi_3( y_{t-3} - y_{t-4}) + \varepsilon_t\]where\(y_t\)is the Population in year\(t\)and\(\varepsilon_t\)is a white noise series.
What sort of ARIMA model is this (i.e., what are\(p\),\(d\), and\(q\))?Explain why this model was chosen using the ACF and PACF of the differenced series.The last five values of the series are given below.Year20132014201520162017Population (millions)8.098.198.288.378.47The estimated parameters are\(c = 0.0053\),\(\phi_1 = 1.64\),\(\phi_2 = -1.17\), and\(\phi_3 = 0.45\).
Without using theforecast()function, calculate forecasts for the next three years (2018–2020).Now fit the model in R and obtain the forecasts from the same model. How are they different from yours? Why?

The population of Switzerland from 1960 to 2017 is in data setglobal_economy.

- Produce a time plot of the data.

Produce a time plot of the data.

- You decide to fit the following model to the series:\[y_t = c + y_{t-1} + \phi_1 (y_{t-1} - y_{t-2}) + \phi_2 (y_{t-2} - y_{t-3}) + \phi_3( y_{t-3} - y_{t-4}) + \varepsilon_t\]where\(y_t\)is the Population in year\(t\)and\(\varepsilon_t\)is a white noise series.
What sort of ARIMA model is this (i.e., what are\(p\),\(d\), and\(q\))?

You decide to fit the following model to the series:\[y_t = c + y_{t-1} + \phi_1 (y_{t-1} - y_{t-2}) + \phi_2 (y_{t-2} - y_{t-3}) + \phi_3( y_{t-3} - y_{t-4}) + \varepsilon_t\]where\(y_t\)is the Population in year\(t\)and\(\varepsilon_t\)is a white noise series.
What sort of ARIMA model is this (i.e., what are\(p\),\(d\), and\(q\))?

- Explain why this model was chosen using the ACF and PACF of the differenced series.

Explain why this model was chosen using the ACF and PACF of the differenced series.

- The last five values of the series are given below.Year20132014201520162017Population (millions)8.098.198.288.378.47The estimated parameters are\(c = 0.0053\),\(\phi_1 = 1.64\),\(\phi_2 = -1.17\), and\(\phi_3 = 0.45\).
Without using theforecast()function, calculate forecasts for the next three years (2018–2020).

The last five values of the series are given below.


The estimated parameters are\(c = 0.0053\),\(\phi_1 = 1.64\),\(\phi_2 = -1.17\), and\(\phi_3 = 0.45\).
Without using theforecast()function, calculate forecasts for the next three years (2018–2020).

- Now fit the model in R and obtain the forecasts from the same model. How are they different from yours? Why?

Now fit the model in R and obtain the forecasts from the same model. How are they different from yours? Why?
