
# Forecasting: Principles and Practice(3rd ed)


## 13.6Backcasting


Sometimes it is useful to “backcast” a time series — that is, forecast in reverse time. Although there are no in-built R functions to do this, it is easy to implement by creating a new time index.


Suppose we want to extend our Australian takeaway to the start of 1981 (the actual data starts in April 1982).


```
backcasts <- auscafe |>
  mutate(reverse_time = rev(row_number())) |>
  update_tsibble(index = reverse_time) |>
  model(ets = ETS(Turnover ~ season(period = 12))) |>
  forecast(h = 15) |>
  mutate(Month = auscafe$Month[1] - (1:15)) |>
  as_fable(index = Month, response = "Turnover",
    distribution = "Turnover")
backcasts |>
  autoplot(auscafe |> filter(year(Month) < 1990)) +
  labs(title = "Backcasts of Australian food expenditure",
       y = "$ (billions)")
```


Figure 13.8: Backcasts for Australian monthly expenditure on cafés, restaurants and takeaway food services using an ETS model.


Most of the work here is in re-indexing thetsibbleobject and then re-indexing thefableobject.
