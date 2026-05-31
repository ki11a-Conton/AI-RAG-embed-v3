
# Forecasting: Principles and Practice(3rd ed)


## 3.2Time series components


If we assume an additive decomposition, then we can write\[
  y_{t} = S_{t} + T_{t} + R_t,
\]where\(y_{t}\)is the data,\(S_{t}\)is the seasonal component,\(T_{t}\)is the trend-cycle component, and\(R_t\)is the remainder component, all at period\(t\). Alternatively, a multiplicative decomposition would be written as\[
  y_{t} = S_{t} \times T_{t} \times R_t.
\]


The additive decomposition is the most appropriate if the magnitude of the seasonal fluctuations, or the variation around the trend-cycle, does not vary with the level of the time series. When the variation in the seasonal pattern, or the variation around the trend-cycle, appears to be proportional to the level of the time series, then a multiplicative decomposition is more appropriate. Multiplicative decompositions are common with economic time series.


An alternative to using a multiplicative decomposition is to first transform the data until the variation in the series appears to be stable over time, then use an additive decomposition. When a log transformation has been used, this is equivalent to using a multiplicative decomposition on the original data because\[
  y_{t} = S_{t} \times T_{t} \times R_t \quad\text{is equivalent to}\quad
  \log y_{t} = \log S_{t} + \log T_{t} + \log R_t.
\]


### Example: Employment in the US retail sector


We will look at several methods for obtaining the components\(S_{t}\),\(T_{t}\)and\(R_{t}\)later in this chapter, but first it is helpful to see an example. We will decompose the number of persons employed in retail as shown in Figure3.5. The data shows the total monthly number of persons in thousands employed in the retail sector across the US since 1990.


```
us_retail_employment <- us_employment |>
  filter(year(Month) >= 1990, Title == "Retail Trade") |>
  select(-Series_ID)
autoplot(us_retail_employment, Employed) +
  labs(y = "Persons (thousands)",
       title = "Total employment in US retail")
```


Figure 3.5: Total number of persons employed in US retail.


To illustrate the ideas, we will use the STL decomposition method, which is discussed in Section3.6.


```
dcmp <- us_retail_employment |>
  model(stl = STL(Employed))
components(dcmp)
#> # A dable: 357 x 7 [1M]
#> # Key:     .model [1]
#> # :        Employed = trend + season_year + remainder
#>    .model    Month Employed  trend season_year remainder season_adjust
#>    <chr>     <mth>    <dbl>  <dbl>       <dbl>     <dbl>         <dbl>
#>  1 stl    1990 Jan   13256. 13288.      -33.0      0.836        13289.
#>  2 stl    1990 Feb   12966. 13269.     -258.     -44.6          13224.
#>  3 stl    1990 Mar   12938. 13250.     -290.     -22.1          13228.
#>  4 stl    1990 Apr   13012. 13231.     -220.       1.05         13232.
#>  5 stl    1990 May   13108. 13211.     -114.      11.3          13223.
#>  6 stl    1990 Jun   13183. 13192.      -24.3     15.5          13207.
#>  7 stl    1990 Jul   13170. 13172.      -23.2     21.6          13193.
#>  8 stl    1990 Aug   13160. 13151.       -9.52    17.8          13169.
#>  9 stl    1990 Sep   13113. 13131.      -39.5     22.0          13153.
#> 10 stl    1990 Oct   13185. 13110.       61.6     13.2          13124.
#> # ℹ 347 more rows
```


The output above shows the components of an STL decomposition. The original data is shown (asEmployed), followed by the estimated components. This output forms a “dable” or decomposition table. The header to the table shows that theEmployedseries has been decomposed additively.


Thetrendcolumn (containing the trend-cycle\(T_t\)) follows the overall movement of the series, ignoring any seasonality and random fluctuations, as shown in Figure3.6.


```
components(dcmp) |>
  as_tsibble() |>
  autoplot(Employed, colour="gray") +
  geom_line(aes(y=trend), colour = "#D55E00") +
  labs(
    y = "Persons (thousands)",
    title = "Total employment in US retail"
  )
```


Figure 3.6: Total number of persons employed in US retail: the trend-cycle component (orange) and the raw data (grey).


We can plot all of the components in a single figure usingautoplot(), as shown in Figure3.7.


```
components(dcmp) |> autoplot()
```


Figure 3.7: The total number of persons employed in US retail (top) and its three additive components.


The three components are shown separately in the bottom three panels. These components can be added together to reconstruct the data shown in the top panel. Notice that the seasonal component changes over time, so that any two consecutive years have similar patterns, but years far apart may have different seasonal patterns. The remainder component shown in the bottom panel is what is left over when the seasonal and trend-cycle components have been subtracted from the data.


The grey bars to the left of each panel show the relative scales of the components. Each grey bar represents the same length but because the plots are on different scales, the bars vary in size. The large grey bar in the bottom panel shows that the variation in the remainder component is smallest compared to the variation in the data. If we shrank the bottom three panels until their bars became the same size as that in the data panel, then all the panels would be on the same scale.


### Seasonally adjusted data


If the seasonal component is removed from the original data, the resulting values are the “seasonally adjusted” data. For an additive decomposition, the seasonally adjusted data are given by\(y_{t}-S_{t}\), and for multiplicative data, the seasonally adjusted values are obtained using\(y_{t}/S_{t}\).


Figure3.8shows the seasonally adjusted number of persons employed.


```
components(dcmp) |>
  as_tsibble() |>
  autoplot(Employed, colour = "gray") +
  geom_line(aes(y=season_adjust), colour = "#0072B2") +
  labs(y = "Persons (thousands)",
       title = "Total employment in US retail")
```


Figure 3.8: Seasonally adjusted retail employment data (blue) and the original data (grey).


If the variation due to seasonality is not of primary interest, the seasonally adjusted series can be useful. For example, monthly unemployment data are usually seasonally adjusted in order to highlight variation due to the underlying state of the economy rather than the seasonal variation. An increase in unemployment due to school leavers seeking work is seasonal variation, while an increase in unemployment due to an economic recession is non-seasonal. Most economic analysts who study unemployment data are more interested in the non-seasonal variation. Consequently, employment data (and many other economic series) are usually seasonally adjusted.


Seasonally adjusted series contain the remainder component as well as the trend-cycle. Therefore, they are not “smooth”, and “downturns” or “upturns” can be misleading. If the purpose is to look for turning points in a series, and interpret any changes in direction, then it is better to use the trend-cycle component rather than the seasonally adjusted data.
