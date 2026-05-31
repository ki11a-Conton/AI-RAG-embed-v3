
# Forecasting: Principles and Practice(3rd ed)


## 10.7Exercises

- This exercise uses data setLakeHurongiving the level of Lake Huron from 1875–1972.Convert the data to a tsibble object using theas_tsibble()function.Fit a piecewise linear trend model to the Lake Huron data with a knot at 1920 and an ARMA error structure.Forecast the level for the next 30 years. Do you think the extrapolated linear trend is realistic?

This exercise uses data setLakeHurongiving the level of Lake Huron from 1875–1972.

- Convert the data to a tsibble object using theas_tsibble()function.
- Fit a piecewise linear trend model to the Lake Huron data with a knot at 1920 and an ARMA error structure.
- Forecast the level for the next 30 years. Do you think the extrapolated linear trend is realistic?
- Repeat Exercise 4 from Section7.10, but this time adding in ARIMA errors to address the autocorrelations in the residuals.How much difference does the ARIMA error process make to the regression coefficients?How much difference does the ARIMA error process make to the forecasts?Check the residuals of the fitted model to ensure the ARIMA process has adequately addressed the autocorrelations seen in theTSLMmodel.

Repeat Exercise 4 from Section7.10, but this time adding in ARIMA errors to address the autocorrelations in the residuals.

- How much difference does the ARIMA error process make to the regression coefficients?
- How much difference does the ARIMA error process make to the forecasts?
- Check the residuals of the fitted model to ensure the ARIMA process has adequately addressed the autocorrelations seen in theTSLMmodel.
- Repeat the daily electricity example, but instead of using a quadratic function of temperature, use a piecewise linear function with the “knot” around 25 degrees Celsius (use predictorsTemperature&Temp2). How can you optimise the choice of knot?The data can be created as follows.vic_elec_daily<-vic_elec|>filter(year(Time)==2014)|>index_by(Date =date(Time))|>summarise(Demand =sum(Demand)/1e3,Temperature =max(Temperature),Holiday =any(Holiday))|>mutate(Temp2 =I(pmax(Temperature-25,0)),Day_Type =case_when(Holiday~"Holiday",wday(Date)%in%2:6~"Weekday",TRUE~"Weekend"))

Repeat the daily electricity example, but instead of using a quadratic function of temperature, use a piecewise linear function with the “knot” around 25 degrees Celsius (use predictorsTemperature&Temp2). How can you optimise the choice of knot?


The data can be created as follows.


```
vic_elec_daily <- vic_elec |>
  filter(year(Time) == 2014) |>
  index_by(Date = date(Time)) |>
  summarise(
    Demand = sum(Demand)/1e3,
    Temperature = max(Temperature),
    Holiday = any(Holiday)) |>
  mutate(
    Temp2 = I(pmax(Temperature-25,0)),
    Day_Type = case_when(
      Holiday ~ "Holiday",
      wday(Date) %in% 2:6 ~ "Weekday",
      TRUE ~ "Weekend"))
```

- This exercise concernsaus_accommodation: the total quarterly takings from accommodation and the room occupancy level for hotels, motels, and guest houses in Australia, between January 1998 and June 2016. Total quarterly takings are in millions of Australian dollars.Compute the CPI-adjusted takings and plot the result for each stateFor each state, fit a dynamic regression model of CPI-adjusted takings with seasonal dummy variables, a piecewise linear time trend with one knot at 2008 Q1, and ARIMA errors.Check that the residuals of the model look like white noise.Forecast the takings for each state to the end of 2017. (Hint: You will need to produce forecasts of the CPI first.)What sources of uncertainty have not been taken into account in the prediction intervals?

This exercise concernsaus_accommodation: the total quarterly takings from accommodation and the room occupancy level for hotels, motels, and guest houses in Australia, between January 1998 and June 2016. Total quarterly takings are in millions of Australian dollars.

- Compute the CPI-adjusted takings and plot the result for each state
- For each state, fit a dynamic regression model of CPI-adjusted takings with seasonal dummy variables, a piecewise linear time trend with one knot at 2008 Q1, and ARIMA errors.
- Check that the residuals of the model look like white noise.
- Forecast the takings for each state to the end of 2017. (Hint: You will need to produce forecasts of the CPI first.)
- What sources of uncertainty have not been taken into account in the prediction intervals?
- We fitted a harmonic regression model to part of theus_gasolineseries in Exercise 5 in Section7.10. We will now revisit this model, and extend it to include more data and ARMA errors.UsingTSLM(), fit a harmonic regression with a piecewise linear time trend to the full series. Select the position of the knots in the trend and the appropriate number of Fourier terms to include by minimising the AICc or CV value.Now refit the model usingARIMA()to allow for correlated errors, keeping the same predictor variables as you used withTSLM().Check the residuals of the final model using thegg_tsresiduals()function and a Ljung-Box test. Do they look sufficiently like white noise to continue? If not, try modifying your model, or removing the first few years of data.Once you have a model with white noise residuals, produce forecasts for the next year.

We fitted a harmonic regression model to part of theus_gasolineseries in Exercise 5 in Section7.10. We will now revisit this model, and extend it to include more data and ARMA errors.

