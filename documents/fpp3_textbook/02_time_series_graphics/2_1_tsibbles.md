
# Forecasting: Principles and Practice(3rd ed)


## 2.1tsibbleobjects


A time series can be thought of as a list of numbers (the observations), along with some information about what times those numbers were recorded (the index). This information can be stored as atsibbleobject in R.


### The index variable


Suppose you have annual observations for the last few years:


We turn this into atsibbleobject using thetsibble()function:


```
y <- tsibble(
  Year = 2015:2019,
  Observation = c(123, 39, 78, 52, 110),
  index = Year
)
```


tsibbleobjects extend tidy data frames (tibbleobjects) by introducing temporal structure. We have set the time seriesindexto be theYearcolumn, which associates the measurements (Observation) with the time of recording (Year).


For observations that are more frequent than once per year, we need to use a time class function on the index. For example, suppose we have a monthly datasetz:


```
z
#> # A tibble: 5 × 2
#>   Month    Observation
#>   <chr>          <dbl>
#> 1 2019 Jan          50
#> 2 2019 Feb          23
#> 3 2019 Mar          34
#> 4 2019 Apr          30
#> 5 2019 May          25
```


This can be converted to atsibbleobject using the following code:


```
z |>
  mutate(Month = yearmonth(Month)) |>
  as_tsibble(index = Month)
#> # A tsibble: 5 x 2 [1M]
#>      Month Observation
#>      <mth>       <dbl>
#> 1 2019 Jan          50
#> 2 2019 Feb          23
#> 3 2019 Mar          34
#> 4 2019 Apr          30
#> 5 2019 May          25
```


First, theMonthcolumn is being converted from text to a monthly time object withyearmonth(). We then convert the data frame to atsibbleby identifying theindexvariable usingas_tsibble(). Note the addition of “[1M]” on the first line indicating this is monthly data.


Other time class functions can be used depending on the frequency of the observations.


### The key variables


Atsibblealso allows multiple time series to be stored in a single object. Suppose you are interested in a dataset containing the fastest running times for women’s and men’s track races at the Olympics, from 100m to 10000m:


```
olympic_running
#> # A tsibble: 312 x 4 [4Y]
#> # Key:       Length, Sex [14]
#>     Year Length Sex    Time
#>    <int>  <int> <chr> <dbl>
#>  1  1896    100 men    12  
#>  2  1900    100 men    11  
#>  3  1904    100 men    11  
#>  4  1908    100 men    10.8
#>  5  1912    100 men    10.8
#>  6  1916    100 men    NA  
#>  7  1920    100 men    10.8
#>  8  1924    100 men    10.6
#>  9  1928    100 men    10.8
#> 10  1932    100 men    10.3
#> # ℹ 302 more rows
```


The summary above shows that this is atsibbleobject, which contains 312 rows and 4 columns. Alongside this, “[4Y]” informs us that the interval of these observations is every four years. Below this is the key structure, which informs us that there are 14 separate time series in thetsibble. A preview of the first 10 observations is also shown, in which we can see a missing value occurs in 1916. This is because the Olympics were not held during World War I.


The 14 time series in this object are uniquely identified by the keys: theLengthandSexvariables. Thedistinct()function can be used to show the categories of each variable or even combinations of variables:


```
olympic_running |> distinct(Sex)
#> # A tibble: 2 × 1
#>   Sex  
#>   <chr>
#> 1 men  
#> 2 women
```


### Working withtsibbleobjects


We can usedplyrfunctions such asmutate(),filter(),select()andsummarise()to work withtsibbleobjects. To illustrate these, we will use thePBStsibble containing sales data on pharmaceutical products in Australia.


```
PBS
#> # A tsibble: 67,596 x 9 [1M]
#> # Key:       Concession, Type, ATC1, ATC2 [336]
#>       Month Concession   Type    ATC1  ATC1_desc ATC2  ATC2_desc Scripts  Cost
#>       <mth> <chr>        <chr>   <chr> <chr>     <chr> <chr>       <dbl> <dbl>
#>  1 1991 Jul Concessional Co-pay… A     Alimenta… A01   STOMATOL…   18228 67877
#>  2 1991 Aug Concessional Co-pay… A     Alimenta… A01   STOMATOL…   15327 57011
#>  3 1991 Sep Concessional Co-pay… A     Alimenta… A01   STOMATOL…   14775 55020
#>  4 1991 Oct Concessional Co-pay… A     Alimenta… A01   STOMATOL…   15380 57222
#>  5 1991 Nov Concessional Co-pay… A     Alimenta… A01   STOMATOL…   14371 52120
#>  6 1991 Dec Concessional Co-pay… A     Alimenta… A01   STOMATOL…   15028 54299
#>  7 1992 Jan Concessional Co-pay… A     Alimenta… A01   STOMATOL…   11040 39753
#>  8 1992 Feb Concessional Co-pay… A     Alimenta… A01   STOMATOL…   15165 54405
#>  9 1992 Mar Concessional Co-pay… A     Alimenta… A01   STOMATOL…   16898 61108
#> 10 1992 Apr Concessional Co-pay… A     Alimenta… A01   STOMATOL…   18141 65356
#> # ℹ 67,586 more rows
```


