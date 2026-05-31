
# Forecasting: Principles and Practice(3rd ed)


## 2.6Scatterplots


The graphs discussed so far are useful for visualising individual time series. It is also useful to explore relationshipsbetweentime series.


Figures2.12and2.13show two time series: half-hourly electricity demand (in Gigawatts) and temperature (in degrees Celsius), for 2014 in Victoria, Australia. The temperatures are for Melbourne, the largest city in Victoria, while the demand values are for the entire state.


```
vic_elec |>
  filter(year(Time) == 2014) |>
  autoplot(Demand) +
  labs(y = "GW",
       title = "Half-hourly electricity demand: Victoria")
```


Figure 2.12: Half hourly electricity demand in Victoria, Australia, for 2014.


```
vic_elec |>
  filter(year(Time) == 2014) |>
  autoplot(Temperature) +
  labs(
    y = "Degrees Celsius",
    title = "Half-hourly temperatures: Melbourne, Australia"
  )
```


Figure 2.13: Half hourly temperature in Melbourne, Australia, for 2014.


We can study the relationship between demand and temperature by plotting one series against the other.


```
vic_elec |>
  filter(year(Time) == 2014) |>
  ggplot(aes(x = Temperature, y = Demand)) +
  geom_point() +
  labs(title="Electricity demand versus Temperature",
       x = "Temperature (degrees Celsius)",
       y = "Electricity demand (GW)")
```


Figure 2.14: Half-hourly electricity demand plotted against temperature for 2014 in Victoria, Australia.


This scatterplot helps us to visualise the relationship between the variables. It is clear that high demand occurs when temperatures are high due to the effect of air-conditioning. But there is also a heating effect, where demand increases for very low temperatures.


### Correlation


It is common to computecorrelation coefficientsto measure the strength of the linear relationship between two variables. The correlation between variables\(x\)and\(y\)is given by\[
r = \frac{\sum (x_{t} - \bar{x})(y_{t}-\bar{y})}{\sqrt{\sum(x_{t}-\bar{x})^2}\sqrt{\sum(y_{t}-\bar{y})^2}}.
\]The value of\(r\)always lies between\(-1\)and\(1\)with negative values indicating a negative relationship and positive values indicating a positive relationship. The graphs in Figure2.15show examples of data sets with varying levels of correlation.


Figure 2.15: Examples of data sets with different levels of correlation.


The correlation coefficient only measures the strength of thelinearrelationship between two variables, and can sometimes be misleading. For example, the correlation for the electricity demand and temperature data shown in Figure2.14is 0.28, but thenon-linearrelationship is stronger than that.


Figure 2.16: Each of these plots has a correlation coefficient of 0.82. Data fromAnscombe (1973).


The plots in Figure2.16all have correlation coefficients of 0.82, but they have very different relationships. This shows how important it is to look at the plots of the data and not simply rely on correlation values.


### Scatterplot matrices


When there are several potential predictor variables, it is useful to plot each variable against each other variable. Consider the eight time series shown in Figure2.17, showing quarterly visitor numbers across states and territories of Australia.


```
visitors <- tourism |>
  group_by(State) |>
  summarise(Trips = sum(Trips))
visitors |>
  ggplot(aes(x = Quarter, y = Trips)) +
  geom_line() +
  facet_grid(vars(State), scales = "free_y") +
  labs(title = "Australian domestic tourism",
       y= "Overnight trips ('000)")
```


Figure 2.17: Quarterly visitor nights for the states and territories of Australia.


To see the relationships between these eight time series, we can plot each time series against the others. These plots can be arranged in a scatterplot matrix, as shown in Figure2.18. (This plot requires theGGallypackage to be installed.)


```
visitors |>
  pivot_wider(values_from=Trips, names_from=State) |>
  GGally::ggpairs(columns = 2:9)
```


Figure 2.18: A scatterplot matrix of the quarterly visitor nights in the states and territories of Australia.


For each panel, the variable on the vertical axis is given by the variable name in that row, and the variable on the horizontal axis is given by the variable name in that column. There are many options available to produce different plots within each panel. In the default version, the correlations are shown in the upper right half of the plot, while the scatterplots are shown in the lower half. On the diagonal are shown density plots.


The value of the scatterplot matrix is that it enables a quick view of the relationships between all pairs of variables. In this example, mostly positive relationships are revealed, with the strongest relationships being between the neighbouring states located in the south and south east coast of Australia, namely, New South Wales, Victoria and South Australia. Some negative relationships are also revealed between the Northern Territory and other regions. The Northern Territory is located in the north of Australia famous for its outback desert landscapes visited mostly in winter. Hence, the peak visitation in the Northern Territory is in the July (winter) quarter in contrast to January (summer) quarter for the rest of the regions.


### Bibliography
