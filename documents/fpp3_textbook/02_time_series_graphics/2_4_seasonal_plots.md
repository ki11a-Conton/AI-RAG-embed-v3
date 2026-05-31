
# Forecasting: Principles and Practice(3rd ed)


## 2.4Seasonal plots


A seasonal plot is similar to a time plot except that the data are plotted against the individual “seasons” in which the data were observed. An example is given in Figure2.4showing the antidiabetic drug sales.


```
a10 |>
  gg_season(Cost, labels = "both") +
  labs(y = "$ (millions)",
       title = "Seasonal plot: Antidiabetic drug sales")
```


Figure 2.4: Seasonal plot of monthly antidiabetic drug sales in Australia.


This is the same data as was shown earlier, but now the data from each year overlap. A seasonal plot allows the underlying seasonal pattern to be seen more clearly, and is especially useful in identifying years in which the pattern changes.


There is a large jump in sales in January each year. These are probably sales in late December as customers stockpile before the end of the calendar year, but the sales are not registered with the government until a week or two later. The graph also shows that there was an unusually small number of sales in March 2008 (most other years show an increase between February and March). The small number of sales in June 2008 is probably due to incomplete counting of sales at the time the data were collected.


### Multiple seasonal periods


Where the data has more than one seasonal pattern, theperiodargument can be used to select which seasonal plot is required. Thevic_elecdata contains half-hourly electricity demand for the state of Victoria, Australia. We can plot the daily pattern, weekly pattern or yearly pattern by specifying theperiodargument as shown in Figures2.5–2.7.


In the first plot, the three days with 25 hours are when daylight saving ended in each year and so these days contained an extra hour. There were also three days with only 23 hours each (when daylight saving started) but these are hidden beneath all the other lines on the plot.


```
vic_elec |> gg_season(Demand, period = "day") +
  theme(legend.position = "none") +
  labs(y="MWh", title="Electricity demand: Victoria")
```


Figure 2.5: Seasonal plot showing daily seasonal patterns for Victorian electricity demand.


```
vic_elec |> gg_season(Demand, period = "week") +
  theme(legend.position = "none") +
  labs(y="MWh", title="Electricity demand: Victoria")
```


Figure 2.6: Seasonal plot showing weekly seasonal patterns for Victorian electricity demand.


```
vic_elec |> gg_season(Demand, period = "year") +
  labs(y="MWh", title="Electricity demand: Victoria")
```


Figure 2.7: Seasonal plot showing yearly seasonal patterns for Victorian electricity demand.
