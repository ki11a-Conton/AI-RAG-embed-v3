
# Forecasting: Principles and Practice(3rd ed)


## 8.8Exercises

- Consider the the number of pigs slaughtered in Victoria, available in theaus_livestockdataset.Use theETS()function to estimate the equivalent model for simple exponential smoothing. Find the optimal values of\(\alpha\)and\(\ell_0\), and generate forecasts for the next four months.Compute a 95% prediction interval for the first forecast using\(\hat{y} \pm 1.96s\)where\(s\)is the standard deviation of the residuals. Compare your interval with the interval produced by R.

Consider the the number of pigs slaughtered in Victoria, available in theaus_livestockdataset.

- Use theETS()function to estimate the equivalent model for simple exponential smoothing. Find the optimal values of\(\alpha\)and\(\ell_0\), and generate forecasts for the next four months.
- Compute a 95% prediction interval for the first forecast using\(\hat{y} \pm 1.96s\)where\(s\)is the standard deviation of the residuals. Compare your interval with the interval produced by R.
- Write your own function to implement simple exponential smoothing. The function should take argumentsy(the time series),alpha(the smoothing parameter\(\alpha\)) andlevel(the initial level\(\ell_0\)). It should return the forecast of the next observation in the series. Does it give the same forecast asETS()?

Write your own function to implement simple exponential smoothing. The function should take argumentsy(the time series),alpha(the smoothing parameter\(\alpha\)) andlevel(the initial level\(\ell_0\)). It should return the forecast of the next observation in the series. Does it give the same forecast asETS()?

- Modify your function from the previous exercise to return the sum of squared errors rather than the forecast of the next observation. Then use theoptim()function to find the optimal values of\(\alpha\)and\(\ell_0\). Do you get the same values as theETS()function?

Modify your function from the previous exercise to return the sum of squared errors rather than the forecast of the next observation. Then use theoptim()function to find the optimal values of\(\alpha\)and\(\ell_0\). Do you get the same values as theETS()function?

- Combine your previous two functions to produce a function that both finds the optimal values of\(\alpha\)and\(\ell_0\), and produces a forecast of the next observation in the series.

Combine your previous two functions to produce a function that both finds the optimal values of\(\alpha\)and\(\ell_0\), and produces a forecast of the next observation in the series.

- Data setglobal_economycontains the annual Exports from many countries. Select one country to analyse.Plot the Exports series and discuss the main features of the data.Use an ETS(A,N,N) model to forecast the series, and plot the forecasts.Compute the RMSE values for the training data.Compare the results to those from an ETS(A,A,N) model. (Remember that the trended model is using one more parameter than the simpler model.) Discuss the merits of the two forecasting methods for this data set.Compare the forecasts from both methods. Which do you think is best?Calculate a 95% prediction interval for the first forecast for each model, using the RMSE values and assuming normal errors. Compare your intervals with those produced using R.

Data setglobal_economycontains the annual Exports from many countries. Select one country to analyse.

- Plot the Exports series and discuss the main features of the data.
- Use an ETS(A,N,N) model to forecast the series, and plot the forecasts.
- Compute the RMSE values for the training data.
- Compare the results to those from an ETS(A,A,N) model. (Remember that the trended model is using one more parameter than the simpler model.) Discuss the merits of the two forecasting methods for this data set.
- Compare the forecasts from both methods. Which do you think is best?
- Calculate a 95% prediction interval for the first forecast for each model, using the RMSE values and assuming normal errors. Compare your intervals with those produced using R.
- Forecast the Chinese GDP from theglobal_economydata set using an ETS model. Experiment with the various options in theETS()function to see how much the forecasts change with damped trend, or with a Box-Cox transformation. Try to develop an intuition of what each is doing to the forecasts.[Hint: use a relatively large value ofhwhen forecasting, so you can clearly see the differences between the various options when plotting the forecasts.]

Forecast the Chinese GDP from theglobal_economydata set using an ETS model. Experiment with the various options in theETS()function to see how much the forecasts change with damped trend, or with a Box-Cox transformation. Try to develop an intuition of what each is doing to the forecasts.


