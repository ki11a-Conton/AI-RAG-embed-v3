
# Forecasting: Principles and Practice(3rd ed)


## 2.10Exercises

- Explore the following four time series:Bricksfromaus_production,Lynxfrompelt,Closefromgafa_stock,Demandfromvic_elec.Use?(orhelp()) to find out about the data in each series.What is the time interval of each series?Useautoplot()to produce a time plot of each series.For the last plot, modify the axis labels and title.

Explore the following four time series:Bricksfromaus_production,Lynxfrompelt,Closefromgafa_stock,Demandfromvic_elec.

- Use?(orhelp()) to find out about the data in each series.
- What is the time interval of each series?
- Useautoplot()to produce a time plot of each series.
- For the last plot, modify the axis labels and title.
- Usefilter()to find what days corresponded to the peak closing price for each of the four stocks ingafa_stock.

Usefilter()to find what days corresponded to the peak closing price for each of the four stocks ingafa_stock.

- Download the filetute1.csvfromthe book website, open it in Excel (or some other spreadsheet application), and review its contents. You should find four columns of information. Columns B through D each contain a quarterly series, labelled Sales, AdBudget and GDP. Sales contains the quarterly sales for a small company over the period 1981-2005. AdBudget is the advertising budget and GDP is the gross domestic product. All series have been adjusted for inflation.You can read the data into R with the following script:tute1<-readr::read_csv("tute1.csv")View(tute1)Convert the data to time seriesmytimeseries<-tute1|>mutate(Quarter =yearquarter(Quarter))|>as_tsibble(index =Quarter)Construct time series plots of each of the three seriesmytimeseries|>pivot_longer(-Quarter)|>ggplot(aes(x =Quarter,y =value,colour =name))+geom_line()+facet_grid(name~.,scales ="free_y")Check what happens when you don’t includefacet_grid().

Download the filetute1.csvfromthe book website, open it in Excel (or some other spreadsheet application), and review its contents. You should find four columns of information. Columns B through D each contain a quarterly series, labelled Sales, AdBudget and GDP. Sales contains the quarterly sales for a small company over the period 1981-2005. AdBudget is the advertising budget and GDP is the gross domestic product. All series have been adjusted for inflation.

- You can read the data into R with the following script:tute1<-readr::read_csv("tute1.csv")View(tute1)

You can read the data into R with the following script:


```
tute1 <- readr::read_csv("tute1.csv")
View(tute1)
```

- Convert the data to time seriesmytimeseries<-tute1|>mutate(Quarter =yearquarter(Quarter))|>as_tsibble(index =Quarter)

Convert the data to time series


```
mytimeseries <- tute1 |>
  mutate(Quarter = yearquarter(Quarter)) |>
  as_tsibble(index = Quarter)
```

- Construct time series plots of each of the three seriesmytimeseries|>pivot_longer(-Quarter)|>ggplot(aes(x =Quarter,y =value,colour =name))+geom_line()+facet_grid(name~.,scales ="free_y")Check what happens when you don’t includefacet_grid().

Construct time series plots of each of the three series


```
mytimeseries |>
  pivot_longer(-Quarter) |>
  ggplot(aes(x = Quarter, y = value, colour = name)) +
  geom_line() +
  facet_grid(name ~ ., scales = "free_y")
```


Check what happens when you don’t includefacet_grid().

- TheUSgaspackage contains data on the demand for natural gas in the US.Install theUSgaspackage.Create a tsibble fromus_totalwith year as the index and state as the key.Plot the annual natural gas consumption by state for the New England area (comprising the states of Maine, Vermont, New Hampshire, Massachusetts, Connecticut and Rhode Island).

TheUSgaspackage contains data on the demand for natural gas in the US.

- Install theUSgaspackage.
- Create a tsibble fromus_totalwith year as the index and state as the key.
- Plot the annual natural gas consumption by state for the New England area (comprising the states of Maine, Vermont, New Hampshire, Massachusetts, Connecticut and Rhode Island).
- Downloadtourism.xlsxfromthe book websiteand read it into R usingreadxl::read_excel().Create a tsibble which is identical to thetourismtsibble from thetsibblepackage.Find what combination ofRegionandPurposehad the maximum number of overnight trips on average.Create a new tsibble which combines the Purposes and Regions, and just has total trips by State.
- Downloadtourism.xlsxfromthe book websiteand read it into R usingreadxl::read_excel().
- Create a tsibble which is identical to thetourismtsibble from thetsibblepackage.
- Find what combination ofRegionandPurposehad the maximum number of overnight trips on average.
- Create a new tsibble which combines the Purposes and Regions, and just has total trips by State.
- Theaus_arrivalsdata set comprises quarterly international arrivals to Australia from Japan, New Zealand, UK and the US.Useautoplot(),gg_season()andgg_subseries()to compare the differences between the arrivals from these four countries.Can you identify any unusual observations?

