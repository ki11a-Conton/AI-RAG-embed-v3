
# Forecasting: Principles and Practice(3rd ed)


## 5.11Exercises

- Produce forecasts for the following series using whichever ofNAIVE(y),SNAIVE(y)orRW(y ~ drift())is more appropriate in each case:Australian Population (global_economy)Bricks (aus_production)NSW Lambs (aus_livestock)Household wealth (hh_budget).Australian takeaway food turnover (aus_retail).

Produce forecasts for the following series using whichever ofNAIVE(y),SNAIVE(y)orRW(y ~ drift())is more appropriate in each case:

- Australian Population (global_economy)
- Bricks (aus_production)
- NSW Lambs (aus_livestock)
- Household wealth (hh_budget).
- Australian takeaway food turnover (aus_retail).
- Use the Facebook stock price (data setgafa_stock) to do the following:Produce a time plot of the series.Produce forecasts using the drift method and plot them.Show that the forecasts are identical to extending the line drawn between the first and last observations.Try using some of the other benchmark functions to forecast the same data set. Which do you think is best? Why?

Use the Facebook stock price (data setgafa_stock) to do the following:

- Produce a time plot of the series.
- Produce forecasts using the drift method and plot them.
- Show that the forecasts are identical to extending the line drawn between the first and last observations.
- Try using some of the other benchmark functions to forecast the same data set. Which do you think is best? Why?
- Apply a seasonal naïve method to the quarterly Australian beer production data from 1992. Check if the residuals look like white noise, and plot the forecasts. The following code will help.# Extract data of interestrecent_production<-aus_production|>filter(year(Quarter)>=1992)# Define and estimate a modelfit<-recent_production|>model(SNAIVE(Beer))# Look at the residualsfit|>gg_tsresiduals()# Look a some forecastsfit|>forecast()|>autoplot(recent_production)What do you conclude?

Apply a seasonal naïve method to the quarterly Australian beer production data from 1992. Check if the residuals look like white noise, and plot the forecasts. The following code will help.


```
# Extract data of interest
recent_production <- aus_production |>
  filter(year(Quarter) >= 1992)
# Define and estimate a model
fit <- recent_production |> model(SNAIVE(Beer))
# Look at the residuals
fit |> gg_tsresiduals()
# Look a some forecasts
fit |> forecast() |> autoplot(recent_production)
```


What do you conclude?

- Repeat the previous exercise using the Australian Exports series fromglobal_economyand the Bricks series fromaus_production. Use whichever ofNAIVE()orSNAIVE()is more appropriate in each case.

Repeat the previous exercise using the Australian Exports series fromglobal_economyand the Bricks series fromaus_production. Use whichever ofNAIVE()orSNAIVE()is more appropriate in each case.

- Produce forecasts for the 7 Victorian series inaus_livestockusingSNAIVE(). Plot the resulting forecasts including the historical data. Is this a reasonable benchmark for these series?

Produce forecasts for the 7 Victorian series inaus_livestockusingSNAIVE(). Plot the resulting forecasts including the historical data. Is this a reasonable benchmark for these series?

- Are the following statements true or false? Explain your answer.Good forecast methods should have normally distributed residuals.A model with small residuals will give good forecasts.The best measure of forecast accuracy is MAPE.If your model doesn’t forecast well, you should make it more complicated.Always choose the model with the best forecast accuracy as measured on the test set.

Are the following statements true or false? Explain your answer.

- Good forecast methods should have normally distributed residuals.
- A model with small residuals will give good forecasts.
- The best measure of forecast accuracy is MAPE.
- If your model doesn’t forecast well, you should make it more complicated.
- Always choose the model with the best forecast accuracy as measured on the test set.
- For your retail time series (from Exercise 7 in Section2.10):Create a training dataset consisting of observations before 2011 usingmyseries_train<-myseries|>filter(year(Month)<2011)Check that your data have been split appropriately by producing the following plot.autoplot(myseries, Turnover)+autolayer(myseries_train, Turnover,colour ="red")Fit a seasonal naïve model usingSNAIVE()applied to your training data (myseries_train).fit<-myseries_train|>model(SNAIVE())Check the residuals.fit|>gg_tsresiduals()Do the residuals appear to be uncorrelated and normally distributed?Produce forecasts for the test datafc<-fit|>forecast(new_data =anti_join(myseries, myseries_train))fc|>autoplot(myseries)Compare the accuracy of your forecasts against the actual values.fit|>accuracy()fc|>accuracy(myseries)How sensitive are the accuracy measures to the amount of training data used?

For your retail time series (from Exercise 7 in Section2.10):

- Create a training dataset consisting of observations before 2011 usingmyseries_train<-myseries|>filter(year(Month)<2011)

Create a training dataset consisting of observations before 2011 using


```
myseries_train <- myseries |>
  filter(year(Month) < 2011)
```

- Check that your data have been split appropriately by producing the following plot.autoplot(myseries, Turnover)+autolayer(myseries_train, Turnover,colour ="red")

Check that your data have been split appropriately by producing the following plot.


```
autoplot(myseries, Turnover) +
  autolayer(myseries_train, Turnover, colour = "red")
```

- Fit a seasonal naïve model usingSNAIVE()applied to your training data (myseries_train).fit<-myseries_train|>model(SNAIVE())

Fit a seasonal naïve model usingSNAIVE()applied to your training data (myseries_train).


```
fit <- myseries_train |>
  model(SNAIVE())
```

- Check the residuals.fit|>gg_tsresiduals()Do the residuals appear to be uncorrelated and normally distributed?

Check the residuals.


```
fit |> gg_tsresiduals()
```


Do the residuals appear to be uncorrelated and normally distributed?

