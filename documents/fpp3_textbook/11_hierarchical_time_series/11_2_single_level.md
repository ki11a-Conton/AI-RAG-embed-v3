
# Forecasting: Principles and Practice(3rd ed)


## 11.2Single level approaches


Traditionally, forecasts of hierarchical or grouped time series involved selecting one level of aggregation and generating forecasts for that level. These are then either aggregated for higher levels, or disaggregated for lower levels, to obtain a set of coherent forecasts for the rest of the structure.


### The bottom-up approach


A simple method for generating coherent forecasts is the “bottom-up” approach. This approach involves first generating forecasts for each series at the bottom level, and then summing these to produce forecasts for all the series in the structure.


For example, for the hierarchy of Figure11.1, we first generate\(h\)-step-ahead forecasts for each of the bottom-level series:\[
  \yhat{AA}{h},~~\yhat{AB}{h},~~\yhat{AC}{h},~~ \yhat{BA}{h}~~\text{and}~~\yhat{BB}{h}.
\](We have simplified the previously used notation of\(\hat{y}_{T+h|T}\)for brevity.)


Summing these, we get\(h\)-step-ahead coherent forecasts for the rest of the series:\[\begin{align*}
  \tilde{y}_{h} & =\yhat{AA}{h}+\yhat{AB}{h}+\yhat{AC}{h}+\yhat{BA}{h}+\yhat{BB}{h}, \\
  \ytilde{A}{h} & = \yhat{AA}{h}+\yhat{AB}{h}+\yhat{AC}{h}, \\
\text{and}\quad
  \ytilde{B}{h} &= \yhat{BA}{h}+\yhat{BB}{h}.
\end{align*}\](In this chapter, we will use the “tilde” notation to indicate coherent forecasts.)


An advantage of this approach is that we are forecasting at the bottom level of a structure, and therefore no information is lost due to aggregation. On the other hand, bottom-level data can be quite noisy and more challenging to model and forecast.


#### Example: Generating bottom-up forecasts


Suppose we want national and state forecasts for the Australian tourism data, but we aren’t interested in disaggregations using regions or the purpose of travel. So we first create a simpletsibbleobject containing only state and national trip totals for each quarter.


```
tourism_states <- tourism |>
  aggregate_key(State, Trips = sum(Trips))
```


We could generate the bottom-level state forecasts first, and then sum them to obtain the national forecasts.


```
fcasts_state <- tourism_states |>
  filter(!is_aggregated(State)) |>
  model(ets = ETS(Trips)) |>
  forecast()

# Sum bottom-level forecasts to get top-level forecasts
fcasts_national <- fcasts_state |>
  summarise(value = sum(Trips), .mean = mean(value))
```


However, we want a more general approach that will work with all the forecasting methods discussed in this chapter. So we will use thereconcile()function to specify how we want to compute coherent forecasts.


```
tourism_states |>
  model(ets = ETS(Trips)) |>
  reconcile(bu = bottom_up(ets)) |>
  forecast()
#> # A fable: 144 x 5 [1Q]
#> # Key:     State, .model [18]
#>    State  .model Quarter
#>    <chr*> <chr>    <qtr>
#>  1 ACT    ets    2018 Q1
#>  2 ACT    ets    2018 Q2
#>  3 ACT    ets    2018 Q3
#>  4 ACT    ets    2018 Q4
#>  5 ACT    ets    2019 Q1
#>  6 ACT    ets    2019 Q2
#>  7 ACT    ets    2019 Q3
#>  8 ACT    ets    2019 Q4
#>  9 ACT    bu     2018 Q1
#> 10 ACT    bu     2018 Q2
#> # ℹ 134 more rows
#> # ℹ 2 more variables: Trips <dist>, .mean <dbl>
```


Thereconcile()step has created a new “model” to produce bottom-up forecasts. Thefableobject contains theetsforecasts as well as the coherentbuforecasts, for the 8 states and the national aggregate. At the state level, these forecasts are identical, but the nationaletsforecasts will be different from the nationalbuforecasts.


For bottom-up forecasting, this is rather inefficient as we are not interested in the ETS model for the national total, and the resultingfablecontains a lot of duplicates. But later we will introduce more advanced methods where we will need models for all levels of aggregation, and where the coherent forecasts are different from any of the original forecasts.


#### Workflow for forecasting aggregation structures


