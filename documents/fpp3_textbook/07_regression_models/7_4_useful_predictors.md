
# Forecasting: Principles and Practice(3rd ed)


## 7.4Some useful predictors


There are several useful predictors that occur frequently when using regression for time series data.


### Trend


It is common for time series data to be trending. A linear trend can be modelled by simply using\(x_{1,t}=t\)as a predictor,\[
  y_{t}= \beta_0+\beta_1t+\varepsilon_t,
\]where\(t=1,\dots,T\). A trend variable can be specified in theTSLM()function using thetrend()special. In Section7.7we discuss how we can also model nonlinear trends.


### Dummy variables


So far, we have assumed that each predictor takes numerical values. But what about when a predictor is a categorical variable taking only two values (e.g., “yes” and “no”)? Such a variable might arise, for example, when forecasting daily sales and you want to take account of whether the day is apublic holidayor not. So the predictor takes value “yes” on a public holiday, and “no” otherwise.


This situation can still be handled within the framework of multiple regression models by creating a “dummy variable” which takes value 1 corresponding to “yes” and 0 corresponding to “no”. A dummy variable is also known as an “indicator variable”.


A dummy variable can also be used to account for anoutlierin the data. Rather than omit the outlier, a dummy variable removes its effect. In this case, the dummy variable takes value 1 for that observation and 0 everywhere else. An example is the case where a special event has occurred. For example when forecasting tourist arrivals to Brazil, we will need to account for the effect of the Rio de Janeiro summer Olympics in 2016.


If there are more than two categories, then the variable can be coded using several dummy variables (one fewer than the total number of categories).TSLM()will automatically handle this case if you specify a factor variable as a predictor. There is usually no need to manually create the corresponding dummy variables.


### Seasonal dummy variables


Suppose that we are forecasting daily data and we want to account for the day of the week as a predictor. Then the following dummy variables can be created.


Notice that only six dummy variables are needed to code seven categories. That is because the seventh category (in this case Sunday) is captured by the intercept, and is specified when the dummy variables are all set to zero.


Many beginners will try to add a seventh dummy variable for the seventh category. This is known as the “dummy variable trap”, because it will cause the regression to fail. There will be one too many parameters to estimate when an intercept is also included. The general rule is to use one fewer dummy variables than categories. So for quarterly data, use three dummy variables; for monthly data, use 11 dummy variables; and for daily data, use six dummy variables, and so on.


The interpretation of each of the coefficients associated with the dummy variables is that it isa measure of the effect of that category relative to the omitted category. In the above example, the coefficient of\(d_{1,t}\)associated with Monday will measure the effect of Monday on the forecast variable compared to the effect of Sunday. An example of interpreting estimated dummy variable coefficients capturing the quarterly seasonality of Australian beer production follows.


TheTSLM()function will automatically handle this situation if you specify the specialseason().


### Example: Australian quarterly beer production


Recall the Australian quarterly beer production data shown again in Figure7.14.


```
recent_production <- aus_production |>
  filter(year(Quarter) >= 1992)
recent_production |>
  autoplot(Beer) +
  labs(y = "Megalitres",
       title = "Australian quarterly beer production")
```


Figure 7.14: Australian quarterly beer production.


We want to forecast the value of future beer production. We can model this data using a regression model with a linear trend and quarterly dummy variables,\[
  y_{t} = \beta_{0} + \beta_{1} t + \beta_{2}d_{2,t} + \beta_3 d_{3,t} + \beta_4 d_{4,t} + \varepsilon_{t},
\]where\(d_{i,t} = 1\)if\(t\)is in quarter\(i\)and 0 otherwise. The first quarter variable has been omitted, so the coefficients associated with the other quarters are measures of the difference between those quarters and the first quarter.


```
fit_beer <- recent_production |>
  model(TSLM(Beer ~ trend() + season()))
report(fit_beer)
#> Series: Beer 
#> Model: TSLM 
#> 
#> Residuals:
#>    Min     1Q Median     3Q    Max 
#> -42.90  -7.60  -0.46   7.99  21.79 
#> 
#> Coefficients:
#>               Estimate Std. Error t value Pr(>|t|)    
#> (Intercept)   441.8004     3.7335  118.33  < 2e-16 ***
#> trend()        -0.3403     0.0666   -5.11  2.7e-06 ***
#> season()year2 -34.6597     3.9683   -8.73  9.1e-13 ***
#> season()year3 -17.8216     4.0225   -4.43  3.4e-05 ***
#> season()year4  72.7964     4.0230   18.09  < 2e-16 ***
#> ---
#> Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
#> 
#> Residual standard error: 12.2 on 69 degrees of freedom
#> Multiple R-squared: 0.924,   Adjusted R-squared: 0.92
#> F-statistic:  211 on 4 and 69 DF, p-value: <2e-16
```


Note thattrend()andseason()are not standard functions; they are “special” functions that work within theTSLM()model formulae.


There is an average downward trend of -0.34 megalitres per quarter. On average, the second quarter has production of 34.7 megalitres lower than the first quarter, the third quarter has production of 17.8 megalitres lower than the first quarter, and the fourth quarter has production of 72.8 megalitres higher than the first quarter.


```
augment(fit_beer) |>
  ggplot(aes(x = Quarter)) +
  geom_line(aes(y = Beer, colour = "Data")) +
  geom_line(aes(y = .fitted, colour = "Fitted")) +
  scale_colour_manual(
    values = c(Data = "black", Fitted = "#D55E00")
  ) +
  labs(y = "Megalitres",
       title = "Australian quarterly beer production") +
  guides(colour = guide_legend(title = "Series"))
```


Figure 7.15: Time plot of beer production and predicted beer production.