Theaus_arrivalsdata set comprises quarterly international arrivals to Australia from Japan, New Zealand, UK and the US.

- Useautoplot(),gg_season()andgg_subseries()to compare the differences between the arrivals from these four countries.
- Can you identify any unusual observations?
- Monthly Australian retail data is provided inaus_retail. Select one of the time series as follows (but choose your own seed value):set.seed(12345678)myseries<-aus_retail|>filter(`Series ID`==sample(aus_retail$`Series ID`,1))Explore your chosen retail time series using the following functions:autoplot(),gg_season(),gg_subseries(),gg_lag(),ACF() |> autoplot()Can you spot any seasonality, cyclicity and trend? What do you learn about the series?

Monthly Australian retail data is provided inaus_retail. Select one of the time series as follows (but choose your own seed value):


```
set.seed(12345678)
myseries <- aus_retail |>
  filter(`Series ID` == sample(aus_retail$`Series ID`,1))
```


Explore your chosen retail time series using the following functions:


autoplot(),gg_season(),gg_subseries(),gg_lag(),


ACF() |> autoplot()


Can you spot any seasonality, cyclicity and trend? What do you learn about the series?

- Use the following graphics functions:autoplot(),gg_season(),gg_subseries(),gg_lag(),ACF()and explore features from the following time series: “Total Private”Employedfromus_employment,Bricksfromaus_production,Harefrompelt, “H02”CostfromPBS, andBarrelsfromus_gasoline.Can you spot any seasonality, cyclicity and trend?What do you learn about the series?What can you say about the seasonal patterns?Can you identify any unusual years?

Use the following graphics functions:autoplot(),gg_season(),gg_subseries(),gg_lag(),ACF()and explore features from the following time series: “Total Private”Employedfromus_employment,Bricksfromaus_production,Harefrompelt, “H02”CostfromPBS, andBarrelsfromus_gasoline.

- Can you spot any seasonality, cyclicity and trend?
- What do you learn about the series?
- What can you say about the seasonal patterns?
- Can you identify any unusual years?
- The following time plots and ACF plots correspond to four different time series. Your task is to match each time plot in the first row with one of the ACF plots in the second row.

The following time plots and ACF plots correspond to four different time series. Your task is to match each time plot in the first row with one of the ACF plots in the second row.

- Theaus_livestockdata contains the monthly total number of pigs slaughtered in Victoria, Australia, from Jul 1972 to Dec 2018. Usefilter()to extract pig slaughters in Victoria between 1990 and 1995. Useautoplot()andACF()for this data. How do they differ from white noise? If a longer period of data is used, what difference does it make to the ACF?

Theaus_livestockdata contains the monthly total number of pigs slaughtered in Victoria, Australia, from Jul 1972 to Dec 2018. Usefilter()to extract pig slaughters in Victoria between 1990 and 1995. Useautoplot()andACF()for this data. How do they differ from white noise? If a longer period of data is used, what difference does it make to the ACF?

- Use the following code to compute the daily changes in Google closing stock prices.dgoog<-gafa_stock|>filter(Symbol=="GOOG",year(Date)>=2018)|>mutate(trading_day =row_number())|>update_tsibble(index =trading_day,regular =TRUE)|>mutate(diff =difference(Close))Why was it necessary to re-index the tsibble?Plot these differences and their ACF.Do the changes in the stock prices look like white noise?
- Use the following code to compute the daily changes in Google closing stock prices.dgoog<-gafa_stock|>filter(Symbol=="GOOG",year(Date)>=2018)|>mutate(trading_day =row_number())|>update_tsibble(index =trading_day,regular =TRUE)|>mutate(diff =difference(Close))

Use the following code to compute the daily changes in Google closing stock prices.


```
dgoog <- gafa_stock |>
  filter(Symbol == "GOOG", year(Date) >= 2018) |>
  mutate(trading_day = row_number()) |>
  update_tsibble(index = trading_day, regular = TRUE) |>
  mutate(diff = difference(Close))
```

- Why was it necessary to re-index the tsibble?

Why was it necessary to re-index the tsibble?

- Plot these differences and their ACF.

Plot these differences and their ACF.

- Do the changes in the stock prices look like white noise?

Do the changes in the stock prices look like white noise?