- UsingTSLM(), fit a harmonic regression with a piecewise linear time trend to the full series. Select the position of the knots in the trend and the appropriate number of Fourier terms to include by minimising the AICc or CV value.
- Now refit the model usingARIMA()to allow for correlated errors, keeping the same predictor variables as you used withTSLM().
- Check the residuals of the final model using thegg_tsresiduals()function and a Ljung-Box test. Do they look sufficiently like white noise to continue? If not, try modifying your model, or removing the first few years of data.
- Once you have a model with white noise residuals, produce forecasts for the next year.
- Electricity consumption is often modelled as a function of temperature. Temperature is measured by daily heating degrees and cooling degrees. Heating degrees is\(18^\circ\)C minus the average daily temperature when the daily average is below\(18^\circ\)C; otherwise it is zero. This provides a measure of our need to heat ourselves as temperature falls. Cooling degrees measures our need to cool ourselves as the temperature rises. It is defined as the average daily temperature minus\(18^\circ\)C when the daily average is above\(18^\circ\)C; otherwise it is zero. Let\(y_t\)denote the monthly total of kilowatt-hours of electricity used, let\(x_{1,t}\)denote the monthly total of heating degrees, and let\(x_{2,t}\)denote the monthly total of cooling degrees.An analyst fits the following model to a set of such data:\[y^*_t = \beta_1x^*_{1,t} + \beta_2x^*_{2,t} + \eta_t,\]where\[(1-\Phi_{1}B^{12} - \Phi_{2}B^{24})(1-B)(1-B^{12})\eta_t = (1+\theta_1 B)\varepsilon_t\]and\(y^*_t = \log(y_t)\),\(x^*_{1,t} = \sqrt{x_{1,t}}\)and\(x^*_{2,t}=\sqrt{x_{2,t}}\).What sort of ARIMA model is identified for\(\eta_t\)?The estimated coefficients areParameterEstimates.e.\(Z\)\(P\)-value\(\beta_1\)0.00770.00154.980.000\(\beta_2\)0.02080.00239.230.000\(\theta_1\)-0.58300.07208.100.000\(\Phi_{1}\)-0.53730.0856-6.270.000\(\Phi_{2}\)-0.46670.0862-5.410.000Explain what the estimates of\(\beta_1\)and\(\beta_2\)tell us about electricity consumption.Write the equation in a form more suitable for forecasting.Describe how this model could be used to forecast electricity demand for the next 12 months.Explain why the\(\eta_t\)term should be modelled with an ARIMA model rather than modelling the data using a standard regression package. In your discussion, comment on the properties of the estimates, the validity of the standard regression results, and the importance of the\(\eta_t\)model in producing forecasts.

Electricity consumption is often modelled as a function of temperature. Temperature is measured by daily heating degrees and cooling degrees. Heating degrees is\(18^\circ\)C minus the average daily temperature when the daily average is below\(18^\circ\)C; otherwise it is zero. This provides a measure of our need to heat ourselves as temperature falls. Cooling degrees measures our need to cool ourselves as the temperature rises. It is defined as the average daily temperature minus\(18^\circ\)C when the daily average is above\(18^\circ\)C; otherwise it is zero. Let\(y_t\)denote the monthly total of kilowatt-hours of electricity used, let\(x_{1,t}\)denote the monthly total of heating degrees, and let\(x_{2,t}\)denote the monthly total of cooling degrees.


An analyst fits the following model to a set of such data:\[y^*_t = \beta_1x^*_{1,t} + \beta_2x^*_{2,t} + \eta_t,\]where\[(1-\Phi_{1}B^{12} - \Phi_{2}B^{24})(1-B)(1-B^{12})\eta_t = (1+\theta_1 B)\varepsilon_t\]and\(y^*_t = \log(y_t)\),\(x^*_{1,t} = \sqrt{x_{1,t}}\)and\(x^*_{2,t}=\sqrt{x_{2,t}}\).

- What sort of ARIMA model is identified for\(\eta_t\)?

What sort of ARIMA model is identified for\(\eta_t\)?

- The estimated coefficients are

The estimated coefficients are


Explain what the estimates of\(\beta_1\)and\(\beta_2\)tell us about electricity consumption.

- Write the equation in a form more suitable for forecasting.
- Describe how this model could be used to forecast electricity demand for the next 12 months.
- Explain why the\(\eta_t\)term should be modelled with an ARIMA model rather than modelling the data using a standard regression package. In your discussion, comment on the properties of the estimates, the validity of the standard regression results, and the importance of the\(\eta_t\)model in producing forecasts.
- For the retail time series considered in earlier chapters:Develop an appropriate dynamic regression model with Fourier terms for the seasonality. Use the AICc to select the number of Fourier terms to include in the model. (You will probably need to use the same Box-Cox transformation you identified previously.)Check the residuals of the fitted model. Does the residual series look like white noise?Compare the forecasts with those you obtained earlier using alternative models.

For the retail time series considered in earlier chapters:

- Develop an appropriate dynamic regression model with Fourier terms for the seasonality. Use the AICc to select the number of Fourier terms to include in the model. (You will probably need to use the same Box-Cox transformation you identified previously.)
- Check the residuals of the fitted model. Does the residual series look like white noise?
- Compare the forecasts with those you obtained earlier using alternative models.