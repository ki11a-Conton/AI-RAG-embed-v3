
# Forecasting: Principles and Practice(3rd ed)


## 13.7Very long and very short time series


### Forecasting very short time series


We often get asked howfewdata points can be used to fit a time series model. As with almost all sample size questions, there is no easy answer. It depends on thenumber of model parameters to be estimated and the amount of randomness in the data. The sample size required increases with the number of parameters to be estimated, and the amount of noise in the data.


Some textbooks provide rules-of-thumb giving minimum sample sizes for various time series models. These are misleading and unsubstantiated in theory or practice. Further, they ignore the underlying variability of the data and often overlook the number of parameters to be estimated as well. There is, for example, no justification for the magic number of 30 often given as a minimum for ARIMA modelling. The only theoretical limit is that we need more observations than there are parameters in our forecasting model. However, in practice, we usually need substantially more observations than that.


Ideally, we would test if our chosen model performs well out-of-sample compared to some simpler approaches. However, with short series, there is not enough data to allow some observations to be withheld for testing purposes, and even time series cross validation can be difficult to apply. The AICc is particularly useful here, because it is a proxy for the one-step forecast out-of-sample MSE. Choosing the model with the minimum AICc value allows both the number of parameters and the amount of noise to be taken into account.


What tends to happen with short series is that the AICc suggests simple models because anything with more than one or two parameters will produce poor forecasts due to the estimation error. We will fit an ARIMA model to the annual series from the M3-competition with fewer than 20 observations. First we need to create a tsibble, containing the relevant series.


```
m3totsibble <- function(z) {
  bind_rows(
    as_tsibble(z$x) |> mutate(Type = "Training"),
    as_tsibble(z$xx) |> mutate(Type = "Test")
  ) |>
    mutate(
      st = z$st,
      type = z$type,
      period = z$period,
      description = z$description,
      sn = z$sn
    ) |>
    as_tibble()
}
short <- Mcomp::M3 |>
  subset("yearly") |>
  purrr::map_dfr(m3totsibble) |>
  group_by(sn) |>
  mutate(n = max(row_number())) |>
  filter(n <= 20) |>
  ungroup() |>
  as_tsibble(index = index, key = c(sn, period, st))
```


Now we can apply an ARIMA model to each series.


```
short_fit <- short |>
  model(arima = ARIMA(value))
```


Of the 152 series,
21 had models with zero parameters (white noise and random walks),
86 had models with one parameter,
31 had models with two parameters,
13 had models with three parameters, and only
1 series had a model with four parameters.


### Forecasting very long time series


Most time series models do not work well for very long time series. The problem is that real data do not come from the models we use. When the number of observations is not large (say up to about 200) the models often work well as an approximation to whatever process generated the data. But eventually we will have enough data that the difference between the true process and the model starts to become more obvious. An additional problem is that the optimisation of the parameters becomes more time consuming because of the number of observations involved.


What to do about these issues depends on the purpose of the model. A more flexible and complicated model could be used, but this still assumes that the model structure will work over the whole period of the data. A better approach is usually to allow the model itself to change over time. ETS models are designed to handle this situation by allowing the trend and seasonal terms to evolve over time. ARIMA models with differencing have a similar property. But dynamic regression models do not allow any evolution of model components.


If we are only interested in forecasting the next few observations, one simple approach is to throw away the earliest observations and only fit a model to the most recent observations. Then an inflexible model can work well because there is not enough time for the relationships to change substantially.


For example, we fitted a dynamic harmonic regression model to 26 years of weekly gasoline production in Section13.1. It is, perhaps, unrealistic to assume that the seasonal pattern remains the same over nearly three decades. So we could simply fit a model to the most recent years instead.
