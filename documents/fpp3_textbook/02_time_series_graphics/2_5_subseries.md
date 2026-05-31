
# Forecasting: Principles and Practice(3rd ed)


## 2.5Seasonal subseries plots


An alternative plot that emphasises the seasonal patterns is where the data for each season are collected together in separate mini time plots.


```
a10 |>
  gg_subseries(Cost) +
  labs(
    y = "$ (millions)",
    title = "Australian antidiabetic drug sales"
  )
```


Figure 2.8: Seasonal subseries plot of monthly antidiabetic drug sales in Australia.


The blue horizontal lines indicate the means for each month. This form of plot enables the underlying seasonal pattern to be seen clearly, and also shows the changes in seasonality over time. It is especially useful in identifying changes within particular seasons. In this example, the plot is not particularly revealing; but in some cases, this is the most useful way of viewing seasonal changes over time.


### Example: Australian holiday tourism


Australian quarterly vacation data provides an interesting example of how these plots can reveal information. First we need to extract the relevant data from thetourismtsibble. All the usualtidyversewrangling verbs apply. To get the total visitor nights spent on Holiday by State for each quarter (i.e., ignoring Regions) we can use the following code. Note that we do not have to explicitly group by the time index as this is required in atsibble.


```
holidays <- tourism |>
  filter(Purpose == "Holiday") |>
  group_by(State) |>
  summarise(Trips = sum(Trips))
```


```
holidays
#> # A tsibble: 640 x 3 [1Q]
#> # Key:       State [8]
#>    State Quarter Trips
#>    <chr>   <qtr> <dbl>
#>  1 ACT   1998 Q1  196.
#>  2 ACT   1998 Q2  127.
#>  3 ACT   1998 Q3  111.
#>  4 ACT   1998 Q4  170.
#>  5 ACT   1999 Q1  108.
#>  6 ACT   1999 Q2  125.
#>  7 ACT   1999 Q3  178.
#>  8 ACT   1999 Q4  218.
#>  9 ACT   2000 Q1  158.
#> 10 ACT   2000 Q2  155.
#> # ℹ 630 more rows
```


Time plots of each series show that there is strong seasonality for most states, but that the seasonal peaks do not coincide.


```
autoplot(holidays, Trips) +
  labs(y = "Overnight trips ('000)",
       title = "Australian domestic holidays")
```


Figure 2.9: Time plots of Australian domestic holidays by state.


To see the timing of the seasonal peaks in each state, we can use a season plot. Figure2.10makes it clear that the southern states of Australia (Tasmania, Victoria and South Australia) have strongest tourism in Q1 (their summer), while the northern states (Queensland and the Northern Territory) have the strongest tourism in Q3 (their dry season).


```
gg_season(holidays, Trips) +
  labs(y = "Overnight trips ('000)",
       title = "Australian domestic holidays")
```


Figure 2.10: Season plots of Australian domestic holidays by state.


The corresponding subseries plots are shown in Figure2.11.


```
holidays |>
  gg_subseries(Trips) +
  labs(y = "Overnight trips ('000)",
       title = "Australian domestic holidays")
```


Figure 2.11: Subseries plots of Australian domestic holidays by state.


This figure makes it evident that Western Australian tourism has jumped markedly in recent years, while Victorian tourism has increased in Q1 and Q4 but not in the middle of the year.