This contains monthly data on Medicare Australia prescription data from July 1991 to June 2008. These are classified according to various concession types, and Anatomical Therapeutic Chemical (ATC) indexes. For this example, we are interested in theCosttime series (total cost of scripts in Australian dollars).


We can use thefilter()function to extract the A10 scripts:


```
PBS |>
  filter(ATC2 == "A10")
#> # A tsibble: 816 x 9 [1M]
#> # Key:       Concession, Type, ATC1, ATC2 [4]
#>       Month Concession   Type   ATC1  ATC1_desc ATC2  ATC2_desc Scripts   Cost
#>       <mth> <chr>        <chr>  <chr> <chr>     <chr> <chr>       <dbl>  <dbl>
#>  1 1991 Jul Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   89733 2.09e6
#>  2 1991 Aug Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   77101 1.80e6
#>  3 1991 Sep Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   76255 1.78e6
#>  4 1991 Oct Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   78681 1.85e6
#>  5 1991 Nov Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   70554 1.69e6
#>  6 1991 Dec Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   75814 1.84e6
#>  7 1992 Jan Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   64186 1.56e6
#>  8 1992 Feb Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   75899 1.73e6
#>  9 1992 Mar Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   89445 2.05e6
#> 10 1992 Apr Concessional Co-pa… A     Alimenta… A10   ANTIDIAB…   97315 2.23e6
#> # ℹ 806 more rows
```


This allows rows of the tsibble to be selected. Next we can simplify the resulting object by selecting the columns we will need in subsequent analysis.


```
PBS |>
  filter(ATC2 == "A10") |>
  select(Month, Concession, Type, Cost)
#> # A tsibble: 816 x 4 [1M]
#> # Key:       Concession, Type [4]
#>       Month Concession   Type           Cost
#>       <mth> <chr>        <chr>         <dbl>
#>  1 1991 Jul Concessional Co-payments 2092878
#>  2 1991 Aug Concessional Co-payments 1795733
#>  3 1991 Sep Concessional Co-payments 1777231
#>  4 1991 Oct Concessional Co-payments 1848507
#>  5 1991 Nov Concessional Co-payments 1686458
#>  6 1991 Dec Concessional Co-payments 1843079
#>  7 1992 Jan Concessional Co-payments 1564702
#>  8 1992 Feb Concessional Co-payments 1732508
#>  9 1992 Mar Concessional Co-payments 2046102
#> 10 1992 Apr Concessional Co-payments 2225977
#> # ℹ 806 more rows
```


Theselect()function allows us to select particular columns, whilefilter()allows us to keep particular rows.


Note that the index variableMonth, and the keysConcessionandType, would be returned even if they were not explicitly selected as they are required for a tsibble (to ensure each row contains a unique combination of keys and index).


Another useful function issummarise()which allows us to combine data across keys. For example, we may wish to compute total cost per month regardless of theConcessionorTypekeys.


```
PBS |>
  filter(ATC2 == "A10") |>
  select(Month, Concession, Type, Cost) |>
  summarise(TotalC = sum(Cost))
#> # A tsibble: 204 x 2 [1M]
#>       Month  TotalC
#>       <mth>   <dbl>
#>  1 1991 Jul 3526591
#>  2 1991 Aug 3180891
#>  3 1991 Sep 3252221
#>  4 1991 Oct 3611003
#>  5 1991 Nov 3565869
#>  6 1991 Dec 4306371
#>  7 1992 Jan 5088335
#>  8 1992 Feb 2814520
#>  9 1992 Mar 2985811
#> 10 1992 Apr 3204780
#> # ℹ 194 more rows
```


The new variableTotalCis the sum of allCostvalues for each month.


We can create new variables using themutate()function. Here we change the units from dollars to millions of dollars:


