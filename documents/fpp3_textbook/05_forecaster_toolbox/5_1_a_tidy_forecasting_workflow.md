
# Forecasting: Principles and Practice(3rd ed)


## 5.1A tidy forecasting workflow


The process of producing forecasts for time series data can be broken down into a few steps.


To illustrate the process, we will fit linear trend models to national GDP data stored inglobal_economy.


### Data preparation (tidy)


The first step in forecasting is to prepare data in the correct format. This process may involve loading in data, identifying missing values, filtering the time series, and other pre-processing tasks. The functionality provided bytsibbleand other packages in thetidyversesubstantially simplifies this step.


Many models have different data requirements; some require the series to be in time order, others require no missing values. Checking your data is an essential step to understanding its features and should always be done before models are estimated.


We will model GDP per capita over time; so first, we must compute the relevant variable.


```
gdppc <- global_economy |>
  mutate(GDP_per_capita = GDP / Population)
```


### Plot the data (visualise)


As we have seen in Chapter2, visualisation is an essential step in understanding the data. Looking at your data allows you to identify common patterns, and subsequently specify an appropriate model.


The data for one country in our example are plotted in Figure5.1.


```
gdppc |>
  filter(Country == "Sweden") |>
  autoplot(GDP_per_capita) +
  labs(y = "$US", title = "GDP per capita for Sweden")
```


Figure 5.1: GDP per capita data for Sweden from 1960 to 2017.


### Define a model (specify)


There are many different time series models that can be used for forecasting, and much of this book is dedicated to describing various models. Specifying an appropriate model for the data is essential for producing appropriate forecasts.


Models infableare specified using model functions, which each use a formula (y ~ x) interface. The response variable(s) are specified on the left of the formula, and the structure of the model is written on the right.


For example, a linear trend model (to be discussed in Chapter7) for GDP per capita can be specified with


```
TSLM(GDP_per_capita ~ trend()).
```


In this case the model function isTSLM()(time series linear model), the response variable isGDP_per_capitaand it is being modelled usingtrend()(a “special” function specifying a linear trend when it is used withinTSLM()). We will be taking a closer look at how each model can be specified in their respective sections.


The special functions used to define the model’s structure vary between models (as each model can support different structures). The “Specials” section of the documentation for each model function lists these special functions and how they can be used.


The left side of the formula also supports the transformations discussed in Section3.1, which can be useful in simplifying the time series patterns or constraining the forecasts to be between specific values (see Section13.3).


### Train the model (estimate)


Once an appropriate model is specified, we next train the model on some data. One or more model specifications can be estimated using themodel()function.


To estimate the model in our example, we use


```
fit <- gdppc |>
  model(trend_model = TSLM(GDP_per_capita ~ trend()))
```


This fits a linear trend model to the GDP per capita data for each combination of key variables in the tsibble. In this example, it will fit a model to each of the 263 countries in the dataset. The resulting object is a model table or a “mable”.


```
fit
#> # A mable: 263 x 2
#> # Key:     Country [263]
#>    Country             trend_model
#>    <fct>                   <model>
#>  1 Afghanistan              <TSLM>
#>  2 Albania                  <TSLM>
#>  3 Algeria                  <TSLM>
#>  4 American Samoa           <TSLM>
#>  5 Andorra                  <TSLM>
#>  6 Angola                   <TSLM>
#>  7 Antigua and Barbuda      <TSLM>
#>  8 Arab World               <TSLM>
#>  9 Argentina                <TSLM>
#> 10 Armenia                  <TSLM>
#> # ℹ 253 more rows
```


Each row corresponds to one combination of the key variables. Thetrend_modelcolumn contains information about the fitted model for each country. In later chapters we will learn how to see more information about each model.


### Check model performance (evaluate)


Once a model has been fitted, it is important to check how well it has performed on the data. There are several diagnostic tools available to check model behaviour, and also accuracy measures that allow one model to be compared against another. Sections5.8and5.9go into further details.


### Produce forecasts (forecast)


With an appropriate model specified, estimated and checked, it is time to produce the forecasts usingforecast(). The easiest way to use this function is by specifying the number of future observations to forecast. For example, forecasts for the next 10 observations can be generated usingh = 10. We can also use natural language; e.g.,h = "2 years"can be used to predict two years into the future.


In other situations, it may be more convenient to provide a dataset of future time periods to forecast. This is commonly required when your model uses additional information from the data, such as exogenous regressors. Additional data required by the model can be included in the dataset of observations to forecast.


```
fit |> forecast(h = "3 years")
#> # A fable: 789 x 5 [1Y]
#> # Key:     Country, .model [263]
#>    Country        .model       Year
#>    <fct>          <chr>       <dbl>
#>  1 Afghanistan    trend_model  2018
#>  2 Afghanistan    trend_model  2019
#>  3 Afghanistan    trend_model  2020
#>  4 Albania        trend_model  2018
#>  5 Albania        trend_model  2019
#>  6 Albania        trend_model  2020
#>  7 Algeria        trend_model  2018
#>  8 Algeria        trend_model  2019
#>  9 Algeria        trend_model  2020
#> 10 American Samoa trend_model  2018
#> # ℹ 779 more rows
#> # ℹ 2 more variables: GDP_per_capita <dist>, .mean <dbl>
```


This is a forecast table, or “fable”. Each row corresponds to one forecast period for each country. TheGDP_per_capitacolumn contains the forecast distribution, while the.meancolumn contains the point forecast. The point forecast is the mean (or average) of the forecast distribution.


The forecasts can be plotted along with the historical data usingautoplot()as follows.


```
fit |>
  forecast(h = "3 years") |>
  filter(Country == "Sweden") |>
  autoplot(gdppc) +
  labs(y = "$US", title = "GDP per capita for Sweden")
```


Figure 5.2: Forecasts of GDP per capita for Sweden using a simple trend model.
