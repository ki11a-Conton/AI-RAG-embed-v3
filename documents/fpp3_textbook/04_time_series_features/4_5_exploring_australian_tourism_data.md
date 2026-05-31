
# Forecasting: Principles and Practice(3rd ed)


## 4.5Exploring Australian tourism data


All of the features included in thefeastspackage can be computed in one line like this.


```
tourism_features <- tourism |>
  features(Trips, feature_set(pkgs = "feasts"))
tourism_features
#> # A tibble: 304 × 51
#>    Region         State          Purpose trend_strength seasonal_strength_year
#>    <chr>          <chr>          <chr>            <dbl>                  <dbl>
#>  1 Adelaide       South Austral… Busine…          0.464                  0.407
#>  2 Adelaide       South Austral… Holiday          0.554                  0.619
#>  3 Adelaide       South Austral… Other            0.746                  0.202
#>  4 Adelaide       South Austral… Visiti…          0.435                  0.452
#>  5 Adelaide Hills South Austral… Busine…          0.464                  0.179
#>  6 Adelaide Hills South Austral… Holiday          0.528                  0.296
#>  7 Adelaide Hills South Austral… Other            0.593                  0.404
#>  8 Adelaide Hills South Austral… Visiti…          0.488                  0.254
#>  9 Alice Springs  Northern Terr… Busine…          0.534                  0.251
#> 10 Alice Springs  Northern Terr… Holiday          0.381                  0.832
#> # ℹ 294 more rows
#> # ℹ 46 more variables: seasonal_peak_year <dbl>, seasonal_trough_year <dbl>,
#> #   spikiness <dbl>, linearity <dbl>, curvature <dbl>, stl_e_acf1 <dbl>,
#> #   stl_e_acf10 <dbl>, acf1 <dbl>, acf10 <dbl>, diff1_acf1 <dbl>,
#> #   diff1_acf10 <dbl>, diff2_acf1 <dbl>, diff2_acf10 <dbl>,
#> #   season_acf1 <dbl>, pacf5 <dbl>, diff1_pacf5 <dbl>, diff2_pacf5 <dbl>,
#> #   season_pacf <dbl>, zero_run_mean <dbl>, nonzero_squared_cv <dbl>, …
```


Provided theurcaandfracdiffpackages are installed, this gives 48 features for every combination of the three key variables (Region,StateandPurpose). We can treat this tibble like any data set and analyse it to find interesting observations or groups of observations.


We’ve already seen how we can plot one feature against another (Section4.3). We can also do pairwise plots of groups of features. In Figure4.3, for example, we show all features that involve seasonality, along with thePurposevariable.


```
library(glue)
tourism_features |>
  select_at(vars(contains("season"), Purpose)) |>
  mutate(
    seasonal_peak_year = seasonal_peak_year +
      4*(seasonal_peak_year==0),
    seasonal_trough_year = seasonal_trough_year +
      4*(seasonal_trough_year==0),
    seasonal_peak_year = glue("Q{seasonal_peak_year}"),
    seasonal_trough_year = glue("Q{seasonal_trough_year}"),
  ) |>
  GGally::ggpairs(mapping = aes(colour = Purpose))
```


Figure 4.3: Pairwise plots of all the seasonal features for the Australian tourism data


Here, thePurposevariable is mapped to colour. There is a lot of information in this figure, and we will highlight just a few things we can learn.

- The three numerical measures related to seasonality (seasonal_strength_year,season_acf1andseason_pacf) are all positively correlated.
- The bottom left panel and the top right panel both show that the most strongly seasonal series are related to holidays (as we saw previously).
- The bar plots in the bottom row of theseasonal_peak_yearandseasonal_trough_yearcolumns show that seasonal peaks in Business travel occur most often in Quarter 3, and least often in Quarter 1.

It is difficult to explore more than a handful of variables in this way. A useful way to handle many more variables is to use a dimension reduction technique such as principal components. This gives linear combinations of variables that explain the most variation in the original data. We can compute the principal components of the tourism features as follows.


```
library(broom)
pcs <- tourism_features |>
  select(-State, -Region, -Purpose) |>
  prcomp(scale = TRUE) |>
  augment(tourism_features)
pcs |>
  ggplot(aes(x = .fittedPC1, y = .fittedPC2, col = Purpose)) +
  geom_point() +
  theme(aspect.ratio = 1)
```


Figure 4.4: A plot of the first two principal components, calculated from the 48 features of the Australian quarterly tourism data.


Each point on Figure4.4represents one series and its location on the plot is based on all 48 features. The first principal component (.fittedPC1) is the linear combination of the features which explains the most variation in the data. The second principal component (.fittedPC2) is the linear combination which explains the next most variation in the data, while being uncorrelated with the first principal component. For more information about principal component dimension reduction, seeIzenman (2008).


Figure4.4reveals a few things about the tourism data. First, the holiday series behave quite differently from the rest of the series. Almost all of the holiday series appear in the top half of the plot, while almost all of the remaining series appear in the bottom half of the plot. Clearly, the second principal component is distinguishing between holidays and other types of travel.


The plot also allows us to identify anomalous time series — series which have unusual feature combinations. These appear as points that are separate from the majority of series in Figure4.4. There are four that stand out, and we can identify which series they correspond to as follows.


```
outliers <- pcs |>
  filter(.fittedPC1 > 10) |>
  select(Region, State, Purpose, .fittedPC1, .fittedPC2)
outliers
#> # A tibble: 4 × 5
#>   Region                 State             Purpose  .fittedPC1 .fittedPC2
#>   <chr>                  <chr>             <chr>         <dbl>      <dbl>
#> 1 Australia's North West Western Australia Business       13.4    -11.3  
#> 2 Australia's South West Western Australia Holiday        10.9      0.880
#> 3 Melbourne              Victoria          Holiday        12.3    -10.4  
#> 4 South Coast            New South Wales   Holiday        11.9      9.42
outliers |>
  left_join(tourism, by = c("State", "Region", "Purpose"), multiple = "all") |>
  mutate(Series = glue("{State}", "{Region}", "{Purpose}", .sep = "\n\n")) |>
  ggplot(aes(x = Quarter, y = Trips)) +
  geom_line() +
  facet_grid(Series ~ ., scales = "free") +
  labs(title = "Outlying time series in PC space")
```


Figure 4.5: Four anomalous time series from the Australian tourism data.


We can speculate why these series are identified as unusual.

- Holiday visits to the south coast of NSW is highly seasonal but has almost no trend, whereas most holiday destinations in Australia show some trend over time.
- Melbourne is an unusual holiday destination because it has almost no seasonality, whereas most holiday destinations in Australia have highly seasonal tourism.
- The north western corner of Western Australia is unusual because it shows an increase in business tourism in the last few years of data, but little or no seasonality.
- The south western corner of Western Australia is unusual because it shows both an increase in holiday tourism in the last few years of data and a high level of seasonality.

### Bibliography