[Hint: use a relatively large value ofhwhen forecasting, so you can clearly see the differences between the various options when plotting the forecasts.]

- Find an ETS model for the Gas data fromaus_productionand forecast the next few years. Why is multiplicative seasonality necessary here? Experiment with making the trend damped. Does it improve the forecasts?

Find an ETS model for the Gas data fromaus_productionand forecast the next few years. Why is multiplicative seasonality necessary here? Experiment with making the trend damped. Does it improve the forecasts?

- Recall your retail time series data (from Exercise 7 in Section2.10).Why is multiplicative seasonality necessary for this series?Apply Holt-Winters’ multiplicative method to the data. Experiment with making the trend damped.Compare the RMSE of the one-step forecasts from the two methods. Which do you prefer?Check that the residuals from the best method look like white noise.Now find the test set RMSE, while training the model to the end of 2010. Can you beat the seasonal naïve approach from Exercise 7 in Section5.11?

Recall your retail time series data (from Exercise 7 in Section2.10).

- Why is multiplicative seasonality necessary for this series?
- Apply Holt-Winters’ multiplicative method to the data. Experiment with making the trend damped.
- Compare the RMSE of the one-step forecasts from the two methods. Which do you prefer?
- Check that the residuals from the best method look like white noise.
- Now find the test set RMSE, while training the model to the end of 2010. Can you beat the seasonal naïve approach from Exercise 7 in Section5.11?
- For the same retail data, try an STL decomposition applied to the Box-Cox transformed series, followed by ETS on the seasonally adjusted data. How does that compare with your best previous forecasts on the test set?

For the same retail data, try an STL decomposition applied to the Box-Cox transformed series, followed by ETS on the seasonally adjusted data. How does that compare with your best previous forecasts on the test set?

- Compute the total domestic overnight trips across Australia from thetourismdataset.Plot the data and describe the main features of the series.Decompose the series using STL and obtain the seasonally adjusted data.Forecast the next two years of the series using an additive damped trend method applied to the seasonally adjusted data. (This can be specified usingdecomposition_model().)Forecast the next two years of the series using an appropriate model for Holt’s linear method applied to the seasonally adjusted data (as before but without damped trend).Now useETS()to choose a seasonal model for the data.Compare the RMSE of the ETS model with the RMSE of the models you obtained using STL decompositions. Which gives the better in-sample fits?Compare the forecasts from the three approaches? Which seems most reasonable?Check the residuals of your preferred model.

Compute the total domestic overnight trips across Australia from thetourismdataset.

- Plot the data and describe the main features of the series.
- Decompose the series using STL and obtain the seasonally adjusted data.
- Forecast the next two years of the series using an additive damped trend method applied to the seasonally adjusted data. (This can be specified usingdecomposition_model().)
- Forecast the next two years of the series using an appropriate model for Holt’s linear method applied to the seasonally adjusted data (as before but without damped trend).
- Now useETS()to choose a seasonal model for the data.
- Compare the RMSE of the ETS model with the RMSE of the models you obtained using STL decompositions. Which gives the better in-sample fits?
- Compare the forecasts from the three approaches? Which seems most reasonable?
- Check the residuals of your preferred model.
- For this exercise use the quarterly number of arrivals to Australia from New Zealand, 1981 Q1 – 2012 Q3, from data setaus_arrivals.Make a time plot of your data and describe the main features of the series.Create a training set that withholds the last two years of available data. Forecast the test set using an appropriate model for Holt-Winters’ multiplicative method.Why is multiplicative seasonality necessary here?Forecast the two-year test set using each of the following methods:an ETS model;an additive ETS model applied to a log transformed series;a seasonal naïve method;an STL decomposition applied to the log transformed data followed by an ETS model applied to the seasonally adjusted (transformed) data.Which method gives the best forecasts? Does it pass the residual tests?Compare the same four methods using time series cross-validation instead of using a training and test set. Do you come to the same conclusions?

For this exercise use the quarterly number of arrivals to Australia from New Zealand, 1981 Q1 – 2012 Q3, from data setaus_arrivals.

