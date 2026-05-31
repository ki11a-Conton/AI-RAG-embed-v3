
# Forecasting: Principles and Practice(3rd ed)


## 7.2Least squares estimation


In practice, of course, we have a collection of observations but we do not know the values of the coefficients\(\beta_0,\beta_1, \dots, \beta_k\). These need to be estimated from the data.


The least squares principle provides a way of choosing the coefficients effectively by minimising the sum of the squared errors. That is, we choose the values of\(\beta_0, \beta_1, \dots, \beta_k\)that minimise\[
  \sum_{t=1}^T \varepsilon_t^2 = \sum_{t=1}^T (y_t -
  \beta_{0} - \beta_{1} x_{1,t} - \beta_{2} x_{2,t} - \cdots - \beta_{k} x_{k,t})^2.
\]


This is calledleast squaresestimation because it gives the least value for the sum of squared errors. Finding the best estimates of the coefficients is often called “fitting” the model to the data, or sometimes “learning” or “training” the model. The line shown in Figure7.3was obtained in this way.


When we refer to theestimatedcoefficients, we will use the notation\(\hat\beta_0, \dots, \hat\beta_k\). The equations for these will be given in Section7.9.


TheTSLM()function fits a linear regression model to time series data. It is similar to thelm()function which is widely used for linear models, butTSLM()provides additional facilities for handling time series.


### Example: US consumption expenditure


A multiple linear regression model for US consumption is\[
y_t=\beta_0 + \beta_1 x_{1,t}+ \beta_2 x_{2,t}+ \beta_3 x_{3,t}+ \beta_4 x_{4,t}+\varepsilon_t,
\]where\(y\)is the percentage change in real personal consumption expenditure,\(x_1\)is the percentage change in real personal disposable income,\(x_2\)is the percentage change in industrial production,\(x_3\)is the percentage change in personal savings and\(x_4\)is the change in the unemployment rate.


The following output provides information about the fitted model. The first column ofCoefficientsgives an estimate of each\(\beta\)coefficient and the second column gives its standard error (i.e., the standard deviation which would be obtained from repeatedly estimating the\(\beta\)coefficients on similar data sets). The standard error gives a measure of the uncertainty in the estimated\(\beta\)coefficient.


```
fit_consMR <- us_change |>
  model(tslm = TSLM(Consumption ~ Income + Production +
                                    Unemployment + Savings))
report(fit_consMR)
#> Series: Consumption 
#> Model: TSLM 
#> 
#> Residuals:
#>     Min      1Q  Median      3Q     Max 
#> -0.9055 -0.1582 -0.0361  0.1362  1.1547 
#> 
#> Coefficients:
#>              Estimate Std. Error t value Pr(>|t|)    
#> (Intercept)   0.25311    0.03447    7.34  5.7e-12 ***
#> Income        0.74058    0.04012   18.46  < 2e-16 ***
#> Production    0.04717    0.02314    2.04    0.043 *  
#> Unemployment -0.17469    0.09551   -1.83    0.069 .  
#> Savings      -0.05289    0.00292  -18.09  < 2e-16 ***
#> ---
#> Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
#> 
#> Residual standard error: 0.31 on 193 degrees of freedom
#> Multiple R-squared: 0.768,   Adjusted R-squared: 0.763
#> F-statistic:  160 on 4 and 193 DF, p-value: <2e-16
```


For forecasting purposes, the final two columns are of limited interest. The “t value” is the ratio of an estimated\(\beta\)coefficient to its standard error and the last column gives the p-value: the probability of the estimated\(\beta\)coefficient being as large as it is if there was no real relationship between consumption and the corresponding predictor. This is useful when studying the effect of each predictor, but is not particularly useful for forecasting.


### Fitted values


Predictions of\(y\)can be obtained by using the estimated coefficients in the regression equation and setting the error term to zero. In general we write,\[\begin{equation}
  \hat{y}_t = \hat\beta_{0} + \hat\beta_{1} x_{1,t} + \hat\beta_{2} x_{2,t} + \cdots + \hat\beta_{k} x_{k,t}.
  \tag{7.2}
\end{equation}\]Plugging in the values of\(x_{1,t},\dots,x_{k,t}\)for\(t=1,\dots,T\)returns predictions of\(y_t\)within the training set, referred to asfitted values. Note that these are predictions of the data used to estimate the model, not genuine forecasts of future values of\(y\).


