
# Forecasting: Principles and Practice(3rd ed)


## 7.1The linear model


### Simple linear regression


In the simplest case, the regression model allows for a linear relationship between the forecast variable\(y\)and a single predictor variable\(x\):\[
  y_t = \beta_0 + \beta_1 x_t + \varepsilon_t.
\]An artificial example of data from such a model is shown in Figure7.1. The coefficients\(\beta_0\)and\(\beta_1\)denote the intercept and the slope of the line respectively. The intercept\(\beta_0\)represents the predicted value of\(y\)when\(x=0\). The slope\(\beta_1\)represents the average predicted change in\(y\)resulting from a one unit increase in\(x\).


Figure 7.1: An example of data from a simple linear regression model.


Notice that the observations do not lie on the straight line but are scattered around it. We can think of each observation\(y_t\)as consisting of the systematic or explained part of the model,\(\beta_0+\beta_1x_t\), and the random “error”,\(\varepsilon_t\). The “error” term does not imply a mistake, but a deviation from the underlying straight line model. It captures anything that may affect\(y_t\)other than\(x_t\).


### Example: US consumption expenditure


Figure7.2shows time series of quarterly percentage changes (growth rates) of real personal consumption expenditure,\(y\), and real personal disposable income,\(x\), for the US from 1970 Q1 to 2019 Q2.


```
us_change |>
  pivot_longer(c(Consumption, Income), names_to="Series") |>
  autoplot(value) +
  labs(y = "% change")
```


Figure 7.2: Percentage changes in personal consumption expenditure and personal income for the US.


A scatter plot of consumption changes against income changes is shown in Figure7.3along with the estimated regression line


\[
  \hat{y}_t=0.54 + 0.27x_t.
\](We put a “hat” above\(y\)to indicate that this is the value of\(y\)predicted by the model.)


```
us_change |>
  ggplot(aes(x = Income, y = Consumption)) +
  labs(y = "Consumption (quarterly % change)",
       x = "Income (quarterly % change)") +
  geom_point() +
  geom_smooth(method = "lm", se = FALSE)
```


Figure 7.3: Scatterplot of quarterly changes in consumption expenditure versus quarterly changes in personal income and the fitted regression line.


The equation is estimated using theTSLM()function:


```
us_change |>
  model(TSLM(Consumption ~ Income)) |>
  report()
#> Series: Consumption 
#> Model: TSLM 
#> 
#> Residuals:
#>     Min      1Q  Median      3Q     Max 
#> -2.5824 -0.2778  0.0186  0.3233  1.4223 
#> 
#> Coefficients:
#>             Estimate Std. Error t value Pr(>|t|)    
#> (Intercept)   0.5445     0.0540   10.08  < 2e-16 ***
#> Income        0.2718     0.0467    5.82  2.4e-08 ***
#> ---
#> Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
#> 
#> Residual standard error: 0.591 on 196 degrees of freedom
#> Multiple R-squared: 0.147,   Adjusted R-squared: 0.143
#> F-statistic: 33.8 on 1 and 196 DF, p-value: 2.4e-08
```


We will discuss howTSLM()computes the coefficients in Section7.2.


The fitted line has a positive slope, reflecting the positive relationship between income and consumption. The slope coefficient shows that a one unit increase in\(x\)(a 1 percentage point increase in personal disposable income) results on average in 0.27 units increase in\(y\)(an average increase of 0.27 percentage points in personal consumption expenditure). Alternatively the estimated equation shows that a value of 1 for\(x\)(the percentage increase in personal disposable income) will result in a forecast value of\(0.54 + 0.27 \times 1 = 0.82\)for\(y\)(the percentage increase in personal consumption expenditure).


The interpretation of the intercept requires that a value of\(x=0\)makes sense. In this case when\(x=0\)(i.e., when there is no change in personal disposable income since the last quarter) the predicted value of\(y\)is 0.54 (i.e., an average increase in personal consumption expenditure of
0.54%). Even when\(x=0\)does not make sense, the intercept is an important part of the model. Without it, the slope coefficient can be distorted unnecessarily. The intercept should always be included unless the requirement is to force the regression line “through the origin”. In what follows we assume that an intercept is always included in the model.


### Multiple linear regression


When there are two or more predictor variables, the model is called amultiple regression model. The general form of a multiple regression model is\[\begin{equation}
  y_t = \beta_{0} + \beta_{1} x_{1,t} + \beta_{2} x_{2,t} + \cdots + \beta_{k} x_{k,t} + \varepsilon_t,
  \tag{7.1}
\end{equation}\]where\(y\)is the variable to be forecast and\(x_{1},\dots,x_{k}\)are the\(k\)predictor variables. Each of the predictor variables must be numerical. The coefficients\(\beta_{1},\dots,\beta_{k}\)measure the effect of each predictor after taking into account the effects of all the other predictors in the model. Thus, the coefficients measure themarginal effectsof the predictor variables.


### Example: US consumption expenditure


Figure7.4shows additional predictors that may be useful for forecasting US consumption expenditure. These are quarterly percentage changes in industrial production and personal savings, and quarterly changes in the unemployment rate (as this is already a percentage). Building a multiple linear regression model can potentially generate more accurate forecasts as we expect consumption expenditure to not only depend on personal income but on other predictors as well.


```
us_change |>
  select(-Consumption, -Income) |>
  pivot_longer(-Quarter) |>
  ggplot(aes(Quarter, value, colour = name)) +
  geom_line() +
  facet_grid(name ~ ., scales = "free_y") +
  guides(colour = "none") +
  labs(y="% change")
```


Figure 7.4: Quarterly percentage changes in industrial production and personal savings and quarterly changes in the unemployment rate for the US over the period 1970Q1-2019Q2.


Figure7.5is a scatterplot matrix of five variables. The first column shows the relationships between the forecast variable (consumption) and each of the predictors. The scatterplots show positive relationships with income and industrial production, and negative relationships with savings and unemployment. The strength of these relationships are shown by the correlation coefficients across the first row. The remaining scatterplots and correlation coefficients show the relationships between the predictors.


```
us_change |>
  GGally::ggpairs(columns = 2:6)
```


Figure 7.5: A scatterplot matrix of US consumption expenditure and the four predictors.


### Assumptions


When we use a linear regression model, we are implicitly making some assumptions about the variables in Equation(7.1).


First, we assume that the model is a reasonable approximation to reality; that is, the relationship between the forecast variable and the predictor variables satisfies this linear equation.


Second, we make the following assumptions about the errors\((\varepsilon_{1},\dots,\varepsilon_{T})\):

- they have mean zero; otherwise the forecasts will be systematically biased.
- they are not autocorrelated; otherwise the forecasts will be inefficient, as there is more information in the data that can be exploited.
- they are unrelated to the predictor variables; otherwise there would be more information that should be included in the systematic part of the model.

It is also useful to have the errors being normally distributed with a constant variance\(\sigma^2\)in order to easily produce prediction intervals.


Another important assumption in the linear regression model is that each predictor\(x\)is not a random variable. If we were performing a controlled experiment in a laboratory, we could control the values of each\(x\)(so they would not be random) and observe the resulting values of\(y\). With observational data (including most data in business and economics), it is not possible to control the value of\(x\), we simply observe it. Hence we make this an assumption.