```
PBS |>
  filter(ATC2 == "A10") |>
  select(Month, Concession, Type, Cost) |>
  summarise(TotalC = sum(Cost)) |>
  mutate(Cost = TotalC/1e6)
#> # A tsibble: 204 x 3 [1M]
#>       Month  TotalC  Cost
#>       <mth>   <dbl> <dbl>
#>  1 1991 Jul 3526591  3.53
#>  2 1991 Aug 3180891  3.18
#>  3 1991 Sep 3252221  3.25
#>  4 1991 Oct 3611003  3.61
#>  5 1991 Nov 3565869  3.57
#>  6 1991 Dec 4306371  4.31
#>  7 1992 Jan 5088335  5.09
#>  8 1992 Feb 2814520  2.81
#>  9 1992 Mar 2985811  2.99
#> 10 1992 Apr 3204780  3.20
#> # ℹ 194 more rows
```


Finally, we will save the resulting tsibble for examples later in this chapter.


```
PBS |>
  filter(ATC2 == "A10") |>
  select(Month, Concession, Type, Cost) |>
  summarise(TotalC = sum(Cost)) |>
  mutate(Cost = TotalC / 1e6) -> a10
```


At the end of this series of piped functions, we have used a right assignment (->), which is not common in R code, but is convenient at the end of a long series of commands as it continues the flow of the code.


### Read a csv file and convert to a tsibble


Almost all of the data used in this book is already stored astsibbleobjects. But most data lives in databases, MS-Excel files or csv files, before it is imported into R. So often the first step in creating a tsibble is to read in the data, and then identify the index and key variables.


For example, suppose we have the following quarterly data stored in a csv file (only the first 10 rows are shown). This data set provides information on the size of the prison population in Australia, disaggregated by state, gender, legal status and indigenous status. (Here, ATSI stands for Aboriginal or Torres Strait Islander.)


We can read it into R, and create a tsibble object, by simply identifying which column contains the time index, and which columns are keys. The remaining columns are values — there can be many value columns, although in this case there is only one (Count). The original csv file stored the dates as individual days, although the data is actually quarterly, so we need to convert theDatevariable to quarters.


```
prison <- readr::read_csv("https://OTexts.com/fpp3/extrafiles/prison_population.csv")
```


```
prison <- prison |>
  mutate(Quarter = yearquarter(Date)) |>
  select(-Date) |>
  as_tsibble(key = c(State, Gender, Legal, Indigenous),
             index = Quarter)

prison
#> # A tsibble: 3,072 x 6 [1Q]
#> # Key:       State, Gender, Legal, Indigenous [64]
#>    State Gender Legal    Indigenous Count Quarter
#>    <chr> <chr>  <chr>    <chr>      <dbl>   <qtr>
#>  1 ACT   Female Remanded ATSI           0 2005 Q1
#>  2 ACT   Female Remanded ATSI           1 2005 Q2
#>  3 ACT   Female Remanded ATSI           0 2005 Q3
#>  4 ACT   Female Remanded ATSI           0 2005 Q4
#>  5 ACT   Female Remanded ATSI           1 2006 Q1
#>  6 ACT   Female Remanded ATSI           1 2006 Q2
#>  7 ACT   Female Remanded ATSI           1 2006 Q3
#>  8 ACT   Female Remanded ATSI           0 2006 Q4
#>  9 ACT   Female Remanded ATSI           0 2007 Q1
#> 10 ACT   Female Remanded ATSI           1 2007 Q2
#> # ℹ 3,062 more rows
```


This tsibble contains 64 separate time series corresponding to the combinations of the 8 states, 2 genders, 2 legal statuses and 2 indigenous statuses. Each of these series is 48 observations in length, from 2005 Q1 to 2016 Q4.


For a tsibble to be valid, it requires a unique index for each combination of keys. Thetsibble()oras_tsibble()function will return an error if this is not true.


### The seasonal period


Some graphics and some models will use the seasonal period of the data. The seasonal period is the number of observations before the seasonal pattern repeats. In most cases, this will be automatically detected using the time index variable.


Some common periods for different time intervals are shown in the table below:


For quarterly, monthly and weekly data, there is only one seasonal period — the number of observations within each year. Actually, there are not\(52\)weeks in a year, but\(365.25/7 = 52.18\)on average, allowing for a leap year every fourth year. Approximating seasonal periods to integers can be useful as many seasonal terms in models only support integer seasonal periods.


If the data is observed more than once per week, then there is often more than one seasonal pattern in the data. For example, data with daily observations might have weekly (period\(=7\)) or annual (period\(=365.25\)) seasonal patterns. Similarly, data that are observed every minute might have hourly (period\(=60\)), daily (period\(=24\times60=1440\)), weekly (period\(=24\times60\times7=10080\)) and annual seasonality (period\(=24\times60\times365.25=525960\)).


More complicated (and unusual) seasonal patterns can be specified using theperiod()function in thelubridatepackage.