The following plots show the actual values compared to the fitted values for the percentage change in the US consumption expenditure series. The time plot in Figure7.6shows that the fitted values follow the actual data fairly closely. This is verified by the strong positive relationship shown by the scatterplot in Figure7.7.


```
augment(fit_consMR) |>
  ggplot(aes(x = Quarter)) +
  geom_line(aes(y = Consumption, colour = "Data")) +
  geom_line(aes(y = .fitted, colour = "Fitted")) +
  labs(y = NULL,
    title = "Percent change in US consumption expenditure"
  ) +
  scale_colour_manual(values=c(Data="black",Fitted="#D55E00")) +
  guides(colour = guide_legend(title = NULL))
```


Figure 7.6: Time plot of actual US consumption expenditure and predicted US consumption expenditure.


```
augment(fit_consMR) |>
  ggplot(aes(x = Consumption, y = .fitted)) +
  geom_point() +
  labs(
    y = "Fitted (predicted values)",
    x = "Data (actual values)",
    title = "Percent change in US consumption expenditure"
  ) +
  geom_abline(intercept = 0, slope = 1)
```


Figure 7.7: Actual US consumption expenditure plotted against predicted US consumption expenditure.


### Goodness-of-fit


A common way to summarise how well a linear regression model fits the data is via the coefficient of determination, or\(R^2\). This can be calculated as the square of the correlation between the observed\(y\)values and the predicted\(\hat{y}\)values. Alternatively, it can also be calculated as,\[
  R^2 = \frac{\sum(\hat{y}_{t} - \bar{y})^2}{\sum(y_{t}-\bar{y})^2},
\]where the summations are over all observations. Thus, it reflects the proportion of variation in the forecast variable that is accounted for (or explained) by the regression model.


In simple linear regression, the value of\(R^2\)is also equal to the square of the correlation between\(y\)and\(x\)(provided an intercept has been included).


If the predictions are close to the actual values, we would expect\(R^2\)to be close to 1. On the other hand, if the predictions are unrelated to the actual values, then\(R^2=0\)(again, assuming there is an intercept). In all cases,\(R^2\)lies between 0 and 1.


The\(R^2\)value is used frequently, though often incorrectly, in forecasting. The value of\(R^2\)will never decrease when adding an extra predictor to the model and this can lead to over-fitting. There are no set rules for what is a good\(R^2\)value, and typical values of\(R^2\)depend on the type of data used. Validating a model’s forecasting performance on the test data is much better than measuring the\(R^2\)value on the training data.


### Example: US consumption expenditure


Figure7.7plots the actual consumption expenditure values versus the fitted values. The correlation between these variables is\(r=0.877\)hence\(R^2= 0.768\)(shown in the output above). In this case, the model does an excellent job as it explains 76.8% of the variation in the consumption data. Compare that to the\(R^2\)value of 0.15 obtained from the simple regression with the same data set in Section7.1. Adding the three extra predictors has allowed a lot more of the variation in the consumption data to be explained.


### Standard error of the regression


Another measure of how well the model has fitted the data is the standard deviation of the residuals, which is often known as the “residual standard error”. This is shown in the above output with the value 0.31.


It is calculated using\[\begin{equation}
  \hat{\sigma}_e=\sqrt{\frac{1}{T-k-1}\sum_{t=1}^{T}{e_t^2}},
  \tag{7.3}
\end{equation}\]where\(k\)is the number of predictors in the model. Notice that we divide by\(T-k-1\)because we have estimated\(k+1\)parameters (the intercept and a coefficient for each predictor variable) in computing the residuals.


The standard error is related to the size of the average error that the model produces. We can compare this error to the sample mean of\(y\)or with the standard deviation of\(y\)to gain some perspective on the accuracy of the model.


The standard error will be used when generating prediction intervals, discussed in Section7.6.