- Produce forecasts for the test datafc<-fit|>forecast(new_data =anti_join(myseries, myseries_train))fc|>autoplot(myseries)

Produce forecasts for the test data


```
fc <- fit |>
  forecast(new_data = anti_join(myseries, myseries_train))
fc |> autoplot(myseries)
```

- Compare the accuracy of your forecasts against the actual values.fit|>accuracy()fc|>accuracy(myseries)

Compare the accuracy of your forecasts against the actual values.


```
fit |> accuracy()
fc |> accuracy(myseries)
```

- How sensitive are the accuracy measures to the amount of training data used?

How sensitive are the accuracy measures to the amount of training data used?

- Consider the number of pigs slaughtered in New South Wales (data setaus_livestock).Produce some plots of the data in order to become familiar with it.Create a training set of 486 observations, withholding a test set of 72 observations (6 years).Try using various benchmark methods to forecast the training set and compare the results on the test set. Which method did best?Check the residuals of your preferred method. Do they resemble white noise?

Consider the number of pigs slaughtered in New South Wales (data setaus_livestock).

- Produce some plots of the data in order to become familiar with it.
- Create a training set of 486 observations, withholding a test set of 72 observations (6 years).
- Try using various benchmark methods to forecast the training set and compare the results on the test set. Which method did best?
- Check the residuals of your preferred method. Do they resemble white noise?
- Create a training set for household wealth (hh_budget) by withholding the last four years as a test set.Fit all the appropriate benchmark methods to the training set and forecast the periods covered by the test set.Compute the accuracy of your forecasts. Which method does best?Do the residuals from the best method resemble white noise?
- Create a training set for household wealth (hh_budget) by withholding the last four years as a test set.
- Fit all the appropriate benchmark methods to the training set and forecast the periods covered by the test set.
- Compute the accuracy of your forecasts. Which method does best?
- Do the residuals from the best method resemble white noise?
- Create a training set for Australian takeaway food turnover (aus_retail) by withholding the last four years as a test set.Fit all the appropriate benchmark methods to the training set and forecast the periods covered by the test set.Compute the accuracy of your forecasts. Which method does best?Do the residuals from the best method resemble white noise?
- Create a training set for Australian takeaway food turnover (aus_retail) by withholding the last four years as a test set.
- Fit all the appropriate benchmark methods to the training set and forecast the periods covered by the test set.
- Compute the accuracy of your forecasts. Which method does best?
- Do the residuals from the best method resemble white noise?
- We will use the Bricks data fromaus_production(Australian quarterly clay brick production 1956–2005) for this exercise.Use an STL decomposition to calculate the trend-cycle and seasonal indices. (Experiment with having fixed or changing seasonality.)Compute and plot the seasonally adjusted data.Use a naïve method to produce forecasts of the seasonally adjusted data.Usedecomposition_model()to reseasonalise the results, giving forecasts for the original data.Do the residuals look uncorrelated?Repeat with a robust STL decomposition. Does it make much difference?Compare forecasts fromdecomposition_model()with those fromSNAIVE(), using a test set comprising the last 2 years of data. Which is better?

We will use the Bricks data fromaus_production(Australian quarterly clay brick production 1956–2005) for this exercise.

- Use an STL decomposition to calculate the trend-cycle and seasonal indices. (Experiment with having fixed or changing seasonality.)
- Compute and plot the seasonally adjusted data.
- Use a naïve method to produce forecasts of the seasonally adjusted data.
- Usedecomposition_model()to reseasonalise the results, giving forecasts for the original data.
- Do the residuals look uncorrelated?
- Repeat with a robust STL decomposition. Does it make much difference?
- Compare forecasts fromdecomposition_model()with those fromSNAIVE(), using a test set comprising the last 2 years of data. Which is better?
- tourismcontains quarterly visitor nights (in thousands) from 1998 to 2017 for 76 regions of Australia.Extract data from the Gold Coast region usingfilter()and aggregate total overnight trips (sum overPurpose) usingsummarise(). Call this new datasetgc_tourism.Usingslice()orfilter(), create three training sets for this data excluding the last 1, 2 and 3 years. For example,gc_train_1 <- gc_tourism |> slice(1:(n()-4)).Compute one year of forecasts for each training set using the seasonal naïve (SNAIVE()) method. Call thesegc_fc_1,gc_fc_2andgc_fc_3, respectively.Useaccuracy()to compare the test set forecast accuracy using MAPE. Comment on these.

tourismcontains quarterly visitor nights (in thousands) from 1998 to 2017 for 76 regions of Australia.

- Extract data from the Gold Coast region usingfilter()and aggregate total overnight trips (sum overPurpose) usingsummarise(). Call this new datasetgc_tourism.

Extract data from the Gold Coast region usingfilter()and aggregate total overnight trips (sum overPurpose) usingsummarise(). Call this new datasetgc_tourism.

- Usingslice()orfilter(), create three training sets for this data excluding the last 1, 2 and 3 years. For example,gc_train_1 <- gc_tourism |> slice(1:(n()-4)).

Usingslice()orfilter(), create three training sets for this data excluding the last 1, 2 and 3 years. For example,gc_train_1 <- gc_tourism |> slice(1:(n()-4)).

- Compute one year of forecasts for each training set using the seasonal naïve (SNAIVE()) method. Call thesegc_fc_1,gc_fc_2andgc_fc_3, respectively.

Compute one year of forecasts for each training set using the seasonal naïve (SNAIVE()) method. Call thesegc_fc_1,gc_fc_2andgc_fc_3, respectively.

- Useaccuracy()to compare the test set forecast accuracy using MAPE. Comment on these.

Useaccuracy()to compare the test set forecast accuracy using MAPE. Comment on these.
