
# Forecasting: Principles and Practice(3rd ed)


## 12.5Bootstrapping and bagging


### Bootstrapping time series


In the preceding section, and in Section5.5, we bootstrap the residuals of a time series in order to simulate future values of a series using a model.


More generally, we can generate new time series that are similar to our observed series, using another type of bootstrap.


First, the time series is transformed if necessary, and then decomposed into trend, seasonal and remainder components using STL. Then we obtain shuffled versions of the remainder component to get bootstrapped remainder series. Because there may be autocorrelation present in an STL remainder series, we cannot simply use the re-draw procedure that was described in Section5.5. Instead, we use a “blocked bootstrap”, where contiguous sections of the time series are selected at random and joined together. These bootstrapped remainder series are added to the trend and seasonal components, and the transformation is reversed to give variations on the original time series.


Consider the quarterly cement production in Australia from 1988 Q1 to 2010 Q2. First we check, see Figure12.19that the decomposition has adequately captured the trend and seasonality, and that there is no obvious remaining signal in the remainder series.


```
cement <- aus_production |>
  filter(year(Quarter) >= 1988) |>
  select(Quarter, Cement)
cement_stl <- cement |>
  model(stl = STL(Cement))
cement_stl |>
  components() |>
  autoplot()
```


Figure 12.19: STL decomposition of quarterly Australian cement production.


Now we can generate several bootstrapped versions of the data. Usually,generate()produces simulations of the future from a model. But here we want simulations for the period of the historical data. So we use thenew_dataargument to pass in the original data so that the same time periods are used for the simulated data. We will use a block size of 8 to cover two years of data.


```
cement_stl |>
  generate(new_data = cement, times = 10,
           bootstrap_block_size = 8) |>
  autoplot(.sim) +
  autolayer(cement, Cement) +
  guides(colour = "none") +
  labs(title = "Cement production: Bootstrapped series",
       y="Tonnes ('000)")
```


Figure 12.20: Ten bootstrapped versions of quarterly Australian cement production (coloured), along with the original data (black).


### Bagged forecasts


One use for these bootstrapped time series is to improve forecast accuracy. If we produce forecasts from each of the additional time series, and average the resulting forecasts, we get better forecasts than if we simply forecast the original time series directly. This is called “bagging” which stands for “bootstrapaggregating”.


We demonstrate the idea using thecementdata. First, we simulate many time series that are similar to the original data, using the block-bootstrap described above.


```
sim <- cement_stl |>
  generate(new_data = cement, times = 100,
           bootstrap_block_size = 8) |>
  select(-.model, -Cement)
```


For each of these series, we fit an ETS model. A different ETS model may be selected in each case, although it will most likely select the same model because the series are similar. However, the estimated parameters will be different, so the forecasts will be different even if the selected model is the same. This is a time-consuming process as there are a large number of series.


```
ets_forecasts <- sim |>
  model(ets = ETS(.sim)) |>
  forecast(h = 12)
ets_forecasts |>
  update_tsibble(key = .rep) |>
  autoplot(.mean) +
  autolayer(cement, Cement) +
  guides(colour = "none") +
  labs(title = "Cement production: bootstrapped forecasts",
       y="Tonnes ('000)")
```


Figure 12.21: Forecasts of 100 bootstrapped series obtained using ETS models.


Finally, we average these forecasts for each time period to obtain the “bagged forecasts” for the original data.


```
bagged <- ets_forecasts |>
  summarise(bagged_mean = mean(.mean))
cement |>
  model(ets = ETS(Cement)) |>
  forecast(h = 12) |>
  autoplot(cement) +
  autolayer(bagged, bagged_mean, col = "#D55E00") +
  labs(title = "Cement production in Australia",
       y="Tonnes ('000)")
```


Figure 12.22: Comparing bagged ETS forecasts (the average of 100 bootstrapped forecasts in orange) and ETS applied directly to the data (in blue).


Bergmeir et al. (2016)show that, on average, bagging gives better forecasts than just applyingETS()directly. Of course, it is slower because a lot more computation is required.


### Bibliography
