
# Forecasting: Principles and Practice(3rd ed)


## 3.5Methods used by official statistics agencies


Official statistics agencies (such as the US Census Bureau and the Australian Bureau of Statistics) are responsible for a large number of official economic and social time series. These agencies have developed their own decomposition procedures which are used for seasonal adjustment. Most of them use variants of the X-11 method, or the SEATS method, or a combination of the two. These methods are designed specifically to work with quarterly and monthly data, which are the most common series handled by official statistics agencies. They will not handle seasonality of other kinds, such as daily data, or hourly data, or weekly data. We will use the latest implementation of this group of methods known as “X-13ARIMA-SEATS”. For the methods discussed in this section, you will need to have installed theseasonalpackage in R.


### X-11 method


The X-11 method originated in the US Census Bureau and was further developed by Statistics Canada. It is based on classical decomposition, but includes many extra steps and features in order to overcome the drawbacks of classical decomposition that were discussed in the previous section. In particular, trend-cycle estimates are available for all observations including the end points, and the seasonal component is allowed to vary slowly over time. X-11 also handles trading day variation, holiday effects and the effects of known predictors. There are methods for both additive and multiplicative decomposition. The process is entirely automatic and tends to be highly robust to outliers and level shifts in the time series. The details of the X-11 method are described inDagum & Bianconcini (2016).


```
x11_dcmp <- us_retail_employment |>
  model(x11 = X_13ARIMA_SEATS(Employed ~ x11())) |>
  components()
autoplot(x11_dcmp) +
  labs(title =
    "Decomposition of total US retail employment using X-11.")
```


Figure 3.14: A multiplicative decomposition of US retail employment using X-11.


Compare this decomposition with the STL decomposition shown in Figure3.7and the classical decomposition shown in Figure3.13. The default approach forX_13ARIMA_SEATSshown here is a multiplicative decomposition, whereas the STL and classical decompositions shown earlier were additive; but it doesn’t make much difference in this case. The X-11 trend-cycle has captured the sudden fall in the data due to the 2007–2008 global financial crisis better than either of the other two methods (where the effect of the crisis has leaked into the remainder component). Also, the unusual observation in 1996 is now more clearly seen in the X-11 remainder component.


Figure3.15shows the trend-cycle component and the seasonally adjusted data, along with the original data. The seasonally adjusted data is very similar to the trend-cycle component in this example, so it is hard to distinguish them on the plot.


```
x11_dcmp |>
  ggplot(aes(x = Month)) +
  geom_line(aes(y = Employed, colour = "Data")) +
  geom_line(aes(y = season_adjust,
                colour = "Seasonally Adjusted")) +
  geom_line(aes(y = trend, colour = "Trend")) +
  labs(y = "Persons (thousands)",
       title = "Total employment in US retail") +
  scale_colour_manual(
    values = c("gray", "#0072B2", "#D55E00"),
    breaks = c("Data", "Seasonally Adjusted", "Trend")
  )
```


Figure 3.15: US retail employment: the original data (grey), the trend-cycle component (orange) and the seasonally adjusted data (barely visible in blue).


It can be useful to use seasonal plots and seasonal sub-series plots of the seasonal component, to help us visualise the variation in the seasonal component over time. Figure3.16shows a seasonal sub-series plot of the seasonal component from Figure3.14. In this case, there are only small changes over time.


```
x11_dcmp |>
  gg_subseries(seasonal)
```


Figure 3.16: Seasonal sub-series plot of the seasonal component from the X-11 method applied to total US retail employment.


### SEATS method


“SEATS” stands for “Seasonal Extraction in ARIMA Time Series” (ARIMA models are discussed in Chapter9). This procedure was developed at the Bank of Spain, and is now widely used by government agencies around the world. The details are beyond the scope of this book. However, a complete discussion of the method is available inDagum & Bianconcini (2016).


```
seats_dcmp <- us_retail_employment |>
  model(seats = X_13ARIMA_SEATS(Employed ~ seats())) |>
  components()
autoplot(seats_dcmp) +
  labs(title =
    "Decomposition of total US retail employment using SEATS")
```


Figure 3.17: A decomposition of US retail employment obtained using SEATS.


Figure3.17shows the SEATS method applied to the total retail employment series across the US. The result is quite similar to that obtained using the X-11 method shown in Figure3.14.


TheX_13ARIMA_SEATS()function calls theseasonalpackage which has many options for handling variations of X-11 and SEATS. Seethe package websitefor a detailed introduction to the options and features available.


### Bibliography