```
augment(fit_beer) |>
  ggplot(aes(x = Beer, y = .fitted,
             colour = factor(quarter(Quarter)))) +
  geom_point() +
  labs(y = "Fitted", x = "Actual values",
       title = "Australian quarterly beer production") +
  geom_abline(intercept = 0, slope = 1) +
  guides(colour = guide_legend(title = "Quarter"))
```


Figure 7.16: Actual beer production plotted against predicted beer production.


### Intervention variables


It is often necessary to model interventions that may have affected the variable to be forecast. For example, competitor activity, advertising expenditure, industrial action, and so on, can all have an effect.


When the effect lasts only for one period, we use a “spike” variable. This is a dummy variable that takes value one in the period of the intervention and zero elsewhere. A spike variable is equivalent to a dummy variable for handling an outlier.


Other interventions have an immediate and permanent effect. If an intervention causes a level shift (i.e., the value of the series changes suddenly and permanently from the time of intervention), then we use a “step” variable. A step variable takes value zero before the intervention and one from the time of intervention onward.


Another form of permanent effect is a change of slope. Here the intervention is handled using a piecewise linear trend; a trend that bends at the time of intervention and hence is nonlinear. We will discuss this in Section7.7.


### Trading days


The number of trading days in a month can vary considerably and can have a substantial effect on sales data. To allow for this, the number of trading days in each month can be included as a predictor.


An alternative that allows for the effects of different days of the week has the following predictors:\[\begin{align*}
  x_{1} &= \text{number of Mondays in month;} \\
  x_{2} &= \text{number of Tuesdays in month;} \\
        & \vdots \\
  x_{7} &= \text{number of Sundays in month.}
\end{align*}\]


### Distributed lags


It is often useful to include advertising expenditure as a predictor. However, since the effect of advertising can last beyond the actual campaign, we need to include lagged values of advertising expenditure. Thus, the following predictors may be used.\[\begin{align*}
  x_{1} &= \text{advertising for previous month;} \\
  x_{2} &= \text{advertising for two months previously;} \\
        & \vdots \\
  x_{m} &= \text{advertising for $m$ months previously.}
\end{align*}\]


It is common to require the coefficients to decrease as the lag increases, although this is beyond the scope of this book.


### Easter


Easter differs from most holidays because it is not held on the same date each year, and its effect can last for several days. In this case, a dummy variable can be used with value one where the holiday falls in the particular time period and zero otherwise.


With monthly data, if Easter falls in March then the dummy variable takes value 1 in March, and if it falls in April the dummy variable takes value 1 in April. When Easter starts in March and finishes in April, the dummy variable is split proportionally between months.


### Fourier series


An alternative to using seasonal dummy variables, especially for long seasonal periods, is to use Fourier terms. Jean-Baptiste Fourier was a French mathematician, born in the 1700s, who showed that a series of sine and cosine terms of the right frequencies can approximate any periodic function. We can use them for seasonal patterns.


If\(m\)is the seasonal period, then the first few Fourier terms are given by\[
  x_{1,t} = \sin\left(\textstyle\frac{2\pi t}{m}\right),
  x_{2,t} = \cos\left(\textstyle\frac{2\pi t}{m}\right),
  x_{3,t} = \sin\left(\textstyle\frac{4\pi t}{m}\right),
\]\[
  x_{4,t} = \cos\left(\textstyle\frac{4\pi t}{m}\right),
  x_{5,t} = \sin\left(\textstyle\frac{6\pi t}{m}\right),
  x_{6,t} = \cos\left(\textstyle\frac{6\pi t}{m}\right),
\]and so on. If we have monthly seasonality, and we use the first 11 of these predictor variables, then we will get exactly the same forecasts as using 11 dummy variables.


With Fourier terms, we often need fewer predictors than with dummy variables, especially when\(m\)is large. This makes them useful for weekly data, for example, where\(m\approx 52\). For short seasonal periods (e.g., quarterly data), there is little advantage in using Fourier terms over seasonal dummy variables.


These Fourier terms are produced using thefourier()function. For example, the Australian beer data can be modelled like this.


```
fourier_beer <- recent_production |>
  model(TSLM(Beer ~ trend() + fourier(K = 2)))
report(fourier_beer)
#> Series: Beer 
#> Model: TSLM 
#> 
#> Residuals:
#>    Min     1Q Median     3Q    Max 
#> -42.90  -7.60  -0.46   7.99  21.79 
#> 
#> Coefficients:
#>                    Estimate Std. Error t value Pr(>|t|)    
#> (Intercept)        446.8792     2.8732  155.53  < 2e-16 ***
#> trend()             -0.3403     0.0666   -5.11  2.7e-06 ***
#> fourier(K = 2)C1_4   8.9108     2.0112    4.43  3.4e-05 ***
#> fourier(K = 2)S1_4 -53.7281     2.0112  -26.71  < 2e-16 ***
#> fourier(K = 2)C2_4 -13.9896     1.4226   -9.83  9.3e-15 ***
#> ---
#> Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
#> 
#> Residual standard error: 12.2 on 69 degrees of freedom
#> Multiple R-squared: 0.924,   Adjusted R-squared: 0.92
#> F-statistic:  211 on 4 and 69 DF, p-value: <2e-16
```


TheKargument tofourier()specifies how many pairs of sin and cos terms to include. The maximum allowed is\(K=m/2\)where\(m\)is the seasonal period. Because we have used the maximum here, the results are identical to those obtained when using seasonal dummy variables.


If only the first two Fourier terms are used (\(x_{1,t}\)and\(x_{2,t}\)), the seasonal pattern will follow a simple sine wave. A regression model containing Fourier terms is often called aharmonic regressionbecause the successive Fourier terms represent harmonics of the first two Fourier terms.