The above code illustrates the general workflow for hierarchical and grouped forecasts. We use the following pipeline of functions.


```
data |> aggregate_key() |> model() |>
  reconcile() |> forecast()
```

- Begin with atsibbleobject (here labelleddata) containing the individual bottom-level series.
- Define inaggregate_key()the aggregation structure and build atsibbleobject that also contains the aggregate series.
- Identify amodel()for each series, at all levels of aggregation.
- Specify inreconcile()how the coherent forecasts are to be generated from the selected models.
- Use theforecast()function to generate forecasts for the whole aggregation structure.

### Top-down approaches


Top-down approaches involve first generating forecasts for the Total series\(y_t\), and then disaggregating these down the hierarchy.


Let\(p_1,\dots,p_{m}\)denote a set of disaggregation proportions which determine how the forecasts of the Total series are to be distributed to obtain forecasts for each series at the bottom level of the structure. For example, for the hierarchy of Figure11.1, using proportions\(p_1,\dots,p_{5}\)we get\[
  \ytilde{AA}{t}=p_1\hat{y}_t,~~~\ytilde{AB}{t}=p_2\hat{y}_t,~~~\ytilde{AC}{t}=p_3\hat{y}_t,~~~\ytilde{BA}{t}=p_4\hat{y}_t~~~\text{and}~~~~~~\ytilde{BB}{t}=p_5\hat{y}_t.
\]Once the bottom-level\(h\)-step-ahead forecasts have been generated, these are aggregated to generate coherent forecasts for the rest of the series.


Top-down forecasts can be generated usingtop_down()within thereconcile()function.


There are several possible top-down methods that can be specified. The two most common top-down approaches specify disaggregation proportions based on the historical proportions of the data. These performed well in the study ofGross & Sohl (1990).


#### Average historical proportions


\[
  p_j=\frac{1}{T}\sum_{t=1}^{T}\frac{y_{j,t}}{{y_t}}
\]for\(j=1,\dots,m\). Each proportion\(p_j\)reflects the average of the historical proportions of the bottom-level series\(y_{j,t}\)over the period\(t=1,\dots,T\)relative to the total aggregate\(y_t\).


This approach is implemented in thetop_down()function by settingmethod = "average_proportions".


#### Proportions of the historical averages


\[
  p_j={\sum_{t=1}^{T}\frac{y_{j,t}}{T}}\Big/{\sum_{t=1}^{T}\frac{y_t}{T}}
\]for\(j=1,\dots,m\). Each proportion\(p_j\)captures the average historical value of the bottom-level series\(y_{j,t}\)relative to the average value of the total aggregate\(y_t\).


This approach is implemented in thetop_down()function by settingmethod = "proportion_averages".


A convenient attribute of such top-down approaches is their simplicity. One only needs to model and generate forecasts for the most aggregated top-level series. In general, these approaches seem to produce quite reliable forecasts for the aggregate levels and they are useful with low count data. On the other hand, one disadvantage is the loss of information due to aggregation. Using such top-down approaches, we are unable to capture and take advantage of individual series characteristics such as time dynamics, special events, different seasonal patterns, etc.


#### Forecast proportions


Because historical proportions used for disaggregation do not take account of how those proportions may change over time, top-down approaches based on historical proportions tend to produce less accurate forecasts at lower levels of the hierarchy than bottom-up approaches. To address this issue, proportions based on forecasts rather than historical data can be used(Athanasopoulos et al., 2009).


Consider a one level hierarchy. We first generate\(h\)-step-ahead forecasts for all of the series. We don’t use these forecasts directly, and they are not coherent (they don’t add up correctly). Let’s call these “initial” forecasts. We calculate the proportion of each\(h\)-step-ahead initial forecast at the bottom level, to the aggregate of all the\(h\)-step-ahead initial forecasts at this level. We refer to these as the forecast proportions, and we use them to disaggregate the top-level\(h\)-step-ahead initial forecast in order to generate coherent forecasts for the whole of the hierarchy.