- Make a time plot of your data and describe the main features of the series.
- Create a training set that withholds the last two years of available data. Forecast the test set using an appropriate model for Holt-Winters’ multiplicative method.
- Why is multiplicative seasonality necessary here?
- Forecast the two-year test set using each of the following methods:an ETS model;an additive ETS model applied to a log transformed series;a seasonal naïve method;an STL decomposition applied to the log transformed data followed by an ETS model applied to the seasonally adjusted (transformed) data.
- an ETS model;
- an additive ETS model applied to a log transformed series;
- a seasonal naïve method;
- an STL decomposition applied to the log transformed data followed by an ETS model applied to the seasonally adjusted (transformed) data.
- Which method gives the best forecasts? Does it pass the residual tests?
- Compare the same four methods using time series cross-validation instead of using a training and test set. Do you come to the same conclusions?
- Apply cross-validation techniques to produce 1 year ahead ETS and seasonal naïve forecasts for Portland cement production (fromaus_production). Use a stretching data window with initial size of 5 years, and increment the window by one observation.Compute the MSE of the resulting\(4\)-step-ahead errors. Comment on which forecasts are more accurate. Is this what you expected?
- Apply cross-validation techniques to produce 1 year ahead ETS and seasonal naïve forecasts for Portland cement production (fromaus_production). Use a stretching data window with initial size of 5 years, and increment the window by one observation.
- Compute the MSE of the resulting\(4\)-step-ahead errors. Comment on which forecasts are more accurate. Is this what you expected?
- CompareETS(),SNAIVE()anddecomposition_model(STL, ???)on the following five time series. You might need to use a Box-Cox transformation for the STL decomposition forecasts. Use a test set of three years to decide what gives the best forecasts.Beer and bricks production fromaus_production.Cost of drug subsidies for diabetes (ATC2 == "A10") and corticosteroids (ATC2 == "H02") fromPBS.Total food retailing turnover for Australia fromaus_retail.

CompareETS(),SNAIVE()anddecomposition_model(STL, ???)on the following five time series. You might need to use a Box-Cox transformation for the STL decomposition forecasts. Use a test set of three years to decide what gives the best forecasts.

- Beer and bricks production fromaus_production.
- Cost of drug subsidies for diabetes (ATC2 == "A10") and corticosteroids (ATC2 == "H02") fromPBS.
- Total food retailing turnover for Australia fromaus_retail.
- UseETS()to select an appropriate model for the following series: total number of trips across Australia usingtourism, the closing prices for the four stocks ingafa_stock, and the lynx series inpelt. Does it always give good forecasts?Find an example where it does not work well. Can you figure out why?
- UseETS()to select an appropriate model for the following series: total number of trips across Australia usingtourism, the closing prices for the four stocks ingafa_stock, and the lynx series inpelt. Does it always give good forecasts?

UseETS()to select an appropriate model for the following series: total number of trips across Australia usingtourism, the closing prices for the four stocks ingafa_stock, and the lynx series inpelt. Does it always give good forecasts?

- Find an example where it does not work well. Can you figure out why?

Find an example where it does not work well. Can you figure out why?

- Show that the point forecasts from an ETS(M,A,M) model are the same as those obtained using Holt-Winters’ multiplicative method.

Show that the point forecasts from an ETS(M,A,M) model are the same as those obtained using Holt-Winters’ multiplicative method.

- Show that the forecast variance for an ETS(A,N,N) model is given by\[
\sigma^2\left[1+\alpha^2(h-1)\right].
\]

Show that the forecast variance for an ETS(A,N,N) model is given by\[
\sigma^2\left[1+\alpha^2(h-1)\right].
\]

- Write down 95% prediction intervals for an ETS(A,N,N) model as a function of\(\ell_T\),\(\alpha\),\(h\)and\(\sigma\), assuming normally distributed errors.

Write down 95% prediction intervals for an ETS(A,N,N) model as a function of\(\ell_T\),\(\alpha\),\(h\)and\(\sigma\), assuming normally distributed errors.
