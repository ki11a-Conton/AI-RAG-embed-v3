
# Forecasting: Principles and Practice(3rd ed)


## 13.3Ensuring forecasts stay within limits


It is common to want forecasts to be positive, or to require them to be within some specified range\([a,b]\). Both of these situations are relatively easy to handle using transformations.


### Positive forecasts


To impose a positivity constraint, we can simply work on the log scale. For example, consider the real price of a dozen eggs (1900-1993; in cents) shown in Figure13.4. Because of the log transformation, the forecast distributions are constrained to stay positive, and so they will become progressively more skewed as the mean decreases.


```
egg_prices <- prices |> filter(!is.na(eggs))
egg_prices |>
  model(ETS(log(eggs) ~ trend("A"))) |>
  forecast(h = 50) |>
  autoplot(egg_prices) +
  labs(title = "Annual egg prices",
       y = "$US (in cents adjusted for inflation) ")
```


Figure 13.4: Forecasts for the price of a dozen eggs, constrained to be positive using a log transformation.


### Forecasts constrained to an interval


To see how to handle data constrained to an interval, imagine that the egg prices were constrained to lie within\(a=50\)and\(b=400\). Then we can transform the data using a scaled logit transform which maps\((a,b)\)to the whole real line:\[
  y = \log\left(\frac{x-a}{b-x}\right),
\]where\(x\)is on the original scale and\(y\)is the transformed data. To reverse the transformation, we will use\[
  x  = \frac{(b-a)e^y}{1+e^y} + a.
\]This is not a built-in transformation, so we will need to first setup the transformation functions.


```
scaled_logit <- function(x, lower = 0, upper = 1) {
  log((x - lower) / (upper - x))
}
inv_scaled_logit <- function(x, lower = 0, upper = 1) {
  (upper - lower) * exp(x) / (1 + exp(x)) + lower
}
my_scaled_logit <- new_transformation(
                    scaled_logit, inv_scaled_logit)
egg_prices |>
  model(
    ETS(my_scaled_logit(eggs, lower = 50, upper = 400)
          ~ trend("A"))
  ) |>
  forecast(h = 50) |>
  autoplot(egg_prices) +
  labs(title = "Annual egg prices",
       y = "$US (in cents adjusted for inflation) ")
```


Figure 13.5: Forecasts for the price of a dozen eggs, constrained to be lie between 50 and 400 cents US.


The bias-adjustment is automatically applied here, and the prediction intervals from these transformations have the same coverage probability as on the transformed scale, because quantiles are preserved under monotonically increasing transformations.


The prediction intervals lie above 50 due to the transformation. As a result of this artificial (and unrealistic) constraint, the forecast distributions have become extremely skewed.