For a\(K\)-level hierarchy, this process is repeated for each node, going from the top to the bottom level. Applying this process leads to the following general rule for obtaining the forecast proportions:\[
  p_j=\prod^{K-1}_{\ell=0}\frac{\hat{y}_{j,h}^{(\ell)}}{\hat{S}_{j,h}^{(\ell+1)}}
\]where\(j=1,2,\dots,m\),\(\hat{y}_{j,h}^{(\ell)}\)is the\(h\)-step-ahead initial forecast of the series that corresponds to the node which is\(\ell\)levels above\(j\), and\(\hat{S}_{j,h}^{(\ell)}\)is the sum of the\(h\)-step-ahead initial forecasts below the node that is\(\ell\)levels above node\(j\)and are directly connected to that node. These forecast proportions disaggregate the\(h\)-step-ahead initial forecast of the Total series to get\(h\)-step-ahead coherent forecasts of the bottom-level series.


We will use the hierarchy of Figure11.1to explain this notation and to demonstrate how this general rule is reached. Assume we have generated initial forecasts for each series in the hierarchy. Recall that for the top-level “Total” series,\(\tilde{y}_{h}=\hat{y}_{h}\), for any top-down approach. Here are some examples using the above notation:

- \(\hat{y}_{\text{A},h}^{(1)}=\hat{y}_{\text{B},h}^{(1)}=\hat{y}_{h}= \tilde{y}_{h}\);
- \(\hat{y}_{\text{AA},h}^{(1)}=\hat{y}_{\text{AB},h}^{(1)}=\hat{y}_{\text{AC},h}^{(1)}= \hat{y}_{\text{A},h}\);
- \(\hat{y}_{\text{AA},h}^{(2)}=\hat{y}_{\text{AB},h}^{(2)}= \hat{y}_{\text{AC},h}^{(2)}=\hat{y}_{\text{BA},h}^{(2)}= \hat{y}_{\text{BB},h}^{(2)}=\hat{y}_{h}= \tilde{y}_{h}\);
- \(\Shat{AA}{h}{1} = \Shat{AB}{h}{1}= \Shat{AC}{h}{1}= \yhat{AA}{h}+\yhat{AB}{h}+\yhat{AC}{h}\);
- \(\Shat{AA}{h}{2} = \Shat{AB}{h}{2}= \Shat{AC}{h}{2}= \Shat{A}{h}{1} = \Shat{B}{h}{1}= \hat{S}_{h}= \yhat{A}{h}+\yhat{B}{h}\).

Moving down the farthest left branch of the hierarchy, coherent forecasts are given by\[
  \ytilde{A}{h} = \Bigg(\frac{\yhat{A}{h}}{\Shat{A}{h}{1}}\Bigg) \tilde{y}_{h} =
  \Bigg(\frac{\yhat{AA}{h}^{(1)}}{\Shat{AA}{h}{2}}\Bigg) \tilde{y}_{h}
\]and\[
  \ytilde{AA}{h} = \Bigg(\frac{\yhat{AA}{h}}{\Shat{AA}{h}{1}}\Bigg) \ytilde{A}{h}
  =\Bigg(\frac{\yhat{AA}{h}}{\Shat{AA}{h}{1}}\Bigg) \Bigg(\frac{\yhat{AA}{h}^{(1)}}{\Shat{AA}{h}{2}}\Bigg)\tilde{y}_{h}.
\]Consequently,\[
  p_1=\Bigg(\frac{\yhat{AA}{h}}{\Shat{AA}{h}{1}}\Bigg) \Bigg(\frac{\yhat{AA}{h}^{(1)}}{\Shat{AA}{h}{2}}\Bigg).
\]The other proportions can be obtained similarly.


This approach is implemented in thetop_down()function by settingmethod = "forecast_proportions". Because this approach tends to work better than other top-down methods, it is the default choice in thetop_down()function when nomethodargument is specified.


One disadvantage of all top-down approaches, is that they do not produce unbiased coherent forecasts(Hyndman et al., 2011)even if the base forecasts are unbiased.


### Middle-out approach


The middle-out approach combines bottom-up and top-down approaches. Again, it can only be used for strictly hierarchical aggregation structures.


First, a “middle” level is chosen and forecasts are generated for all the series at this level. For the series above the middle level, coherent forecasts are generated using the bottom-up approach by aggregating the “middle-level” forecasts upwards. For the series below the “middle level”, coherent forecasts are generated using a top-down approach by disaggregating the “middle level” forecasts downwards.


This approach is implemented in themiddle_out()function by specifying the appropriate middle level via thelevelargument and selecting the top-down approach with themethodargument.


### Bibliography
