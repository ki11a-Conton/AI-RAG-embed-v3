
# Forecasting: Principles and Practice(3rd ed)


## 3.7Exercises

- Consider the GDP information inglobal_economy. Plot the GDP per capita for each country over time. Which country has the highest GDP per capita? How has this changed over time?

Consider the GDP information inglobal_economy. Plot the GDP per capita for each country over time. Which country has the highest GDP per capita? How has this changed over time?

- For each of the following series, make a graph of the data. If transforming seems appropriate, do so and describe the effect.United States GDP fromglobal_economy.Slaughter of Victorian “Bulls, bullocks and steers” inaus_livestock.Victorian Electricity Demand fromvic_elec.Gas production fromaus_production.

For each of the following series, make a graph of the data. If transforming seems appropriate, do so and describe the effect.

- United States GDP fromglobal_economy.
- Slaughter of Victorian “Bulls, bullocks and steers” inaus_livestock.
- Victorian Electricity Demand fromvic_elec.
- Gas production fromaus_production.
- Why is a Box-Cox transformation unhelpful for thecanadian_gasdata?

Why is a Box-Cox transformation unhelpful for thecanadian_gasdata?

- What Box-Cox transformation would you select for your retail data (from Exercise 7 in Section2.10)?

What Box-Cox transformation would you select for your retail data (from Exercise 7 in Section2.10)?

- For the following series, find an appropriate Box-Cox transformation in order to stabilise the variance. Tobacco fromaus_production, Economy class passengers between Melbourne and Sydney fromansett, and Pedestrian counts at Southern Cross Station frompedestrian.

For the following series, find an appropriate Box-Cox transformation in order to stabilise the variance. Tobacco fromaus_production, Economy class passengers between Melbourne and Sydney fromansett, and Pedestrian counts at Southern Cross Station frompedestrian.

- Show that a\(3\times5\)MA is equivalent to a 7-term weighted moving average with weights of 0.067, 0.133, 0.200, 0.200, 0.200, 0.133, and 0.067.

Show that a\(3\times5\)MA is equivalent to a 7-term weighted moving average with weights of 0.067, 0.133, 0.200, 0.200, 0.200, 0.133, and 0.067.

- Consider the last five years of the Gas data fromaus_production.gas<-tail(aus_production,5*4)|>select(Gas)Plot the time series. Can you identify seasonal fluctuations and/or a trend-cycle?Useclassical_decompositionwithtype=multiplicativeto calculate the trend-cycle and seasonal indices.Do the results support the graphical interpretation from part a?Compute and plot the seasonally adjusted data.Change one observation to be an outlier (e.g., add 300 to one observation), and recompute the seasonally adjusted data. What is the effect of the outlier?Does it make any difference if the outlier is near the end rather than in the middle of the time series?

Consider the last five years of the Gas data fromaus_production.


```
gas <- tail(aus_production, 5*4) |> select(Gas)
```

- Plot the time series. Can you identify seasonal fluctuations and/or a trend-cycle?
- Useclassical_decompositionwithtype=multiplicativeto calculate the trend-cycle and seasonal indices.
- Do the results support the graphical interpretation from part a?
- Compute and plot the seasonally adjusted data.
- Change one observation to be an outlier (e.g., add 300 to one observation), and recompute the seasonally adjusted data. What is the effect of the outlier?
- Does it make any difference if the outlier is near the end rather than in the middle of the time series?
- Recall your retail time series data (from Exercise 7 in Section2.10).
Decompose the series using X-11. Does it reveal any outliers, or unusual features that you had not noticed previously?

Recall your retail time series data (from Exercise 7 in Section2.10).
Decompose the series using X-11. Does it reveal any outliers, or unusual features that you had not noticed previously?

- Figures3.19and3.20show the result of decomposing the number of persons in the civilian labour force in Australia each month from February 1978 to August 1995.Figure 3.19: Decomposition of the number of persons in the civilian labour force in Australia each month from February 1978 to August 1995.Figure 3.20: Seasonal component from the decomposition shown in the previous figure.Write about 3–5 sentences describing the results of the decomposition. Pay particular attention to the scales of the graphs in making your interpretation.Is the recession of 1991/1992 visible in the estimated components?

Figures3.19and3.20show the result of decomposing the number of persons in the civilian labour force in Australia each month from February 1978 to August 1995.


Figure 3.19: Decomposition of the number of persons in the civilian labour force in Australia each month from February 1978 to August 1995.


Figure 3.20: Seasonal component from the decomposition shown in the previous figure.

- Write about 3–5 sentences describing the results of the decomposition. Pay particular attention to the scales of the graphs in making your interpretation.
- Is the recession of 1991/1992 visible in the estimated components?
- This exercise uses thecanadian_gasdata (monthly Canadian gas production in billions of cubic metres, January 1960 – February 2005).Plot the data usingautoplot(),gg_subseries()andgg_season()to look at the effect of the changing seasonality over time.3Do an STL decomposition of the data. You will need to choose a seasonal window to allow for the changing shape of the seasonal component.How does the seasonal shape change over time? [Hint: Try plotting the seasonal component usinggg_season().]Can you produce a plausible seasonally adjusted series?Compare the results with those obtained using SEATS and X-11. How are they different?

This exercise uses thecanadian_gasdata (monthly Canadian gas production in billions of cubic metres, January 1960 – February 2005).

- Plot the data usingautoplot(),gg_subseries()andgg_season()to look at the effect of the changing seasonality over time.3
- Do an STL decomposition of the data. You will need to choose a seasonal window to allow for the changing shape of the seasonal component.
- How does the seasonal shape change over time? [Hint: Try plotting the seasonal component usinggg_season().]
- Can you produce a plausible seasonally adjusted series?
- Compare the results with those obtained using SEATS and X-11. How are they different?
- The evolving seasonal pattern is possibly due to changes in the regulation of gas prices — thanks to Lewis Kirvan for pointing this out.↩︎

The evolving seasonal pattern is possibly due to changes in the regulation of gas prices — thanks to Lewis Kirvan for pointing this out.↩︎
